/**
 * GET /api/runs — list known pipeline run manifests. OWNED BY LANE D.
 *
 * Wave 0 stub returns empty list.
 */

import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ runs: [] });
}
