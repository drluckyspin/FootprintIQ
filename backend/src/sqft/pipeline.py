"""End-to-end pipeline orchestration."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from sqft import io
from sqft.config import Settings, load_settings
from sqft.dedup import build_address_key_index, unique_addresses
from sqft.flags import evaluate_flags, resolve_confidence
from sqft.floors import resolve_floors
from sqft.geocode import GeocodeCache, geocode_batch, has_usable_coordinates
from sqft.manifest import finalize_manifest, manifest_output_path, save_manifest, start_manifest
from sqft.normalize import normalize_addresses
from sqft.overture import fetch_footprints, resolve_release
from sqft.parcels import NullParcelProvider
from sqft.schema import (
    BuildingMatch,
    EstimateRow,
    GeocodeResult,
    GeocoderPrecision,
    NormalizedAddress,
)
from sqft.log import get_logger
from sqft.spatial_join import join_points_to_buildings

logger = get_logger("pipeline")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _fixtures_dir() -> Path:
    return _repo_root() / "tests" / "fixtures"


def use_fixtures() -> bool:
    return os.environ.get("SQFT_USE_FIXTURES", "").lower() in ("1", "true", "yes")


def _copy_fixture(name: str, dest: Path) -> None:
    src = _fixtures_dir() / name
    if not src.exists():
        raise FileNotFoundError(f"fixture missing: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _footprint_lookup(footprints_path: Path) -> dict[str, dict]:
    df = pd.read_parquet(footprints_path)
    return {str(r["id"]): r for r in df.to_dict(orient="records")}


def _optional_float(val: object) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return float(val)


def _optional_int(val: object) -> int | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return int(val)


def _optional_str(val: object) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return str(val)


def _build_estimate_rows(
    matches: list[BuildingMatch],
    normalized: list[NormalizedAddress],
    geocoded: list[GeocodeResult],
    footprints_path: Path,
    settings: Settings,
    pipeline_run_id: str,
    overture_release: str,
    location_types: dict[str, str],
) -> list[EstimateRow]:
    norm_by_id = {n.location_id: n for n in normalized}
    geo_by_key = {g.address_key: g for g in geocoded}
    fp_by_id = _footprint_lookup(footprints_path)
    rows: list[EstimateRow] = []

    for match in matches:
        norm = norm_by_id.get(match.location_id)
        geo = geo_by_key.get(match.address_key)
        if norm is None:
            continue

        chosen = next((c for c in match.candidates if c.is_chosen), None)
        fp = fp_by_id.get(match.chosen_building_id or "") if match.chosen_building_id else None
        footprint_area = chosen.area_sqft if chosen else None
        height_m = _optional_float(fp["height"]) if fp else None
        num_floors_attr = _optional_int(fp["num_floors"]) if fp else None
        subtype = _optional_str(fp.get("overture_subtype")) if fp else None

        floors_used, floors_source = resolve_floors(
            num_floors_attr,
            height_m,
            subtype,
            settings.floors,
        )
        estimated = (
            round(footprint_area * floors_used, settings.output.decimals)
            if footprint_area is not None
            else None
        )

        row = EstimateRow(
            location_id=match.location_id,
            address_input=norm.address_input,
            address_key=match.address_key,
            location_type=location_types.get(match.location_id, "other"),
            geocoded_lat=geo.lat if geo else None,
            geocoded_lon=geo.lon if geo else None,
            geocoder_precision=geo.precision if geo else GeocoderPrecision.UNKNOWN,
            geocoder_provider=geo.provider if geo else None,
            formatted_address=geo.formatted_address if geo else None,
            building_id=match.chosen_building_id,
            match_method=match.match_method,
            multi_building_count=match.multi_building_count,
            candidates_json=json.dumps([c.model_dump() for c in match.candidates]),
            footprint_area_sqft=footprint_area,
            num_floors_used=floors_used,
            floors_source=floors_source,
            raw_overture_height=height_m,
            raw_overture_num_floors=num_floors_attr,
            estimated_sqft=estimated,
            overture_class=_optional_str(fp.get("overture_class")) if fp else None,
            overture_subtype=subtype,
            overture_source=_optional_str(fp.get("overture_source")) if fp else None,
            overture_update_time=fp.get("overture_update_time") if fp else None,
            overture_release=overture_release,
            pipeline_run_id=pipeline_run_id,
        )
        row.confidence = resolve_confidence(evaluate_flags(row))
        rows.append(row)

    return rows


def _record_stage(
    manifest,
    name: str,
    *,
    row_count: int | None = None,
    duration: float,
    skipped: bool = False,
) -> None:
    if row_count is not None:
        manifest.stage_row_counts[name] = row_count
    manifest.stage_durations_seconds[name] = 0.0 if skipped else duration
    if skipped:
        manifest.notes.append(f"skipped:{name}")


def run_pipeline(
    input_csv: Path,
    *,
    settings: Settings | None = None,
    config_path: Path | None = None,
    resume: bool | None = None,
) -> Path:
    """Run all stages; return path to estimates.parquet."""
    settings = settings or load_settings(config_path)
    resume = settings.pipeline.resume if resume is None else resume
    data_dir = settings.data_dir
    config_path = config_path or _repo_root() / "config.yaml"
    overture_release = resolve_release(settings.overture)

    logger.info(
        "pipeline start input=%s run_id=pending fixtures=%s resume=%s data_dir=%s",
        input_csv,
        use_fixtures(),
        resume,
        data_dir,
    )

    raw = io.read_input_csv(input_csv)
    if settings.pipeline.sample_size:
        raw = raw[: settings.pipeline.sample_size]
    location_types = {r.location_id: r.location_type for r in raw}

    manifest = start_manifest(
        input_csv,
        config_path,
        _repo_root(),
        overture_release,
        input_row_count=len(raw),
    )
    manifest_path = manifest_output_path(data_dir, manifest.pipeline_run_id)

    norm_path = io.interim_path(data_dir, "normalized")
    geo_path = io.interim_path(data_dir, "geocoded")
    fp_path = io.interim_path(data_dir, "footprints")
    est_path = io.output_path(data_dir, "estimates")

    if resume and est_path.exists():
        logger.warning(
            "resume: %s already exists — skipping all stages (no Google/Overture calls). "
            "Re-run with: rm %s && make sample  OR  cli run-all --no-resume",
            est_path,
            est_path,
        )
        finalize_manifest(manifest, manifest_path, est_path)
        return est_path

    # normalize
    if resume and norm_path.exists():
        normalized = [
            NormalizedAddress.model_validate(r)
            for r in io.read_parquet_dicts(norm_path, "normalized")
        ]
        logger.info("stage normalize: skipped (cached %s)", norm_path)
        _record_stage(manifest, "normalize", row_count=len(normalized), duration=0.0, skipped=True)
    else:
        t0 = time.perf_counter()
        logger.info("stage normalize: %d input rows", len(raw))
        normalized = normalize_addresses(raw, settings.geocoder.chain_tokens)
        io.write_parquet(
            io.models_to_rows(normalized, "normalized"), norm_path, "normalized"
        )
        elapsed = time.perf_counter() - t0
        logger.info("stage normalize: done rows=%d elapsed=%.2fs -> %s", len(normalized), elapsed, norm_path)
        _record_stage(manifest, "normalize", row_count=len(normalized), duration=elapsed)

    dedup_index = build_address_key_index(normalized)
    unique = unique_addresses(normalized)
    logger.info("dedup: %d locations -> %d unique address_keys", len(normalized), len(unique))

    # geocode
    if use_fixtures():
        logger.info("stage geocode: skipped (SQFT_USE_FIXTURES — copying fixture, no Google API calls)")
        _copy_fixture("geocoded.parquet", geo_path)
        geocoded_models = [
            GeocodeResult.model_validate(r)
            for r in io.read_parquet_dicts(geo_path, "geocoded")
        ]
        _record_stage(
            manifest, "geocode", row_count=len(geocoded_models), duration=0.0, skipped=True
        )
    elif resume and geo_path.exists():
        logger.info("stage geocode: skipped (cached %s)", geo_path)
        geocoded_models = [
            GeocodeResult.model_validate(r)
            for r in io.read_parquet_dicts(geo_path, "geocoded")
        ]
        _record_stage(manifest, "geocode", row_count=len(geocoded_models), duration=0.0, skipped=True)
    else:
        t0 = time.perf_counter()
        cache = GeocodeCache(settings.geocoder.cache_path)
        logger.info(
            "stage geocode: calling Google for %d unique addresses (cache=%s)",
            len(unique),
            settings.geocoder.cache_path,
        )
        geocoded_models = asyncio.run(geocode_batch(unique, settings.geocoder, cache))
        usable = sum(1 for g in geocoded_models if has_usable_coordinates(g))
        io.write_parquet(
            io.models_to_rows(geocoded_models, "geocoded"), geo_path, "geocoded"
        )
        elapsed = time.perf_counter() - t0
        logger.info(
            "stage geocode: done usable=%d/%d elapsed=%.2fs -> %s",
            usable,
            len(geocoded_models),
            elapsed,
            geo_path,
        )
        _record_stage(manifest, "geocode", row_count=len(geocoded_models), duration=elapsed)

    # footprints
    if use_fixtures():
        logger.info("stage footprints: skipped (SQFT_USE_FIXTURES — copying fixture, no Overture S3 query)")
        _copy_fixture("footprints.parquet", fp_path)
        _record_stage(manifest, "footprints", duration=0.0, skipped=True)
    elif resume and fp_path.exists():
        logger.info("stage footprints: skipped (cached %s)", fp_path)
        _record_stage(manifest, "footprints", duration=0.0, skipped=True)
    else:
        t0 = time.perf_counter()
        logger.info("stage footprints: querying Overture Maps over S3")
        fetch_footprints(geocoded_models, settings.overture, fp_path)
        elapsed = time.perf_counter() - t0
        logger.info("stage footprints: done elapsed=%.2fs -> %s", elapsed, fp_path)
        _record_stage(manifest, "footprints", duration=elapsed)

    # spatial join + estimate
    t0 = time.perf_counter()
    logger.info("stage spatial_join: matching points to footprints")
    matches = join_points_to_buildings(
        geocoded_models,
        fp_path,
        dedup_index,
        settings.spatial,
        NullParcelProvider(),
        location_types,
    )
    join_elapsed = time.perf_counter() - t0
    matched = sum(1 for m in matches if m.chosen_building_id)
    logger.info(
        "stage spatial_join: done matched=%d/%d elapsed=%.2fs",
        matched,
        len(matches),
        join_elapsed,
    )
    _record_stage(manifest, "spatial_join", row_count=len(matches), duration=join_elapsed)

    t0 = time.perf_counter()
    logger.info("stage estimate: building output rows")
    estimates = _build_estimate_rows(
        matches,
        normalized,
        geocoded_models,
        fp_path,
        settings,
        manifest.pipeline_run_id,
        overture_release,
        location_types,
    )
    io.write_parquet(io.models_to_rows(estimates, "estimates"), est_path, "estimates")
    est_elapsed = time.perf_counter() - t0
    logger.info("stage estimate: done rows=%d elapsed=%.2fs -> %s", len(estimates), est_elapsed, est_path)
    _record_stage(manifest, "estimate", row_count=len(estimates), duration=est_elapsed)

    finalize_manifest(manifest, manifest_path, est_path)
    logger.info("pipeline complete run_id=%s manifest=%s", manifest.pipeline_run_id, manifest_path)
    return est_path
