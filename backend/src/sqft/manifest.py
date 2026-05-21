"""Pipeline run manifest writer. OWNED BY LANE C.

Captures every reproducibility-relevant fact about a pipeline run into
data/output/run_<id>/manifest.json.

Wave 0 stub.
"""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqft.schema import RunManifest


def new_run_id() -> str:
    """Return a short, sortable run id (timestamp + uuid7-ish suffix).

    Lane C MUST: format like "20260521T030500Z__abcd1234".
    """
    raise NotImplementedError("Lane C: implement new_run_id")


def sha256_file(path: Path) -> str:
    """Return hex-encoded sha256 of a file's contents (streaming, for large parquet)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def code_git_sha(repo_root: Path) -> str | None:
    """Return current `git rev-parse HEAD` (short) for repo_root, or None if not a git repo."""
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
) -> RunManifest:
    """Initialize a RunManifest at pipeline start.

    Lane C MUST:
      - new_run_id()
      - sha256_file(input_csv) -> input_csv_sha256
      - sha256_file(config_path) -> config_sha256 (or hash of resolved Settings JSON)
      - code_git_sha(repo_root)
      - started_at_utc = now(UTC)
      - input_row_count = wc -l (minus header) or via io.read_input_csv
    """
    raise NotImplementedError("Lane C: implement start_manifest")


def finalize_manifest(
    manifest: RunManifest,
    output_path: Path,
    output_estimates_path: Path,
) -> Path:
    """Write the final manifest.json. Returns the written path.

    Lane C MUST:
      - finished_at_utc = now(UTC)
      - output_estimates_sha256 = sha256_file(output_estimates_path)
      - Pretty-print JSON (indent=2, sort_keys=True for deterministic diffs)
      - Write to output_path
    """
    raise NotImplementedError("Lane C: implement finalize_manifest")


# Tiny helper Lane C may import:
def utc_now() -> datetime:
    return datetime.now(tz=UTC)


_ = uuid  # silence "imported but unused" until Lane C uses it
