"""Centralized flag/confidence rule evaluation. OWNED BY LANE B."""

from __future__ import annotations

import json
from collections.abc import Callable

from sqft.schema import (
    Confidence,
    EstimateRow,
    FlagKey,
    GeocoderPrecision,
    MatchMethod,
)

AREA_MIN_SQFT = 500.0
AREA_MAX_SQFT = 5_000_000.0
OLD_FOOTPRINT_YEAR = 2018
HEIGHT_OUTLIER_M = 200.0
TALL_BUILDING_M = 12.0

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

_FLAG_COLUMN_BY_KEY: dict[FlagKey, str] = {
    key: f"flag_{key.value.lower()}" for key in FlagKey
}


def evaluate_flags(row: EstimateRow) -> EstimateRow:
    """Set every boolean flag column AND flags_json on the row in-place; return it."""
    active: list[str] = []
    for key in FlagKey:
        applies = FLAG_PREDICATES[key](row)
        setattr(row, _FLAG_COLUMN_BY_KEY[key], applies)
        if applies:
            active.append(key.value)
    row.flags_json = json.dumps(active)
    return row


def resolve_confidence(row: EstimateRow) -> Confidence:
    """Apply the confidence rules (high/medium/low/unmatched)."""
    if row.building_id is None:
        return Confidence.UNMATCHED
    if (
        row.flag_nearest_fallback
        or row.flag_missing_floors_tall_building
        or row.flag_area_out_of_range
    ):
        return Confidence.LOW
    if (
        row.flag_low_geocode_precision
        or row.flag_multi_building_parcel
        or row.flag_old_footprint
    ):
        return Confidence.MEDIUM
    return Confidence.HIGH


def _selected_flags(row: EstimateRow) -> list[str]:
    """Read FLAG_PREDICATES and return [FlagKey.value, ...] for the row, stable order."""
    return [k.value for k in FlagKey if FLAG_PREDICATES[k](row)]
