/**
 * Parameterized SQL queries that the Route Handlers use. OWNED BY LANE D.
 *
 * Wave 0 stub.
 */

import "server-only";

import type {
  ListLocationsQuery,
  ListLocationsResponse,
  LocationDetailResponse,
} from "./api-contract";

export async function listLocations(_q: ListLocationsQuery): Promise<ListLocationsResponse> {
  throw new Error("Lane D: implement listLocations");
}

export async function getLocationDetail(
  _locationId: string,
): Promise<LocationDetailResponse | null> {
  throw new Error("Lane D: implement getLocationDetail");
}

export async function appendQaReview(_review: unknown): Promise<string> {
  throw new Error("Lane D: implement appendQaReview (returns review_id)");
}
