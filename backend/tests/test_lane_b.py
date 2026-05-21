"""Lane B — spatial."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from shapely import wkt

from sqft.area import polygon_area_sqft
from sqft.config import FloorsConfig, SpatialConfig
from sqft.flags import FLAG_PREDICATES, evaluate_flags, resolve_confidence
from sqft.floors import resolve_floors
from sqft.overture import compute_bbox
from sqft.parcels import NullParcelProvider
from sqft.schema import (
    Confidence,
    EstimateRow,
    FlagKey,
    GeocodeResult,
    GeocoderPrecision,
    GeocoderProvider,
    MatchMethod,
)
from sqft.spatial_join import join_points_to_buildings

pytestmark = pytest.mark.lane_b


def _load_geocoded(fixtures_dir: Path) -> list[GeocodeResult]:
    rows = pq.read_table(fixtures_dir / "geocoded.parquet").to_pylist()
    return [GeocodeResult.model_validate(r) for r in rows]


def _location_id_lookup(fixtures_dir: Path) -> dict[str, list[str]]:
    norm = pq.read_table(fixtures_dir / "normalized.parquet").to_pylist()
    lookup: dict[str, list[str]] = {}
    for row in norm:
        lookup.setdefault(row["address_key"], []).append(row["location_id"])
    return lookup


def _location_types(fixtures_dir: Path) -> dict[str, str]:
    norm = pq.read_table(fixtures_dir / "normalized.parquet").to_pylist()
    est = {r["location_id"]: r["location_type"] for r in pq.read_table(fixtures_dir / "estimates.parquet").to_pylist()}
    return {row["location_id"]: est[row["location_id"]] for row in norm}


def test_area_within_tolerance(fixtures_dir: Path) -> None:
    """polygon_area_sqft matches every entry in expected_areas.json within its tolerance."""
    cases = json.loads((fixtures_dir / "expected_areas.json").read_text())
    assert len(cases) >= 3
    for case in cases:
        poly = wkt.loads(case["polygon_wkt"])
        area = polygon_area_sqft(poly)
        assert case["expected_area_sqft_min"] <= area <= case["expected_area_sqft_max"], (
            f"{case['name']}: {area} not in [{case['expected_area_sqft_min']}, {case['expected_area_sqft_max']}]"
        )


def test_resolve_floors_warehouse_ignores_height() -> None:
    """A 12m warehouse must return 1 floor, never 3 (12 / 4)."""
    floors, source = resolve_floors(None, 12.0, "warehouse", FloorsConfig())
    assert floors == 1
    assert source.value in {"subtype_default", "overture_height"}


def test_resolve_floors_uses_num_floors_when_present() -> None:
    floors, source = resolve_floors(3, 40.0, "office", FloorsConfig())
    assert floors == 3
    assert source.value == "overture_num_floors"


def test_resolve_floors_caps_at_max() -> None:
    config = FloorsConfig(max_floors_cap=50, max_height_meters_for_inference=80.0)
    floors, _ = resolve_floors(None, 400.0, "office", config)
    assert floors == 50


def test_evaluate_flags_sets_bool_columns_and_json() -> None:
    row = EstimateRow(
        location_id="T1",
        address_input="500 Elm St Suite 200",
        address_key="k",
        pipeline_run_id="run",
        geocoder_precision=GeocoderPrecision.GEOMETRIC_CENTER,
        match_method=MatchMethod.WITHIN,
        building_id="B1",
        footprint_area_sqft=1000.0,
    )
    evaluate_flags(row)
    flags = json.loads(row.flags_json)
    assert "LOW_GEOCODE_PRECISION" in flags
    assert "SUITE_OR_TENANT_ADDRESS" in flags
    assert row.flag_low_geocode_precision
    assert row.flag_suite_or_tenant_address
    assert flags == [k.value for k in FlagKey if FLAG_PREDICATES[k](row)]


def test_resolve_confidence_rules() -> None:
    base = dict(
        location_id="T1",
        address_input="addr",
        address_key="k",
        pipeline_run_id="run",
        building_id="B1",
        match_method=MatchMethod.WITHIN,
    )
    assert resolve_confidence(EstimateRow(**base, geocoder_precision=GeocoderPrecision.ROOFTOP)) == Confidence.HIGH

    unmatched = EstimateRow(
        **{k: v for k, v in base.items() if k not in ("building_id", "match_method")},
        building_id=None,
        match_method=MatchMethod.UNMATCHED,
    )
    evaluate_flags(unmatched)
    assert resolve_confidence(unmatched) == Confidence.UNMATCHED

    low = EstimateRow(
        **{k: v for k, v in base.items() if k != "match_method"},
        match_method=MatchMethod.NEAREST_WITHIN_BUFFER,
        geocoder_precision=GeocoderPrecision.ROOFTOP,
    )
    evaluate_flags(low)
    assert resolve_confidence(low) == Confidence.LOW

    medium = EstimateRow(
        **base,
        geocoder_precision=GeocoderPrecision.GEOMETRIC_CENTER,
    )
    evaluate_flags(medium)
    assert resolve_confidence(medium) == Confidence.MEDIUM


def test_join_points_to_buildings_against_fixtures(fixtures_dir: Path) -> None:
    """Given fixture geocoded.parquet + footprints.parquet, produce matches that agree
    with the geometry-derived columns of fixture estimates.parquet."""
    geocoded = _load_geocoded(fixtures_dir)
    lookup = _location_id_lookup(fixtures_dir)
    loc_types = _location_types(fixtures_dir)
    matches = join_points_to_buildings(
        geocoded,
        fixtures_dir / "footprints.parquet",
        lookup,
        SpatialConfig(),
        NullParcelProvider(),
        loc_types,
    )
    by_id = {m.location_id: m for m in matches}
    expected = {r["location_id"]: r for r in pq.read_table(fixtures_dir / "estimates.parquet").to_pylist()}

    assert len(by_id) == len(expected)
    for location_id, exp in expected.items():
        got = by_id[location_id]
        assert got.chosen_building_id == exp["building_id"]
        assert got.match_method.value == exp["match_method"]
        assert got.multi_building_count == exp["multi_building_count"]
        if exp["building_id"]:
            chosen = [c for c in got.candidates if c.is_chosen]
            assert len(chosen) == 1
            assert chosen[0].building_id == exp["building_id"]
            assert chosen[0].distance_m == 0.0


def test_overture_compute_bbox_pads_correctly() -> None:
    geocoded = [
        GeocodeResult(
            address_key="a",
            lat=30.0,
            lon=-97.0,
            precision=GeocoderPrecision.ROOFTOP,
            provider=GeocoderProvider.GOOGLE_GEOCODING,
            status="ok",
        ),
        GeocodeResult(
            address_key="b",
            lat=31.0,
            lon=-96.0,
            precision=GeocoderPrecision.ROOFTOP,
            provider=GeocoderProvider.GOOGLE_GEOCODING,
            status="ok",
        ),
        GeocodeResult(
            address_key="skip",
            lat=None,
            lon=None,
            precision=GeocoderPrecision.UNKNOWN,
            provider=GeocoderProvider.GOOGLE_GEOCODING,
            status="failed",
        ),
    ]
    bbox = compute_bbox(geocoded, padding_deg=0.01)
    assert bbox == pytest.approx((-97.01, 29.99, -95.99, 31.01))
