"""Overture Maps building-footprint loader. OWNED BY LANE B."""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import duckdb
import httpx

from sqft.config import REPO_ROOT, OvertureConfig
from sqft.geocode import has_usable_coordinates
from sqft.io import write_parquet
from sqft.log import get_logger
from sqft.schema import GeocodeResult

DEFAULT_BBOX_PADDING_DEG = 0.005
# Wider than padding: if geocoded span exceeds this, query Overture per point (avoids CONUS-wide S3 scans).
_MAX_SINGLE_BBOX_SPAN_DEG = 0.2

# Fallback when release-calendar fetch fails (see resolve_release).
_OVERTURE_RELEASE_FALLBACK = "2026-05-20.0"
_OVERTURE_RELEASE_CALENDAR_URL = "https://docs.overturemaps.org/release-calendar/"
_OVERTURE_STAC_COLLECTION_URL = (
    "https://stac.overturemaps.org/{release}/buildings/building/collection.json"
)
_RELEASE_CACHE: dict[str, str] = {}
# (file_bbox, s3_uri) per release — populated from STAC or disk cache.
_STAC_BUILDINGS_CACHE: dict[str, list[tuple[tuple[float, float, float, float], str]]] = {}

logger = get_logger("overture")

# Public Overture/STAC endpoints; avoid corporate HTTP_PROXY (often 403 on CDN).
_HTTPX_CLIENT = httpx.Client(trust_env=False, timeout=60.0)


def _configure_duckdb_s3(con: duckdb.DuckDBPyConnection) -> None:
    """Tune httpfs for large Overture parquet reads over S3."""
    con.execute("SET s3_region='us-west-2';")
    con.execute("SET http_timeout = 600000;")  # ms
    con.execute("SET http_retries = 5;")


def _https_s3_to_uri(url: str) -> str:
    """Convert Overture HTTPS S3 asset URLs to s3:// URIs for DuckDB httpfs."""
    match = re.match(
        r"https://([^.]+)\.s3\.[^/]+\.amazonaws\.com/(.*)",
        url,
    )
    if match:
        return f"s3://{match.group(1)}/{match.group(2)}"
    return url


def bbox_intersects(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> bool:
    """Return True when lon/lat boxes a and b overlap (inclusive edges)."""
    a_min_lon, a_min_lat, a_max_lon, a_max_lat = a
    b_min_lon, b_min_lat, b_max_lon, b_max_lat = b
    return (
        a_max_lon >= b_min_lon
        and a_min_lon <= b_max_lon
        and a_max_lat >= b_min_lat
        and a_min_lat <= b_max_lat
    )


def _parse_stac_building_item(
    item: dict[str, object],
) -> tuple[tuple[float, float, float, float], str] | None:
    raw_bbox = item.get("bbox")
    if not isinstance(raw_bbox, list) or len(raw_bbox) != 4:
        return None
    file_bbox = (float(raw_bbox[0]), float(raw_bbox[1]), float(raw_bbox[2]), float(raw_bbox[3]))
    assets = item.get("assets")
    if not isinstance(assets, dict):
        return None
    for asset in assets.values():
        if not isinstance(asset, dict):
            continue
        href = asset.get("href")
        if not isinstance(href, str):
            continue
        if "amazonaws.com" in href or href.startswith("s3://"):
            s3_uri = _https_s3_to_uri(href) if href.startswith("http") else href
            return file_bbox, s3_uri
    return None


def _stac_cache_path(release: str) -> Path:
    return REPO_ROOT / "data" / "interim" / f"overture_stac_buildings_{release}.json"


def _read_stac_cache(path: Path) -> list[tuple[tuple[float, float, float, float], str]] | None:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("STAC cache unreadable %s: %s", path, exc)
        return None
    if not isinstance(raw, list):
        return None
    out: list[tuple[tuple[float, float, float, float], str]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        bbox = entry.get("bbox")
        s3 = entry.get("s3")
        if (
            isinstance(bbox, list)
            and len(bbox) == 4
            and all(isinstance(v, (int, float)) for v in bbox)
            and isinstance(s3, str)
        ):
            out.append(
                (
                    (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
                    s3,
                )
            )
    return out or None


def _write_stac_cache(
    path: Path, files: list[tuple[tuple[float, float, float, float], str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [{"bbox": list(bbox), "s3": s3} for bbox, s3 in files]
    path.write_text(json.dumps(payload))


def _normalize_s3_uri(path: str) -> str:
    if path.startswith("https://"):
        return _https_s3_to_uri(path)
    if path.startswith("s3://"):
        return path
    return f"s3://overturemaps-us-west-2/{path.lstrip('/')}"


def _build_stac_cache_via_duckdb(
    s3_prefix: str, cache_path: Path
) -> list[tuple[tuple[float, float, float, float], str]]:
    """Build file bbox index: glob S3 paths, then min/max bbox per file (no STAC HTTP)."""
    glob_pattern = f"{s3_prefix}*.parquet"
    logger.info(
        "building Overture file index via DuckDB S3 glob + per-file bbox (one-time): %s",
        glob_pattern,
    )
    con = duckdb.connect()
    try:
        con.execute("INSTALL httpfs; LOAD httpfs;")
        _configure_duckdb_s3(con)
        path_rows = con.execute(
            "SELECT file FROM glob(?)",
            [glob_pattern],
        ).fetchall()
        total = len(path_rows)
        logger.info("DuckDB glob listed %d building parquet files", total)
        files: list[tuple[tuple[float, float, float, float], str]] = []
        for i, (raw_path,) in enumerate(path_rows, start=1):
            if raw_path is None:
                continue
            s3_uri = _normalize_s3_uri(str(raw_path))
            if i == 1 or i % 50 == 0 or i == total:
                logger.info("DuckDB bbox index %d/%d %s", i, total, s3_uri.rsplit("/", 1)[-1])
            xmin, ymin, xmax, ymax = con.execute(
                """
                SELECT
                    min(bbox.xmin),
                    min(bbox.ymin),
                    max(bbox.xmax),
                    max(bbox.ymax)
                FROM read_parquet(?)
                """,
                [s3_uri],
            ).fetchone()
            files.append(
                ((float(xmin), float(ymin), float(xmax), float(ymax)), s3_uri),
            )
    finally:
        con.close()

    if not files:
        raise ValueError(f"DuckDB S3 index returned no files for {glob_pattern}")
    _write_stac_cache(cache_path, files)
    logger.info("DuckDB S3 file index built: %d files -> %s", len(files), cache_path)
    return files


def _fetch_stac_building_files(
    release: str, s3_prefix: str | None = None
) -> list[tuple[tuple[float, float, float, float], str]]:
    """Load per-file bbox + S3 URI from Overture STAC (cached in memory and on disk)."""
    if release in _STAC_BUILDINGS_CACHE:
        return _STAC_BUILDINGS_CACHE[release]

    cache_path = _stac_cache_path(release)
    cached = _read_stac_cache(cache_path)
    if cached is not None:
        logger.info("STAC building catalog cache hit: %s (%d files)", cache_path, len(cached))
        _STAC_BUILDINGS_CACHE[release] = cached
        return cached

    prefix = s3_prefix or (
        f"s3://overturemaps-us-west-2/release/{release}/theme=buildings/type=building/"
    )
    files: list[tuple[tuple[float, float, float, float], str]]
    try:
        collection_url = _OVERTURE_STAC_COLLECTION_URL.format(release=release)
        logger.info("API GET %s (STAC building catalog)", collection_url)
        coll_resp = _HTTPX_CLIENT.get(collection_url, timeout=60.0)
        coll_resp.raise_for_status()
        collection = coll_resp.json()
        links = collection.get("links") if isinstance(collection, dict) else None
        if not isinstance(links, list):
            raise ValueError(f"STAC collection missing links: {collection_url}")

        item_hrefs: list[str] = []
        for link in links:
            if not isinstance(link, dict) or link.get("rel") != "item":
                continue
            href = link.get("href")
            if isinstance(href, str):
                item_hrefs.append(urljoin(collection_url, href))

        def fetch_item(href: str) -> tuple[tuple[float, float, float, float], str] | None:
            last_exc: Exception | None = None
            for attempt in range(3):
                try:
                    resp = httpx.get(href, timeout=90.0, trust_env=False)
                    resp.raise_for_status()
                    return _parse_stac_building_item(resp.json())
                except (httpx.HTTPError, httpx.ConnectError) as exc:
                    last_exc = exc
                    if attempt < 2:
                        continue
            if last_exc is not None:
                raise last_exc
            return None

        files = []
        workers = min(12, max(4, len(item_hrefs)))
        logger.info("STAC fetching %d building items (workers=%d)", len(item_hrefs), workers)
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(fetch_item, href): href for href in item_hrefs}
            for future in as_completed(futures):
                parsed = future.result()
                if parsed is not None:
                    files.append(parsed)
                done += 1
                if done % 64 == 0 or done == len(item_hrefs):
                    logger.info("STAC items fetched %d/%d", done, len(item_hrefs))
                    if files:
                        _write_stac_cache(cache_path, files)

        if not files:
            raise ValueError(f"STAC catalog returned no building parquet files for {release}")
        _write_stac_cache(cache_path, files)
        logger.info(
            "STAC building catalog loaded: %d parquet files -> %s", len(files), cache_path
        )
    except (httpx.HTTPError, httpx.ConnectError, ValueError) as exc:
        logger.warning("STAC HTTP catalog failed (%s); trying DuckDB S3 metadata index", exc)
        files = _build_stac_cache_via_duckdb(prefix, cache_path)

    _STAC_BUILDINGS_CACHE[release] = files
    return files


def parquet_paths_for_bbox(
    stac_files: list[tuple[tuple[float, float, float, float], str]],
    bbox: tuple[float, float, float, float],
) -> list[str]:
    """Return S3 parquet URIs whose STAC extent intersects the query bbox."""
    return [s3 for file_bbox, s3 in stac_files if bbox_intersects(file_bbox, bbox)]


def resolve_release(config: OvertureConfig) -> str:
    """If config.release == 'latest', resolve to the current release string."""
    if config.release != "latest":
        return config.release
    cache_key = "latest"
    if cache_key in _RELEASE_CACHE:
        logger.debug("overture release cache hit: %s", _RELEASE_CACHE[cache_key])
        return _RELEASE_CACHE[cache_key]
    try:
        logger.info("API GET %s (resolve latest release)", _OVERTURE_RELEASE_CALENDAR_URL)
        resp = _HTTPX_CLIENT.get(_OVERTURE_RELEASE_CALENDAR_URL, timeout=15.0)
        resp.raise_for_status()
        # Only parse the "Current release" section — avoid future dates in the schedule table.
        section = resp.text.split("Proposed release schedule", 1)[0]
        current = re.search(
            r"latest Overture data release is:.*?(\d{4}-\d{2}-\d{2}\.\d+)",
            section,
            re.DOTALL | re.IGNORECASE,
        )
        if current:
            resolved = current.group(1)
        else:
            matches = re.findall(r"\b(\d{4}-\d{2}-\d{2}\.\d+)\b", section)
            resolved = matches[0] if matches else _OVERTURE_RELEASE_FALLBACK
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.warning("overture release lookup failed, using fallback: %s", exc)
        resolved = _OVERTURE_RELEASE_FALLBACK
    _RELEASE_CACHE[cache_key] = resolved
    logger.info("overture release resolved: %s", resolved)
    return resolved


def compute_bbox(
    geocoded: list[GeocodeResult], padding_deg: float = DEFAULT_BBOX_PADDING_DEG
) -> tuple[float, float, float, float]:
    """Return (min_lon, min_lat, max_lon, max_lat) over geocoded points with coordinates."""
    lons: list[float] = []
    lats: list[float] = []
    for row in geocoded:
        if not has_usable_coordinates(row):
            continue
        lons.append(row.lon)  # type: ignore[arg-type]
        lats.append(row.lat)  # type: ignore[arg-type]
    if not lons:
        raise ValueError(
            "compute_bbox: no geocoded points with usable coordinates "
            "(all failed or missing lat/lon)"
        )
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    return (
        min_lon - padding_deg,
        min_lat - padding_deg,
        max_lon + padding_deg,
        max_lat + padding_deg,
    )


def _point_bbox(
    row: GeocodeResult, padding_deg: float = DEFAULT_BBOX_PADDING_DEG
) -> tuple[float, float, float, float]:
    lon, lat = row.lon, row.lat  # type: ignore[misc]
    return (
        lon - padding_deg,
        lat - padding_deg,
        lon + padding_deg,
        lat + padding_deg,
    )


def query_bboxes(
    geocoded: list[GeocodeResult], padding_deg: float = DEFAULT_BBOX_PADDING_DEG
) -> list[tuple[float, float, float, float]]:
    """Return one or more bboxes for Overture S3 queries.

    A single aggregate bbox is used when all points are nearby; otherwise each
    usable point gets its own padded bbox so nationwide samples do not scan the
    entire US buildings theme.
    """
    usable = [g for g in geocoded if has_usable_coordinates(g)]
    if not usable:
        raise ValueError(
            "query_bboxes: no geocoded points with usable coordinates "
            "(all failed or missing lat/lon)"
        )
    if len(usable) == 1:
        return [_point_bbox(usable[0], padding_deg)]
    lons = [g.lon for g in usable]  # type: ignore[misc]
    lats = [g.lat for g in usable]  # type: ignore[misc]
    span_lon = max(lons) - min(lons)
    span_lat = max(lats) - min(lats)
    if span_lon <= _MAX_SINGLE_BBOX_SPAN_DEG and span_lat <= _MAX_SINGLE_BBOX_SPAN_DEG:
        return [compute_bbox(geocoded, padding_deg)]
    return [_point_bbox(g, padding_deg) for g in usable]


_BUILDINGS_QUERY = """
    SELECT
        id,
        ST_AsWKB(geometry) AS geometry_wkb,
        bbox.xmin AS bbox_xmin,
        bbox.ymin AS bbox_ymin,
        bbox.xmax AS bbox_xmax,
        bbox.ymax AS bbox_ymax,
        height,
        CAST(num_floors AS INTEGER) AS num_floors,
        class AS overture_class,
        subtype AS overture_subtype,
        sources[1].dataset AS overture_source,
        version AS overture_version,
        try_cast(sources[1].update_time AS TIMESTAMP) AS overture_update_time
    FROM read_parquet(?)
    WHERE bbox.xmax >= ?
      AND bbox.xmin <= ?
      AND bbox.ymax >= ?
      AND bbox.ymin <= ?
"""

_BUILDINGS_COLNAMES = [
    "id",
    "geometry_wkb",
    "bbox_xmin",
    "bbox_ymin",
    "bbox_xmax",
    "bbox_ymax",
    "height",
    "num_floors",
    "overture_class",
    "overture_subtype",
    "overture_source",
    "overture_version",
    "overture_update_time",
]


def _query_buildings_in_bbox(
    con: duckdb.DuckDBPyConnection,
    parquet_paths: list[str],
    bbox: tuple[float, float, float, float],
) -> list[dict[str, object]]:
    if not parquet_paths:
        return []
    min_lon, min_lat, max_lon, max_lat = bbox
    last_exc: duckdb.IOException | None = None
    for attempt in range(5):
        try:
            rows = con.execute(
                _BUILDINGS_QUERY,
                [parquet_paths, min_lon, max_lon, min_lat, max_lat],
            ).fetchall()
            return [dict(zip(_BUILDINGS_COLNAMES, row, strict=True)) for row in rows]
        except duckdb.IOException as exc:
            last_exc = exc
            msg = str(exc).lower()
            if attempt < 4 and (
                "ssl" in msg or "timeout" in msg or "failure when receiving" in msg
            ):
                delay = 2**attempt
                logger.warning(
                    "DuckDB S3 query failed (attempt %d/5), retry in %ds: %s",
                    attempt + 1,
                    delay,
                    exc,
                )
                time.sleep(delay)
                continue
            raise
    if last_exc is not None:
        raise last_exc
    return []


def fetch_footprints(
    geocoded: list[GeocodeResult],
    config: OvertureConfig,
    output_path: Path,
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> Path:
    """Run the DuckDB-over-S3 query and write footprints.parquet."""
    bboxes = query_bboxes(geocoded)
    release = resolve_release(config)
    s3_prefix = config.s3_path_template.format(release=release)
    try:
        stac_files = _fetch_stac_building_files(release, s3_prefix=s3_prefix)
    except (httpx.HTTPError, httpx.ConnectError, duckdb.IOException, OSError, ValueError) as exc:
        cache_path = _stac_cache_path(release)
        raise RuntimeError(
            "Overture building file index is required before footprints. "
            f"Build it with: make stac-cache (or delete a corrupt cache at {cache_path}). "
            f"Underlying error: {exc}"
        ) from exc
    ok_points = sum(1 for g in geocoded if has_usable_coordinates(g))
    logger.info(
        "fetch_footprints geocoded_ok=%d query_bboxes=%d release=%s stac_files=%d",
        ok_points,
        len(bboxes),
        release,
        len(stac_files),
    )

    owns_con = duckdb_con is None
    con = duckdb_con or duckdb.connect()
    try:
        logger.debug("DuckDB INSTALL spatial; LOAD spatial; INSTALL httpfs; LOAD httpfs")
        con.execute("INSTALL spatial; LOAD spatial;")
        con.execute("INSTALL httpfs; LOAD httpfs;")
        _configure_duckdb_s3(con)
        by_id: dict[str, dict[str, object]] = {}
        for i, bbox in enumerate(bboxes, start=1):
            min_lon, min_lat, max_lon, max_lat = bbox
            parquet_paths = parquet_paths_for_bbox(stac_files, bbox)
            if not parquet_paths:
                logger.warning(
                    "fetch_footprints query %d/%d: no STAC parquet files intersect bbox",
                    i,
                    len(bboxes),
                )
                continue
            logger.info(
                "fetch_footprints query %d/%d bbox=(%.4f,%.4f,%.4f,%.4f) parquet_files=%d",
                i,
                len(bboxes),
                min_lon,
                min_lat,
                max_lon,
                max_lat,
                len(parquet_paths),
            )
            for row in _query_buildings_in_bbox(con, parquet_paths, bbox):
                by_id[str(row["id"])] = row
        dict_rows = list(by_id.values())
        logger.info("fetch_footprints buildings_unique=%d writing %s", len(dict_rows), output_path)
        write_parquet(dict_rows, output_path, "footprints")
    finally:
        if owns_con:
            con.close()
    return output_path


def build_stac_cache(config: OvertureConfig | None = None) -> Path:
    """Pre-build the Overture building file index (STAC HTTP or DuckDB S3 fallback)."""
    cfg = config or OvertureConfig()
    release = resolve_release(cfg)
    s3_prefix = cfg.s3_path_template.format(release=release)
    _fetch_stac_building_files(release, s3_prefix=s3_prefix)
    return _stac_cache_path(release)
