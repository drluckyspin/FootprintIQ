"""Lane C — pipeline + manifest + validate + io + config. Skipped until Lane C lands."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.lane_c, pytest.mark.skip(reason="Lane C not yet implemented")]


def test_read_input_csv_validates_rows(sample_addresses_csv: Path) -> None:
    """RawAddress validation: malformed rows surface with row numbers."""
    raise NotImplementedError("Lane C: implement this test")


def test_load_settings_yaml_and_env_overrides(tmp_path: Path, monkeypatch) -> None:
    raise NotImplementedError("Lane C: implement this test")


def test_pipeline_reproduces_fixture_estimates(tmp_path: Path, fixtures_dir: Path) -> None:
    """Run the pipeline against fixture inputs (or stub the geocoder/Overture stages
    by reading the fixture parquet files), and assert the output matches
    fixture estimates.parquet on the geometry-derived columns."""
    raise NotImplementedError("Lane C: implement this test")


def test_manifest_round_trip(tmp_path: Path) -> None:
    """start_manifest then finalize_manifest produces a valid RunManifest JSON
    that re-parses without errors."""
    raise NotImplementedError("Lane C: implement this test")


def test_generate_report_renders_without_ground_truth(tmp_path: Path, fixtures_dir: Path) -> None:
    raise NotImplementedError("Lane C: implement this test")


def test_generate_qa_worksheet_is_stratified_and_reproducible(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    """Same seed -> same worksheet rows; strata are balanced (no empty stratum if data allows)."""
    raise NotImplementedError("Lane C: implement this test")
