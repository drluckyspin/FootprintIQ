import type { FlagKey } from "./schema";

export const FLAG_EXPLANATIONS: Record<FlagKey, string> = {
  NO_BUILDING_MATCH: "No building footprint matched this geocoded point.",
  LOW_GEOCODE_PRECISION: "Geocoder precision is below rooftop quality.",
  MULTI_BUILDING_PARCEL: "Multiple buildings sit on the same parcel.",
  OLD_FOOTPRINT: "Overture footprint update time is stale.",
  NEAREST_FALLBACK: "Match used nearest-in-buffer, not point-in-polygon.",
  AREA_OUT_OF_RANGE: "Footprint area is outside expected bounds for this type.",
  HEIGHT_OUTLIER: "Building height is an outlier for the subtype.",
  MISSING_FLOORS_TALL_BUILDING: "Tall building missing reliable floor count.",
  GEOCODE_FAILED: "Geocoding did not return coordinates.",
  SUITE_OR_TENANT_ADDRESS: "Suite or tenant token detected in the address.",
};
