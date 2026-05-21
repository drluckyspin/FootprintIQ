/**
 * GET /api/locations — list, filter, paginate. OWNED BY LANE D.
 *
 * Wave 0 stub returns an empty list so the frontend renders without crashing.
 */

import { type NextRequest, NextResponse } from "next/server";

import { ListLocationsQuerySchema } from "@/lib/api-contract";

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const parsed = ListLocationsQuerySchema.safeParse(Object.fromEntries(url.searchParams));
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.format() }, { status: 400 });
  }
  // Lane D: const result = await listLocations(parsed.data);
  return NextResponse.json({ rows: [], total: 0 });
}
