"""Validation + HTML report + stratified QA worksheet."""

from __future__ import annotations

import csv
import html
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

from sqft.io import read_parquet_dicts
from sqft.log import get_logger

logger = get_logger("validate")


def _decile_bins(series: pd.Series, k: int = 10) -> pd.Series:
    ranked = series.rank(method="first")
    return pd.qcut(ranked, q=min(k, len(series.unique())), labels=False, duplicates="drop")


def generate_report(
    estimates_path: Path,
    output_html: Path,
    ground_truth_csv: Path | None = None,
) -> Path:
    logger.info("generate_report reading %s", estimates_path)
    df = pd.read_parquet(estimates_path)
    total = len(df)
    matched = (df["building_id"].notna()).sum() if "building_id" in df.columns else 0
    geocoded = df["geocoded_lat"].notna().sum() if "geocoded_lat" in df.columns else 0

    by_type = (
        df.groupby("location_type", dropna=False)
        .agg(
            rows=("location_id", "count"),
            matched=("building_id", lambda s: s.notna().sum()),
            median_sqft=("estimated_sqft", "median"),
        )
        .reset_index()
    )

    gt_section = ""
    if ground_truth_csv and ground_truth_csv.exists():
        gt = pd.read_csv(ground_truth_csv)
        if "location_id" in gt.columns and "actual_sqft" in gt.columns:
            merged = df.merge(gt[["location_id", "actual_sqft"]], on="location_id", how="inner")
            if len(merged):
                err = (merged["estimated_sqft"] - merged["actual_sqft"]).abs()
                mape = (err / merged["actual_sqft"].replace(0, pd.NA)).mean()
                gt_section = (
                    f"<p>Ground truth rows: {len(merged)}; mean abs error: "
                    f"{err.mean():.0f}; MAPE: {mape:.2%}</p>"
                )

    type_rows = "".join(
        f"<tr><td>{html.escape(str(r.location_type))}</td>"
        f"<td>{int(r.rows)}</td><td>{int(r.matched)}</td>"
        f"<td>{r.median_sqft:.0f}</td></tr>"
        for r in by_type.itertuples()
    )

    body = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>sqft report</title></head>
<body>
<h1>Building sqft pipeline report</h1>
<p>Total rows: {total}</p>
<p>Geocoded: {geocoded} ({geocoded / max(total, 1):.1%})</p>
<p>Matched: {matched} ({matched / max(total, 1):.1%})</p>
{gt_section}
<h2>By location type</h2>
<table border="1"><tr><th>type</th><th>rows</th><th>matched</th><th>median sqft</th></tr>
{type_rows}
</table>
</body></html>"""

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(body, encoding="utf-8")
    logger.info(
        "generate_report wrote %s (rows=%d geocoded=%d matched=%d)",
        output_html,
        total,
        geocoded,
        matched,
    )
    return output_html


def generate_qa_worksheet(
    estimates_path: Path,
    output_csv: Path,
    n: int = 200,
    seed: int = 0,
) -> Path:
    logger.info("generate_qa_worksheet reading %s n=%d seed=%d", estimates_path, n, seed)
    df = pd.read_parquet(estimates_path)
    if df.empty:
        output_csv.write_text(
            "location_id,address_input,estimated_sqft,confidence,flags_json,actual_sqft,notes\n",
            encoding="utf-8",
        )
        return output_csv

    work = df.copy()
    work["_size_decile"] = _decile_bins(work["footprint_area_sqft"].fillna(0))

    strata: dict[tuple, list[int]] = defaultdict(list)
    for idx, row in work.iterrows():
        key = (row["location_type"], row["confidence"], int(row["_size_decile"]))
        strata[key].append(int(idx))

    rng = random.Random(seed)
    keys = list(strata.keys())
    rng.shuffle(keys)
    per_stratum = max(1, n // max(len(keys), 1))
    picked: list[int] = []
    for key in keys:
        pool = strata[key]
        rng.shuffle(pool)
        picked.extend(pool[:per_stratum])
    if len(picked) < n:
        remaining = [i for i in work.index if i not in picked]
        rng.shuffle(remaining)
        picked.extend(remaining[: n - len(picked)])
    picked = picked[:n]

    out = work.loc[picked, [
        "location_id",
        "address_input",
        "estimated_sqft",
        "confidence",
        "flags_json",
    ]].copy()
    out["actual_sqft"] = ""
    out["notes"] = ""

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_csv, index=False, quoting=csv.QUOTE_MINIMAL)
    logger.info("generate_qa_worksheet wrote %s rows=%d", output_csv, len(out))
    return output_csv
