"""I/O helpers. Wave 0 stub — Lane C implements the real ones.

Centralizes:
- CSV input reader (validates against RawAddress)
- Parquet readers/writers for each stage, enforcing the frozen column lists from schema.py
- Path resolution helpers
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from sqft.schema import (
    ESTIMATES_COLS,
    FOOTPRINTS_COLS,
    GEOCODED_COLS,
    NORMALIZED_COLS,
    QA_REVIEWS_COLS,
)

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def data_path(data_dir: Path, *parts: str) -> Path:
    """Resolve `data_dir / *parts`, creating parent dirs."""
    p = Path(data_dir, *parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def interim_path(data_dir: Path, name: str) -> Path:
    return data_path(data_dir, "interim", name)


def output_path(data_dir: Path, name: str) -> Path:
    return data_path(data_dir, "output", name)


# ---------------------------------------------------------------------------
# CSV input
# ---------------------------------------------------------------------------


def read_input_csv(path: Path) -> list[dict]:
    """Read input addresses CSV. Wave 0 stub.

    Lane C MUST:
      - Validate each row against schema.RawAddress
      - Raise with a precise row number on validation failure
      - Return list[dict] (or pyarrow Table) suitable for downstream stages
    """
    raise NotImplementedError("Lane C: implement read_input_csv")


# ---------------------------------------------------------------------------
# Parquet readers/writers
# ---------------------------------------------------------------------------


_COLS_BY_KIND: dict[str, tuple[str, ...]] = {
    "normalized": NORMALIZED_COLS,
    "geocoded": GEOCODED_COLS,
    "footprints": FOOTPRINTS_COLS,
    "estimates": ESTIMATES_COLS,
    "qa_reviews": QA_REVIEWS_COLS,
}


def expected_columns(kind: str) -> tuple[str, ...]:
    """Return the frozen column list for a given parquet stage."""
    if kind not in _COLS_BY_KIND:
        raise KeyError(f"unknown parquet kind: {kind}; valid: {sorted(_COLS_BY_KIND)}")
    return _COLS_BY_KIND[kind]


def read_parquet(path: Path, kind: str) -> pa.Table:
    """Read parquet and validate column set matches the frozen contract for `kind`."""
    table = pq.read_table(path)
    expected = set(expected_columns(kind))
    actual = set(table.column_names)
    missing = expected - actual
    extra = actual - expected
    if missing or extra:
        raise ValueError(
            f"parquet {path} column mismatch for kind={kind}: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    return table


def write_parquet(rows: Iterable[dict], path: Path, kind: str) -> None:
    """Write rows to parquet, enforcing the frozen column order for `kind`."""
    cols = expected_columns(kind)
    rows_list = list(rows)
    if not rows_list:
        # Empty table with correct schema — use pyarrow's schema-from-empty trick.
        table = pa.table({c: pa.array([], type=pa.string()) for c in cols})
    else:
        # Reorder + project columns
        projected = [{c: r.get(c) for c in cols} for r in rows_list]
        table = pa.Table.from_pylist(projected)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


# Lane C may also need: append_parquet, schema-coerced from pydantic, etc.
