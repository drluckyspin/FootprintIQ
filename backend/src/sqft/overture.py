"""Overture Maps building-footprint loader. OWNED BY LANE B."""

from __future__ import annotations

import re
from pathlib import Path

import duckdb
import httpx

from sqft.config import OvertureConfig
from sqft.io import write_parquet
from sqft.schema import GeocodeResult

DEFAULT_BBOX_PADDING_DEG = 0.005

# Offline / test fallback when docs fetch fails (see resolve_release docstring).
_OVERTURE_RELEASE_FALLBACK = "2025-07-23.0"
_RELEASE_CACHE: dict[str, str] = {}


def resolve_release(config: OvertureConfig) -> str:
    """If config.release == 'latest', resolve to the current release string."""
    if config.release != "latest":
        return config.release
    cache_key = "latest"
    if cache_key in _RELEASE_CACHE:
        return _RELEASE_CACHE[cache_key]
    try:
        resp = httpx.get("https://docs.overturemaps.org/releases/", timeout=10.0)
        resp.raise_for_status()
        # Release tags look like 2025-07-23.0 in the docs HTML.
        matches = re.findall(r"\b(\d{4}-\d{2}-\d{2}\.\d+)\b", resp.text)
        resolved = matches[0] if matches else _OVERTURE_RELEASE_FALLBACK
    except (httpx.HTTPError, httpx.TimeoutException):
        resolved = _OVERTURE_RELEASE_FALLBACK
    _RELEASE_CACHE[cache_key] = resolved
    return resolved


def compute_bbox(
    geocoded: list[GeocodeResult], padding_deg: float = DEFAULT_BBOX_PADDING_DEG
) -> tuple[float, float, float, float]:
    """Return (min_lon, min_lat, max_lon, max_lat) over geocoded points (status='ok')."""
    lons: list[float] = []
    lats: list[float] = []
    for row in geocoded:
        if row.status != "ok" or row.lat is None or row.lon is None:
            continue
        lons.append(row.lon)
        lats.append(row.lat)
    if not lons:
        raise ValueError("compute_bbox: no geocoded points with status='ok' and coordinates")
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    return (
        min_lon - padding_deg,
        min_lat - padding_deg,
        max_lon + padding_deg,
        max_lat + padding_deg,
    )


def fetch_footprints(
    geocoded: list[GeocodeResult],
    config: OvertureConfig,
    output_path: Path,
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> Path:
    """Run the DuckDB-over-S3 query and write footprints.parquet."""
    min_lon, min_lat, max_lon, max_lat = compute_bbox(geocoded)
    release = resolve_release(config)
    s3_glob = config.s3_path_template.format(release=release)

    owns_con = duckdb_con is None
    con = duckdb_con or duckdb.connect()
    try:
        con.execute("INSTALL spatial; LOAD spatial;")
        con.execute("INSTALL httpfs; LOAD httpfs;")
        query = """
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
                update_time AS overture_update_time
            FROM read_parquet(?)
            WHERE bbox.xmax >= ?
              AND bbox.xmin <= ?
              AND bbox.ymax >= ?
              AND bbox.ymin <= ?
        """
        rows = con.execute(
            query,
            [f"{s3_glob}*.parquet", min_lon, max_lon, min_lat, max_lat],
        ).fetchall()
        colnames = [
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
        dict_rows = [dict(zip(colnames, row, strict=True)) for row in rows]
        write_parquet(dict_rows, output_path, "footprints")
    finally:
        if owns_con:
            con.close()
    return output_path
