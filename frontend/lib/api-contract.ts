/**
 * JSON API contracts between the Next.js frontend (server + client) and itself.
 * Lane D OWNS this file; Lane C may read it.
 */

import { z } from "zod";
import {
  CandidateBuildingSchema,
  ConfidenceSchema,
  EstimateRowSchema,
  FlagKeySchema,
  GeocodeResultSchema,
  LocationTypeSchema,
  QaReviewSchema,
  RunManifestSchema,
} from "./schema";

// --- /api/locations ----------------------------------------------------------

export const ListLocationsQuerySchema = z.object({
  search: z.string().optional(),
  confidence: z.array(ConfidenceSchema).optional(),
  location_type: z.array(LocationTypeSchema).optional(),
  state: z.array(z.string().length(2)).optional(),
  flag: z.array(FlagKeySchema).optional(),
  limit: z.coerce.number().int().min(1).max(1000).default(100),
  offset: z.coerce.number().int().min(0).default(0),
});
export type ListLocationsQuery = z.infer<typeof ListLocationsQuerySchema>;

export const ListLocationsResponseSchema = z.object({
  rows: z.array(EstimateRowSchema),
  total: z.number().int(),
});
export type ListLocationsResponse = z.infer<typeof ListLocationsResponseSchema>;

// --- /api/locations/[id] -----------------------------------------------------

/** GeoJSON geometry. Lane D may swap to a stricter type later. */
const GeoJSONGeometrySchema = z.object({
  type: z.string(),
  coordinates: z.unknown(),
});

export const FlagDetailSchema = z.object({
  key: FlagKeySchema,
  explanation: z.string(),
});
export type FlagDetail = z.infer<typeof FlagDetailSchema>;

export const LocationDetailResponseSchema = z.object({
  row: EstimateRowSchema,
  geocode: GeocodeResultSchema.nullable(),
  chosen_building: z
    .object({
      id: z.string(),
      geometry: GeoJSONGeometrySchema,
      area_sqft: z.number(),
      overture_class: z.string().nullable().optional(),
      overture_subtype: z.string().nullable().optional(),
    })
    .nullable(),
  candidates: z.array(
    CandidateBuildingSchema.extend({ geometry: GeoJSONGeometrySchema.optional() }),
  ),
  parcel: GeoJSONGeometrySchema.nullable(),
  flags: z.array(FlagDetailSchema),
  manifest_url: z.string(),
});
export type LocationDetailResponse = z.infer<typeof LocationDetailResponseSchema>;

// --- /api/qa -----------------------------------------------------------------

export const PostQaRequestSchema = QaReviewSchema.omit({
  review_id: true,
  reviewed_at_utc: true,
});
export type PostQaRequest = z.infer<typeof PostQaRequestSchema>;

export const PostQaResponseSchema = z.object({
  ok: z.literal(true),
  written_to: z.string(),
  review_id: z.string(),
});
export type PostQaResponse = z.infer<typeof PostQaResponseSchema>;

// --- /api/runs ---------------------------------------------------------------

export const ListRunsResponseSchema = z.object({
  runs: z.array(RunManifestSchema),
});
export type ListRunsResponse = z.infer<typeof ListRunsResponseSchema>;
