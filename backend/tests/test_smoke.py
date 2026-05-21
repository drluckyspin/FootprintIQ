"""Wave 0 smoke tests — must pass before any lane begins.

These verify that the project skeleton is intact and the frozen contracts load.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sqft import schema
from sqft.config import Settings, load_settings

pytestmark = pytest.mark.smoke


def test_schema_module_loads() -> None:
    """Every type referenced by the lanes is importable."""
    assert schema.RawAddress
    assert schema.NormalizedAddress
    assert schema.GeocodeResult
    assert schema.Footprint
    assert schema.BuildingMatch
    assert schema.EstimateRow
    assert schema.RunManifest
    assert schema.QaReview


def test_settings_defaults_load() -> None:
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert settings.geocoder.concurrency > 0
    assert settings.spatial.search_buffer_meters > 0
    assert settings.floors.default >= 1


def test_estimate_row_has_all_flag_columns() -> None:
    """Every FlagKey has a matching flag_<lower_snake> column on EstimateRow."""
    fields = set(schema.EstimateRow.model_fields.keys())
    for key in schema.FlagKey:
        col = f"flag_{key.value.lower()}"
        assert col in fields, f"missing column {col} for flag {key}"


def test_parquet_column_constants_are_tuples_of_strings() -> None:
    for cols in (
        schema.NORMALIZED_COLS,
        schema.GEOCODED_COLS,
        schema.FOOTPRINTS_COLS,
        schema.ESTIMATES_COLS,
        schema.QA_REVIEWS_COLS,
    ):
        assert isinstance(cols, tuple)
        assert all(isinstance(c, str) for c in cols)
        assert len(cols) > 0


def test_sample_addresses_csv_exists(sample_addresses_csv: Path) -> None:
    assert sample_addresses_csv.exists(), "fixtures missing — run build_fixtures.py"
    text = sample_addresses_csv.read_text().strip().splitlines()
    assert text[0].startswith("location_id,")
    assert len(text) == 21, f"expected 20 data rows + 1 header, got {len(text)}"


def test_fixture_parquets_exist(fixtures_dir: Path) -> None:
    for name in ("normalized", "geocoded", "footprints", "estimates", "qa_reviews"):
        p = fixtures_dir / f"{name}.parquet"
        assert p.exists(), f"fixture missing: {p} (run build_fixtures.py)"
