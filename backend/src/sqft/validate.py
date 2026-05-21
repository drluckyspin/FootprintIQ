"""Validation + HTML report generation + stratified ground-truth sampler. OWNED BY LANE C.

Wave 0 stub.
"""

from __future__ import annotations

from pathlib import Path


def generate_report(
    estimates_path: Path,
    output_html: Path,
    ground_truth_csv: Path | None = None,
) -> Path:
    """Render data/output/report.html with:

    Sections (per plan):
      - Coverage summary (% geocoded, % matched, % with floors), broken down by location_type
      - Geocoding precision distribution (bar chart, matplotlib -> PNG embedded)
      - Footprint area histogram (log scale)
      - Multi-building parcel rate
      - Per-state coverage map (if feasible without internet at report time)
      - Candidate-count distribution
      - "% rows where chosen building was not the largest within buffer" (watchdog)
      - If ground_truth_csv provided: scatter (estimated vs actual), MAPE, residual plot,
        table of worst 20 misses

    Returns the path of the written HTML file.
    """
    raise NotImplementedError("Lane C: implement generate_report")


def generate_qa_worksheet(
    estimates_path: Path,
    output_csv: Path,
    n: int = 200,
    seed: int = 0,
) -> Path:
    """Stratified sample of `n` rows across (location_type, confidence, footprint-size decile).

    Lane C MUST:
      - Use a fixed RNG seed for reproducibility
      - Balance across strata; if a stratum is empty, redistribute to others
      - Output columns: location_id, address_input, estimated_sqft, confidence,
                        flags_json, actual_sqft (empty for hand-fill), notes (empty)
    """
    raise NotImplementedError("Lane C: implement generate_qa_worksheet")
