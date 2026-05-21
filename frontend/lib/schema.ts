/**
 * FROZEN CONTRACTS — mirror of backend/src/sqft/schema.py.
 *
 * The schema-sync test (backend/tests/test_schema_sync.py) parses this file with
 * a regex looking for `export const <TypeName>Schema = z.object({ ... })`. Keep
 * each schema in that exact shape (one `z.object` literal per export) so the test
 * can extract field names.
 *
 * Any change here MUST be paired with a matching change to schema.py in the same PR.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Enums (mirror sqft.schema.* enums)
// ---------------------------------------------------------------------------

export const GeocoderPrecisionSchema = z.enum([
  "ROOFTOP",
  "RANGE_INTERPOLATED",
  "GEOMETRIC_CENTER",
  "APPROXIMATE",
  "UNKNOWN",
]);
export type GeocoderPrecision = z.infer<typeof GeocoderPrecisionSchema>;

export const GeocoderProviderSchema = z.enum([
  "google_places",
  "google_geocoding",
  "google_address_validation",
  "census",
  "cache",
]);
export type GeocoderProvider = z.infer<typeof GeocoderProviderSchema>;

export const MatchMethodSchema = z.enum([
  "within",
  "nearest_within_buffer",
  "within_parcel",
  "unmatched",
]);
export type MatchMethod = z.infer<typeof MatchMethodSchema>;

export const ConfidenceSchema = z.enum(["high", "medium", "low", "unmatched"]);
export type Confidence = z.infer<typeof ConfidenceSchema>;

export const FloorsSourceSchema = z.enum([
  "overture_num_floors",
  "overture_height",
  "subtype_default",
  "default",
]);
export type FloorsSource = z.infer<typeof FloorsSourceSchema>;

export const FlagKeySchema = z.enum([
  "NO_BUILDING_MATCH",
  "LOW_GEOCODE_PRECISION",
  "MULTI_BUILDING_PARCEL",
  "OLD_FOOTPRINT",
  "NEAREST_FALLBACK",
  "AREA_OUT_OF_RANGE",
  "HEIGHT_OUTLIER",
  "MISSING_FLOORS_TALL_BUILDING",
  "GEOCODE_FAILED",
  "SUITE_OR_TENANT_ADDRESS",
]);
export type FlagKey = z.infer<typeof FlagKeySchema>;

export const LocationTypeSchema = z.enum(["retail", "warehouse", "other"]);
export type LocationType = z.infer<typeof LocationTypeSchema>;

// ---------------------------------------------------------------------------
// Core models — keep the z.object({...}) block grep-friendly for schema sync.
// ---------------------------------------------------------------------------

export const RawAddressSchema = z.object({
  location_id: z.string(),
  address_line_1: z.string(),
  city: z.string(),
  state: z.string().length(2),
  postal_code: z.string(),
  location_type: LocationTypeSchema.default("other"),
});
export type RawAddress = z.infer<typeof RawAddressSchema>;

export const NormalizedAddressSchema = z.object({
  location_id: z.string(),
  address_input: z.string(),
  normalized_line_1: z.string(),
  normalized_city: z.string(),
  normalized_state: z.string(),
  normalized_zip5: z.string(),
  address_key: z.string(),
  chain_token: z.string().nullable().optional(),
  normalize_warnings: z.array(z.string()).default([]),
});
export type NormalizedAddress = z.infer<typeof NormalizedAddressSchema>;

export const GeocodeResultSchema = z.object({
  address_key: z.string(),
  lat: z.number().nullable().optional(),
  lon: z.number().nullable().optional(),
  precision: GeocoderPrecisionSchema.default("UNKNOWN"),
  provider: GeocoderProviderSchema,
  place_id: z.string().nullable().optional(),
  formatted_address: z.string().nullable().optional(),
  raw_response_hash: z.string().nullable().optional(),
  status: z.enum(["ok", "low_precision", "failed", "skipped"]).default("ok"),
  error: z.string().nullable().optional(),
});
export type GeocodeResult = z.infer<typeof GeocodeResultSchema>;

export const FootprintSchema = z.object({
  id: z.string(),
  geometry_wkb: z.instanceof(Uint8Array).or(z.string()), // serialized as base64 over the wire
  bbox_xmin: z.number(),
  bbox_ymin: z.number(),
  bbox_xmax: z.number(),
  bbox_ymax: z.number(),
  height: z.number().nullable().optional(),
  num_floors: z.number().int().nullable().optional(),
  overture_class: z.string().nullable().optional(),
  overture_subtype: z.string().nullable().optional(),
  overture_source: z.string().nullable().optional(),
  overture_version: z.number().int().nullable().optional(),
  overture_update_time: z.coerce.date().nullable().optional(),
});
export type Footprint = z.infer<typeof FootprintSchema>;

export const CandidateBuildingSchema = z.object({
  building_id: z.string(),
  area_sqft: z.number(),
  distance_m: z.number(),
  overture_class: z.string().nullable().optional(),
  overture_subtype: z.string().nullable().optional(),
  is_chosen: z.boolean().default(false),
});
export type CandidateBuilding = z.infer<typeof CandidateBuildingSchema>;

export const BuildingMatchSchema = z.object({
  location_id: z.string(),
  address_key: z.string(),
  chosen_building_id: z.string().nullable().optional(),
  match_method: MatchMethodSchema,
  multi_building_count: z.number().int().default(0),
  candidates: z.array(CandidateBuildingSchema).default([]),
});
export type BuildingMatch = z.infer<typeof BuildingMatchSchema>;

export const EstimateRowSchema = z.object({
  location_id: z.string(),
  address_input: z.string(),
  address_key: z.string(),
  location_type: LocationTypeSchema.default("other"),
  geocoded_lat: z.number().nullable().optional(),
  geocoded_lon: z.number().nullable().optional(),
  geocoder_precision: GeocoderPrecisionSchema.default("UNKNOWN"),
  geocoder_provider: GeocoderProviderSchema.nullable().optional(),
  formatted_address: z.string().nullable().optional(),
  building_id: z.string().nullable().optional(),
  match_method: MatchMethodSchema.default("unmatched"),
  multi_building_count: z.number().int().default(0),
  candidates_json: z.string().default("[]"),
  footprint_area_sqft: z.number().nullable().optional(),
  num_floors_used: z.number().int().nullable().optional(),
  floors_source: FloorsSourceSchema.nullable().optional(),
  raw_overture_height: z.number().nullable().optional(),
  raw_overture_num_floors: z.number().int().nullable().optional(),
  estimated_sqft: z.number().nullable().optional(),
  overture_class: z.string().nullable().optional(),
  overture_subtype: z.string().nullable().optional(),
  overture_source: z.string().nullable().optional(),
  overture_update_time: z.coerce.date().nullable().optional(),
  overture_release: z.string().nullable().optional(),
  confidence: ConfidenceSchema.default("unmatched"),
  flags_json: z.string().default("[]"),
  flag_no_building_match: z.boolean().default(false),
  flag_low_geocode_precision: z.boolean().default(false),
  flag_multi_building_parcel: z.boolean().default(false),
  flag_old_footprint: z.boolean().default(false),
  flag_nearest_fallback: z.boolean().default(false),
  flag_area_out_of_range: z.boolean().default(false),
  flag_height_outlier: z.boolean().default(false),
  flag_missing_floors_tall_building: z.boolean().default(false),
  flag_geocode_failed: z.boolean().default(false),
  flag_suite_or_tenant_address: z.boolean().default(false),
  pipeline_run_id: z.string(),
});
export type EstimateRow = z.infer<typeof EstimateRowSchema>;

export const RunManifestSchema = z.object({
  pipeline_run_id: z.string(),
  started_at_utc: z.coerce.date(),
  finished_at_utc: z.coerce.date().nullable().optional(),
  code_git_sha: z.string().nullable().optional(),
  config_sha256: z.string(),
  input_csv_path: z.string(),
  input_csv_sha256: z.string(),
  input_row_count: z.number().int(),
  overture_release: z.string(),
  geocoder_provider_counts: z.record(z.number().int()).default({}),
  api_cost_usd_estimated: z.number().default(0),
  api_cost_usd_actual: z.number().default(0),
  stage_row_counts: z.record(z.number().int()).default({}),
  stage_durations_seconds: z.record(z.number()).default({}),
  output_estimates_path: z.string(),
  output_estimates_sha256: z.string().nullable().optional(),
  notes: z.array(z.string()).default([]),
});
export type RunManifest = z.infer<typeof RunManifestSchema>;

export const QaReviewSchema = z.object({
  review_id: z.string(),
  reviewed_at_utc: z.coerce.date(),
  location_id: z.string(),
  pipeline_run_id: z.string(),
  reviewer: z.string().nullable().optional(),
  building_selection: z.enum(["correct", "wrong", "ambiguous"]),
  sqft_assessment: z.enum(["low", "right", "high", "unknown"]).default("unknown"),
  actual_sqft: z.number().nullable().optional(),
  notes: z.string().nullable().optional(),
});
export type QaReview = z.infer<typeof QaReviewSchema>;
