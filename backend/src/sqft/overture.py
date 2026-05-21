"""Overture Maps building-footprint loader. OWNED BY LANE B.

Queries Overture's S3 parquet via DuckDB+httpfs+spatial. Never downloads the full CONUS dataset.
Bbox derived from successfully-geocoded points (with padding).

Wave 0 stub.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from sqft.config import OvertureConfig
from sqft.schema import GeocodeResult

DEFAULT_BBOX_PADDING_DEG = 0.005  # ~500m at mid-latitudes; tune per Lane B's measurements


def resolve_release(config: OvertureConfig) -> str:
    """If config.release == 'latest', resolve to the current release string.

    Lane B MUST:
      - Hit Overture's docs API or the latest known convention (e.g. parse from
        https://docs.overturemaps.org/releases/) — never hardcode
      - Cache the result for the duration of the run
      - Return a string like "2025-07-23.0"
    """
    raise NotImplementedError("Lane B: implement resolve_release")


def compute_bbox(
    geocoded: list[GeocodeResult], padding_deg: float = DEFAULT_BBOX_PADDING_DEG
) -> tuple[float, float, float, float]:
    """Return (min_lon, min_lat, max_lon, max_lat) over geocoded points (status='ok').

    Lane B MUST:
      - Ignore rows without lat/lon
      - Apply `padding_deg` symmetrically
      - For huge inputs, consider splitting into per-state tiles (returning multiple bboxes
        instead). Wave 0 contract: return a single bbox; multi-bbox support is internal to
        fetch_footprints.
    """
    raise NotImplementedError("Lane B: implement compute_bbox")


def fetch_footprints(
    geocoded: list[GeocodeResult],
    config: OvertureConfig,
    output_path: Path,
    duckdb_con: duckdb.DuckDBPyConnection | None = None,
) -> Path:
    """Run the DuckDB-over-S3 query and write footprints.parquet.

    Lane B MUST:
      - INSTALL/LOAD spatial and httpfs
      - Use bbox push-down via `bbox.xmin/xmax/ymin/ymax` columns
      - SELECT: id, geometry, height, num_floors, class, subtype, sources, version, update_time
      - Project geometry to WKB on write (the schema.Footprint contract)
      - Return the output_path on success
    """
    raise NotImplementedError("Lane B: implement fetch_footprints")
