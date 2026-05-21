"""
FROZEN CONTRACTS — single source of truth for every Wave 1 lane.

Any change to this file after Wave 0 requires orchestrator approval.
Mirror changes must be made to frontend/lib/schema.ts in the same PR;
the schema-sync test (tests/test_schema_sync.py) will fail otherwise.

Type families
-------------
- RawAddress          : input CSV row                        (Lane A consumes)
- NormalizedAddress   : after normalize+dedup                (Lane A produces, Lane A/C consume)
- GeocodeResult       : after geocoding                      (Lane A produces, Lane B/C consume)
- Footprint           : Overture building row                (Lane B produces, Lane B/C consume)
- BuildingMatch       : spatial join output                  (Lane B produces, Lane C consumes)
- EstimateRow         : final per-location output row        (Lane C produces, Lane D consumes)
- RunManifest         : reproducibility sidecar              (Lane C produces, Lane D consumes)
- QaReview            : human QA verdict                     (Lane D produces, Lane C consumes)
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class GeocoderPrecision(StrEnum):
    """Normalized precision label across providers."""

    ROOFTOP = "ROOFTOP"
    RANGE_INTERPOLATED = "RANGE_INTERPOLATED"
    GEOMETRIC_CENTER = "GEOMETRIC_CENTER"
    APPROXIMATE = "APPROXIMATE"
    UNKNOWN = "UNKNOWN"


class GeocoderProvider(StrEnum):
    GOOGLE_PLACES = "google_places"
    GOOGLE_GEOCODING = "google_geocoding"
    GOOGLE_ADDRESS_VALIDATION = "google_address_validation"
    CENSUS = "census"
    CACHE = "cache"


class MatchMethod(StrEnum):
    WITHIN = "within"
    NEAREST_WITHIN_BUFFER = "nearest_within_buffer"
    WITHIN_PARCEL = "within_parcel"
    UNMATCHED = "unmatched"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNMATCHED = "unmatched"


class FloorsSource(StrEnum):
    OVERTURE_NUM_FLOORS = "overture_num_floors"
    OVERTURE_HEIGHT = "overture_height"
    SUBTYPE_DEFAULT = "subtype_default"
    DEFAULT = "default"


class FlagKey(StrEnum):
    """All flag keys. Each becomes a boolean column on EstimateRow AND an entry in flags_json."""

    NO_BUILDING_MATCH = "NO_BUILDING_MATCH"
    LOW_GEOCODE_PRECISION = "LOW_GEOCODE_PRECISION"
    MULTI_BUILDING_PARCEL = "MULTI_BUILDING_PARCEL"
    OLD_FOOTPRINT = "OLD_FOOTPRINT"
    NEAREST_FALLBACK = "NEAREST_FALLBACK"
    AREA_OUT_OF_RANGE = "AREA_OUT_OF_RANGE"
    HEIGHT_OUTLIER = "HEIGHT_OUTLIER"
    MISSING_FLOORS_TALL_BUILDING = "MISSING_FLOORS_TALL_BUILDING"
    GEOCODE_FAILED = "GEOCODE_FAILED"
    SUITE_OR_TENANT_ADDRESS = "SUITE_OR_TENANT_ADDRESS"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


class RawAddress(BaseModel):
    """One row of the input CSV. Schema enforced by io.read_input_csv."""

    model_config = ConfigDict(extra="forbid")

    location_id: str
    address_line_1: str
    city: str
    state: str = Field(..., min_length=2, max_length=2, description="USPS two-letter state code")
    postal_code: str
    location_type: Literal["retail", "warehouse", "other"] = "other"


class NormalizedAddress(BaseModel):
    """Output of normalize+dedup. `address_key` is the dedup key used by geocoder cache."""

    model_config = ConfigDict(extra="forbid")

    location_id: str
    address_input: str  # original concatenated input, for traceability
    normalized_line_1: str
    normalized_city: str
    normalized_state: str
    normalized_zip5: str
    address_key: str  # canonical key, hashed-friendly; e.g. "123 main st|austin|tx|78701"
    chain_token: str | None = None  # e.g. "walmart" if detected, drives provider routing
    normalize_warnings: list[str] = Field(default_factory=list)


class GeocodeResult(BaseModel):
    """Output of geocode stage. One row per address_key (after dedup)."""

    model_config = ConfigDict(extra="forbid")

    address_key: str
    lat: float | None = None
    lon: float | None = None
    precision: GeocoderPrecision = GeocoderPrecision.UNKNOWN
    provider: GeocoderProvider
    place_id: str | None = None
    formatted_address: str | None = None
    raw_response_hash: str | None = None  # sha256 of full provider JSON in cache
    status: Literal["ok", "low_precision", "failed", "skipped"] = "ok"
    error: str | None = None


class Footprint(BaseModel):
    """One Overture building row, as written to footprints.parquet.

    `geometry` is stored as WKB bytes in parquet; here it's just a marker field.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    id: str  # Overture GERS ID
    geometry_wkb: bytes  # WKB-encoded polygon, EPSG:4326
    bbox_xmin: float
    bbox_ymin: float
    bbox_xmax: float
    bbox_ymax: float
    height: float | None = None  # meters
    num_floors: int | None = None
    overture_class: str | None = None
    overture_subtype: str | None = None
    overture_source: str | None = None  # e.g. "OSM", "Microsoft", "Google Open Buildings"
    overture_version: int | None = None
    overture_update_time: datetime | None = None


class CandidateBuilding(BaseModel):
    """One candidate building considered for a location. Serialized into EstimateRow.candidates_json."""

    model_config = ConfigDict(extra="forbid")

    building_id: str
    area_sqft: float
    distance_m: float  # 0 if point lies within polygon
    overture_class: str | None = None
    overture_subtype: str | None = None
    is_chosen: bool = False


class BuildingMatch(BaseModel):
    """Intermediate output of spatial_join, before floors/area enrichment."""

    model_config = ConfigDict(extra="forbid")

    location_id: str
    address_key: str
    chosen_building_id: str | None = None
    match_method: MatchMethod
    multi_building_count: int = 0
    candidates: list[CandidateBuilding] = Field(default_factory=list)


class EstimateRow(BaseModel):
    """Final per-location output. This is the parquet schema for estimates.parquet."""

    model_config = ConfigDict(extra="forbid")

    # Identity
    location_id: str
    address_input: str
    address_key: str
    location_type: Literal["retail", "warehouse", "other"] = "other"

    # Geocode
    geocoded_lat: float | None = None
    geocoded_lon: float | None = None
    geocoder_precision: GeocoderPrecision = GeocoderPrecision.UNKNOWN
    geocoder_provider: GeocoderProvider | None = None
    formatted_address: str | None = None

    # Building match
    building_id: str | None = None
    match_method: MatchMethod = MatchMethod.UNMATCHED
    multi_building_count: int = 0
    candidates_json: str = "[]"  # JSON-encoded list[CandidateBuilding]

    # Geometry / area
    footprint_area_sqft: float | None = None

    # Floors
    num_floors_used: int | None = None
    floors_source: FloorsSource | None = None
    raw_overture_height: float | None = None
    raw_overture_num_floors: int | None = None

    # Estimate
    estimated_sqft: float | None = None

    # Overture metadata (mirrors fields from Footprint when matched)
    overture_class: str | None = None
    overture_subtype: str | None = None
    overture_source: str | None = None
    overture_update_time: datetime | None = None
    overture_release: str | None = None  # release string used for this run

    # Confidence + flags
    confidence: Confidence = Confidence.UNMATCHED
    flags_json: str = "[]"  # JSON-encoded list[str], stable ordering
    # Boolean columns — one per FlagKey, defaulting to False.
    flag_no_building_match: bool = False
    flag_low_geocode_precision: bool = False
    flag_multi_building_parcel: bool = False
    flag_old_footprint: bool = False
    flag_nearest_fallback: bool = False
    flag_area_out_of_range: bool = False
    flag_height_outlier: bool = False
    flag_missing_floors_tall_building: bool = False
    flag_geocode_failed: bool = False
    flag_suite_or_tenant_address: bool = False

    # Lineage
    pipeline_run_id: str


class RunManifest(BaseModel):
    """Sidecar JSON written by manifest.py for every pipeline run."""

    model_config = ConfigDict(extra="forbid")

    pipeline_run_id: str
    started_at_utc: datetime
    finished_at_utc: datetime | None = None
    code_git_sha: str | None = None
    config_sha256: str
    input_csv_path: str
    input_csv_sha256: str
    input_row_count: int

    overture_release: str
    geocoder_provider_counts: dict[str, int] = Field(default_factory=dict)
    api_cost_usd_estimated: float = 0.0
    api_cost_usd_actual: float = 0.0

    stage_row_counts: dict[str, int] = Field(default_factory=dict)
    stage_durations_seconds: dict[str, float] = Field(default_factory=dict)

    output_estimates_path: str
    output_estimates_sha256: str | None = None

    notes: list[str] = Field(default_factory=list)


class QaReview(BaseModel):
    """Human QA verdict, written by frontend POST /api/qa. Append-only to qa_reviews.parquet."""

    model_config = ConfigDict(extra="forbid")

    review_id: str  # uuid4
    reviewed_at_utc: datetime
    location_id: str
    pipeline_run_id: str
    reviewer: str | None = None

    building_selection: Literal["correct", "wrong", "ambiguous"]
    sqft_assessment: Literal["low", "right", "high", "unknown"] = "unknown"
    actual_sqft: float | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Parquet column name constants (the actual column ordering on disk).
# Lane A/B/C MUST use these constants when writing parquet.
# ---------------------------------------------------------------------------

NORMALIZED_COLS: tuple[str, ...] = tuple(NormalizedAddress.model_fields.keys())
GEOCODED_COLS: tuple[str, ...] = tuple(GeocodeResult.model_fields.keys())
FOOTPRINTS_COLS: tuple[str, ...] = tuple(Footprint.model_fields.keys())
ESTIMATES_COLS: tuple[str, ...] = tuple(EstimateRow.model_fields.keys())
QA_REVIEWS_COLS: tuple[str, ...] = tuple(QaReview.model_fields.keys())


__all__ = [
    "BuildingMatch",
    "CandidateBuilding",
    "Confidence",
    "ESTIMATES_COLS",
    "EstimateRow",
    "FOOTPRINTS_COLS",
    "FlagKey",
    "FloorsSource",
    "Footprint",
    "GEOCODED_COLS",
    "GeocodeResult",
    "GeocoderPrecision",
    "GeocoderProvider",
    "MatchMethod",
    "NORMALIZED_COLS",
    "NormalizedAddress",
    "QA_REVIEWS_COLS",
    "QaReview",
    "RawAddress",
    "RunManifest",
]


# Pydantic v2 quietness:
_ = (BaseModel, Field, ConfigDict, Any)  # keep imports if unused locally
