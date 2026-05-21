/**
 * GET /api/locations/[id] — full detail with geocode + chosen building + candidates.
 * OWNED BY LANE D.
 *
 * Wave 0 stub returns 501.
 */

import { type NextRequest, NextResponse } from "next/server";

export async function GET(_request: NextRequest, { params }: { params: { id: string } }) {
  // Lane D: const detail = await getLocationDetail(params.id);
  return NextResponse.json({ error: "not implemented", location_id: params.id }, { status: 501 });
}
