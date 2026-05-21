"""I/O helpers."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import ValidationError

from sqft.schema import (
    ESTIMATES_COLS,
    FOOTPRINTS_COLS,
    GEOCODED_COLS,
    NORMALIZED_COLS,
    QA_REVIEWS_COLS,
    RawAddress,
)

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def data_path(data_dir: Path, *parts: str) -> Path:
    p = Path(data_dir, *parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def interim_path(data_dir: Path, name: str) -> Path:
    return data_path(data_dir, "interim", f"{name}.parquet")


def output_path(data_dir: Path, name: str) -> Path:
    return data_path(data_dir, "output", f"{name}.parquet")


# ---------------------------------------------------------------------------
# CSV input
# ---------------------------------------------------------------------------


def read_input_csv(path: Path) -> list[RawAddress]:
    rows: list[RawAddress] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            state = (row.get("state") or "").strip()
            if len(state) < 2:
                state = "XX"
            row["state"] = state
            try:
                rows.append(RawAddress.model_validate(row))
            except ValidationError as exc:
                raise ValueError(f"invalid row {line_no} in {path}: {exc}") from exc
    return rows


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
    if kind not in _COLS_BY_KIND:
        raise KeyError(f"unknown parquet kind: {kind}; valid: {sorted(_COLS_BY_KIND)}")
    return _COLS_BY_KIND[kind]


def read_parquet(path: Path, kind: str) -> pa.Table:
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
    cols = expected_columns(kind)
    rows_list = list(rows)
    if not rows_list:
        table = pa.table({c: pa.array([], type=pa.string()) for c in cols})
    else:
        projected = [{c: r.get(c) for c in cols} for r in rows_list]
        table = pa.Table.from_pylist(projected)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def read_parquet_dicts(path: Path, kind: str) -> list[dict]:
    return read_parquet(path, kind).to_pylist()


def models_to_rows(models: Iterable, kind: str) -> list[dict]:
    return [m.model_dump(mode="json") for m in models]
