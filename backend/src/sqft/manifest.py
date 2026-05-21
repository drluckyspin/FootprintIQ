"""Pipeline run manifest writer."""

from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqft.schema import RunManifest


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def new_run_id() -> str:
    ts = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    return f"{ts}__{suffix}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def code_git_sha(repo_root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            check=True,
            text=True,
        )
        return out.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def start_manifest(
    input_csv: Path,
    config_path: Path,
    repo_root: Path,
    overture_release: str,
    *,
    input_row_count: int,
) -> RunManifest:
    config_bytes = config_path.read_bytes() if config_path.exists() else b"{}"
    return RunManifest(
        pipeline_run_id=new_run_id(),
        started_at_utc=utc_now(),
        code_git_sha=code_git_sha(repo_root),
        config_sha256=hashlib.sha256(config_bytes).hexdigest(),
        input_csv_path=str(input_csv.resolve()),
        input_csv_sha256=sha256_file(input_csv),
        input_row_count=input_row_count,
        overture_release=overture_release,
        output_estimates_path="",
    )


def manifest_output_path(data_dir: Path, run_id: str) -> Path:
    return data_dir / "output" / f"run_{run_id}" / "manifest.json"


def finalize_manifest(
    manifest: RunManifest,
    output_path: Path,
    output_estimates_path: Path,
) -> Path:
    manifest.finished_at_utc = utc_now()
    manifest.output_estimates_path = str(output_estimates_path.resolve())
    if output_estimates_path.exists():
        manifest.output_estimates_sha256 = sha256_file(output_estimates_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = manifest.model_dump(mode="json")
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return output_path


def save_manifest(manifest: RunManifest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True)
    )
