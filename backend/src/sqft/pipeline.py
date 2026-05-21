"""Pipeline orchestration. OWNED BY LANE C.

Chains: normalize -> dedup -> geocode -> overture -> spatial_join -> floors/area/flags -> estimates.

Resume rule: if `data/interim/<stage>.parquet` exists for the current input hash, skip the stage.

Wave 0 stub.
"""

from __future__ import annotations

from pathlib import Path

from sqft.config import Settings
from sqft.schema import RunManifest


def run(
    input_csv: Path,
    settings: Settings,
    *,
    sample_size: int | None = None,
    max_cost_usd: float | None = None,
    resume: bool = True,
) -> tuple[Path, RunManifest]:
    """Run the full pipeline. Returns (estimates_path, manifest).

    Lane C MUST:
      - Pre-flight: estimate cost, abort if > max_cost_usd unless explicit confirm
      - Stage 1 normalize+dedup -> data/interim/normalized.parquet
      - Stage 2 geocode (Lane A) -> data/interim/geocoded.parquet
      - Stage 3 overture (Lane B) -> data/interim/footprints.parquet
      - Stage 4 spatial_join + area + floors + flags (Lane B) -> data/output/estimates.parquet
      - Resume logic per stage (use io helpers; check file existence + manifest hash)
      - Write run manifest sidecar via manifest.finalize_manifest
      - Surface row counts in/out per stage and total elapsed
    """
    raise NotImplementedError("Lane C: implement pipeline.run")
