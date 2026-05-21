import { type NextRequest, NextResponse } from "next/server";

import { ListLocationsQuerySchema } from "@/lib/api-contract";
import { listLocations } from "@/lib/queries";

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const raw: Record<string, string | string[]> = {};
  for (const [key, value] of url.searchParams.entries()) {
    if (raw[key]) {
      const prev = raw[key];
      raw[key] = Array.isArray(prev) ? [...prev, value] : [prev, value];
    } else {
      raw[key] = value;
    }
  }
  const parsed = ListLocationsQuerySchema.safeParse(raw);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.format() }, { status: 400 });
  }
  const result = await listLocations(parsed.data);
  return NextResponse.json(result);
}
