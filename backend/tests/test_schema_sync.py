"""Schema-sync test: ensures backend pydantic models and frontend zod schemas list
the same fields. Runs in Wave 0; gating for any PR that touches schema.py / schema.ts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from sqft import schema

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SCHEMA = REPO_ROOT / "frontend" / "lib" / "schema.ts"


pytestmark = pytest.mark.smoke


def _parse_zod_field_names(ts_source: str, type_name: str) -> set[str]:
    """Extract field names from `export const <TypeName>Schema = z.object({ ... })`.

    Uses a brace-counter (not pure regex) so default values like `.default({})` don't
    close the body match prematurely. Also strips out nested object literals and
    parenthesized expressions before scanning, so only top-level `field:` patterns
    at depth 1 are captured.
    """
    anchor = re.search(rf"export\s+const\s+{type_name}Schema\s*=\s*z\.object\(\s*\{{", ts_source)
    if anchor is None:
        raise AssertionError(f"could not locate zod schema {type_name}Schema in {FRONTEND_SCHEMA}")
    start = anchor.end()  # position right after the opening `{`
    depth = 1
    i = start
    while i < len(ts_source) and depth > 0:
        c = ts_source[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        i += 1
    if depth != 0:
        raise AssertionError(f"unbalanced braces in {type_name}Schema in {FRONTEND_SCHEMA}")
    body = ts_source[start : i - 1]  # exclude the matching `}`

    # Walk through body capturing identifiers at depth 0 followed by ':' (allowing optional '?').
    # Skip everything inside parentheses or nested braces so default-value object literals etc.
    # don't introduce false positives.
    fields: set[str] = set()
    paren = 0
    brace = 0
    j = 0
    while j < len(body):
        c = body[j]
        if c == "(":
            paren += 1
        elif c == ")":
            paren -= 1
        elif c == "{":
            brace += 1
        elif c == "}":
            brace -= 1
        if paren == 0 and brace == 0 and (c.isalpha() or c == "_"):
            # try to grab an identifier
            m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*\??\s*:", body[j:])
            if m:
                fields.add(m.group(1))
                j += m.end()
                continue
        j += 1
    return fields


# Pairs of (pydantic class, zod TypeName). Add to this list when adding new contracts.
PAIRS = [
    (schema.RawAddress, "RawAddress"),
    (schema.NormalizedAddress, "NormalizedAddress"),
    (schema.GeocodeResult, "GeocodeResult"),
    (schema.Footprint, "Footprint"),
    (schema.CandidateBuilding, "CandidateBuilding"),
    (schema.BuildingMatch, "BuildingMatch"),
    (schema.EstimateRow, "EstimateRow"),
    (schema.RunManifest, "RunManifest"),
    (schema.QaReview, "QaReview"),
]


@pytest.mark.parametrize("py_model,ts_name", PAIRS)
def test_pydantic_zod_field_parity(py_model, ts_name: str) -> None:
    if not FRONTEND_SCHEMA.exists():
        pytest.skip(f"frontend schema not present yet: {FRONTEND_SCHEMA}")
    py_fields = set(py_model.model_fields.keys())
    ts_fields = _parse_zod_field_names(FRONTEND_SCHEMA.read_text(), ts_name)
    missing_in_ts = py_fields - ts_fields
    extra_in_ts = ts_fields - py_fields
    assert not missing_in_ts and not extra_in_ts, (
        f"schema drift in {ts_name}: "
        f"missing in ts={sorted(missing_in_ts)}, extra in ts={sorted(extra_in_ts)}"
    )


def test_flag_keys_listed_in_estimate_row_columns() -> None:
    """Each FlagKey must have a flag_<lower_snake> boolean column on EstimateRow."""
    py_fields = set(schema.EstimateRow.model_fields.keys())
    for key in schema.FlagKey:
        col = f"flag_{key.value.lower()}"
        assert col in py_fields, f"{col} missing on EstimateRow for {key}"


# Helper not exported (silence unused-import linters)
_ = json
