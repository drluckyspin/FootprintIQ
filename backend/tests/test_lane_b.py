"""Lane B — spatial. Tests skip until Lane B implements the stubs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.lane_b, pytest.mark.skip(reason="Lane B not yet implemented")]


def test_area_within_tolerance(fixtures_dir: Path) -> None:
    """polygon_area_sqft matches every entry in expected_areas.json within its tolerance."""
    cases = json.loads((fixtures_dir / "expected_areas.json").read_text())
    assert len(cases) >= 3
    raise NotImplementedError("Lane B: implement this test")


def test_resolve_floors_warehouse_ignores_height() -> None:
    """A 12m warehouse must return 1 floor, never 3 (12 / 4)."""
    raise NotImplementedError("Lane B: implement this test")


def test_resolve_floors_uses_num_floors_when_present() -> None:
    raise NotImplementedError("Lane B: implement this test")


def test_resolve_floors_caps_at_max() -> None:
    raise NotImplementedError("Lane B: implement this test")


def test_evaluate_flags_sets_bool_columns_and_json() -> None:
    """boolean columns and flags_json must agree (same set of flags)."""
    raise NotImplementedError("Lane B: implement this test")


def test_resolve_confidence_rules() -> None:
    """unmatched/low/medium/high are produced per the plan's rules."""
    raise NotImplementedError("Lane B: implement this test")


def test_join_points_to_buildings_against_fixtures(fixtures_dir: Path) -> None:
    """Given fixture geocoded.parquet + footprints.parquet, produce matches that agree
    with the geometry-derived columns of fixture estimates.parquet."""
    raise NotImplementedError("Lane B: implement this test")


def test_overture_compute_bbox_pads_correctly() -> None:
    raise NotImplementedError("Lane B: implement this test")
