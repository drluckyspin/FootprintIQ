"""Centralized flag/confidence rule evaluation. OWNED BY LANE B.

Each flag is a pure predicate over a partially-built EstimateRow.
Produces both:
  - boolean columns (flag_no_building_match, etc. — set on EstimateRow directly)
  - flags_json   = JSON array of FlagKey strings (stable ordering for downstream tools)
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from sqft.schema import (
    Confidence,
    EstimateRow,
    FlagKey,
    GeocoderPrecision,
    MatchMethod,
)

# Tunable thresholds (Wave 0 defaults; Lane B may move these into config later if desired).
AREA_MIN_SQFT = 500.0
AREA_MAX_SQFT = 5_000_000.0  # high enough to include Amazon BFI4 (~3.6M)
OLD_FOOTPRINT_YEAR = 2018
HEIGHT_OUTLIER_M = 200.0  # any taller is almost certainly a parse artifact
TALL_BUILDING_M = 12.0  # buildings >12m without floor data trigger MISSING_FLOORS_TALL_BUILDING


# Each FlagPredicate takes the EstimateRow being built and returns True if the flag applies.
FlagPredicate = Callable[[EstimateRow], bool]


def _flag_no_building_match(r: EstimateRow) -> bool:
    return r.building_id is None or r.match_method == MatchMethod.UNMATCHED


def _flag_low_geocode_precision(r: EstimateRow) -> bool:
    return r.geocoder_precision not in {
        GeocoderPrecision.ROOFTOP,
        GeocoderPrecision.RANGE_INTERPOLATED,
    }


def _flag_multi_building_parcel(r: EstimateRow) -> bool:
    return r.multi_building_count > 1


def _flag_old_footprint(r: EstimateRow) -> bool:
    return bool(r.overture_update_time and r.overture_update_time.year < OLD_FOOTPRINT_YEAR)


def _flag_nearest_fallback(r: EstimateRow) -> bool:
    return r.match_method == MatchMethod.NEAREST_WITHIN_BUFFER


def _flag_area_out_of_range(r: EstimateRow) -> bool:
    if r.footprint_area_sqft is None:
        return False
    return r.footprint_area_sqft < AREA_MIN_SQFT or r.footprint_area_sqft > AREA_MAX_SQFT


def _flag_height_outlier(r: EstimateRow) -> bool:
    return bool(r.raw_overture_height is not None and r.raw_overture_height > HEIGHT_OUTLIER_M)


def _flag_missing_floors_tall_building(r: EstimateRow) -> bool:
    return bool(
        r.raw_overture_num_floors is None
        and r.raw_overture_height is not None
        and r.raw_overture_height > TALL_BUILDING_M
    )


def _flag_geocode_failed(r: EstimateRow) -> bool:
    return r.geocoded_lat is None or r.geocoded_lon is None


def _flag_suite_or_tenant_address(r: EstimateRow) -> bool:
    # heuristic: address_input contains a unit marker
    s = (r.address_input or "").lower()
    return any(tok in s for tok in (" suite ", " ste ", " unit ", " #", " apt "))


FLAG_PREDICATES: dict[FlagKey, FlagPredicate] = {
    FlagKey.NO_BUILDING_MATCH: _flag_no_building_match,
    FlagKey.LOW_GEOCODE_PRECISION: _flag_low_geocode_precision,
    FlagKey.MULTI_BUILDING_PARCEL: _flag_multi_building_parcel,
    FlagKey.OLD_FOOTPRINT: _flag_old_footprint,
    FlagKey.NEAREST_FALLBACK: _flag_nearest_fallback,
    FlagKey.AREA_OUT_OF_RANGE: _flag_area_out_of_range,
    FlagKey.HEIGHT_OUTLIER: _flag_height_outlier,
    FlagKey.MISSING_FLOORS_TALL_BUILDING: _flag_missing_floors_tall_building,
    FlagKey.GEOCODE_FAILED: _flag_geocode_failed,
    FlagKey.SUITE_OR_TENANT_ADDRESS: _flag_suite_or_tenant_address,
}


def evaluate_flags(row: EstimateRow) -> EstimateRow:
    """Set every boolean flag column AND flags_json on the row in-place; return it.

    Lane B MUST keep this pure: input row + same dictionary -> same output, no I/O.
    """
    raise NotImplementedError("Lane B: implement evaluate_flags")


def resolve_confidence(row: EstimateRow) -> Confidence:
    """Apply the confidence rules (high/medium/low/unmatched).

    Lane B MUST follow the rules in the plan:
      - unmatched: building_id is None
      - low: flag_nearest_fallback OR flag_missing_floors_tall_building OR flag_area_out_of_range
      - medium: flag_low_geocode_precision OR flag_multi_building_parcel OR flag_old_footprint
      - high: otherwise
    """
    raise NotImplementedError("Lane B: implement resolve_confidence")


# Convenience for tests
def _selected_flags(row: EstimateRow) -> list[str]:
    """Read FLAG_PREDICATES and return [FlagKey.value, ...] for the row, stable order."""
    return [k.value for k in FlagKey if FLAG_PREDICATES[k](row)]


_ = (json, Any)  # keep imports
