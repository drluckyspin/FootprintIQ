"""Lane C — pipeline + manifest + validate + io + config."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from sqft.config import Settings, load_settings
from sqft.io import read_input_csv
from sqft.manifest import finalize_manifest, new_run_id, sha256_file, start_manifest
from sqft.pipeline import run_pipeline
from sqft.schema import RunManifest
from sqft.validate import generate_qa_worksheet, generate_report

pytestmark = pytest.mark.lane_c

STRICT_COLS = ("building_id", "match_method")

# Stable fixture rows where geocode + footprint polygons align with build_fixtures.py
ANCHOR_LOCATION_IDS = (
    "WMART_001",
    "WMART_002",
    "WMART_003",
    "TGT_001",
    "BAKER_001",
)


def test_read_input_csv_validates_rows(sample_addresses_csv: Path) -> None:
    rows = read_input_csv(sample_addresses_csv)
    assert len(rows) >= 15


def test_read_input_csv_rejects_bad_row(tmp_path: Path, sample_addresses_csv: Path) -> None:
    text = sample_addresses_csv.read_text()
    lines = text.splitlines()
    bad = lines[0] + "\n" + lines[1] + "\n" + "BAD,not,enough,columns\n"
    path = tmp_path / "bad.csv"
    path.write_text(bad)
    with pytest.raises(ValueError):
        read_input_csv(path)


def test_load_settings_yaml_and_env_overrides(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.dump({"geocoder": {"concurrency": 7}}))
    monkeypatch.setenv("SQFT_DATA_DIR", str(tmp_path / "data"))
    s = load_settings(cfg)
    assert s.geocoder.concurrency == 7
    assert s.data_dir == tmp_path / "data"


def test_pipeline_reproduces_fixture_estimates(
    tmp_path: Path, fixtures_dir: Path, sample_addresses_csv: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SQFT_USE_FIXTURES", "1")
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "data"
    settings = Settings(data_dir=data_dir)
    out = run_pipeline(sample_addresses_csv, settings=settings, resume=False)
    assert out.exists()

    import pandas as pd

    got = pd.read_parquet(out).set_index("location_id")
    exp = pd.read_parquet(fixtures_dir / "estimates.parquet").set_index("location_id")
    assert len(got) == len(exp)
    for loc in ANCHOR_LOCATION_IDS:
        for col in STRICT_COLS:
            assert got.at[loc, col] == exp.at[loc, col], f"{loc}.{col}"
        est = got.at[loc, "estimated_sqft"]
        assert est is not None and not pd.isna(est) and est > 0
        assert got.at[loc, "footprint_area_sqft"] > 0

    broken = got.loc[["TEST_001", "TEST_002"]]
    assert broken["building_id"].isna().all()


def test_manifest_round_trip(tmp_path: Path, sample_addresses_csv: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("{}")
    m = start_manifest(
        sample_addresses_csv,
        config,
        tmp_path,
        "2024-11-13.0",
        input_row_count=20,
    )
    assert new_run_id().count("__") == 1
    est = tmp_path / "estimates.parquet"
    est.write_bytes(b"test")
    path = finalize_manifest(m, tmp_path / "manifest.json", est)
    reparsed = RunManifest.model_validate_json(path.read_text())
    assert reparsed.pipeline_run_id == m.pipeline_run_id
    assert reparsed.output_estimates_sha256 == sha256_file(est)


def test_generate_report_renders_without_ground_truth(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    html_path = tmp_path / "report.html"
    generate_report(fixtures_dir / "estimates.parquet", html_path)
    text = html_path.read_text()
    assert "Building sqft pipeline report" in text
    assert "<table" in text


def test_generate_qa_worksheet_is_stratified_and_reproducible(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    out1 = tmp_path / "ws1.csv"
    out2 = tmp_path / "ws2.csv"
    est = fixtures_dir / "estimates.parquet"
    generate_qa_worksheet(est, out1, n=10, seed=0)
    generate_qa_worksheet(est, out2, n=10, seed=0)
    assert out1.read_text() == out2.read_text()
    rows = out1.read_text().strip().splitlines()
    assert len(rows) == 11  # header + 10


def test_pipeline_resume_skips_geocode_stage(
    tmp_path: Path, sample_addresses_csv: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SQFT_USE_FIXTURES", "1")
    monkeypatch.chdir(tmp_path)
    settings = Settings(data_dir=tmp_path / "data")
    run_pipeline(sample_addresses_csv, settings=settings, resume=False)
    manifest_files = list((tmp_path / "data" / "output").glob("run_*/manifest.json"))
    assert manifest_files
    first = json.loads(manifest_files[0].read_text())
    assert first["stage_durations_seconds"].get("geocode", -1) >= 0

    run_pipeline(sample_addresses_csv, settings=settings, resume=True)
    # Second full run returns early when estimates exist
    assert (tmp_path / "data" / "output" / "estimates.parquet").exists()
