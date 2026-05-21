import { NextResponse } from "next/server";

import { ListRunsResponseSchema } from "@/lib/api-contract";
import { listRuns } from "@/lib/queries";

export async function GET() {
  const { runs } = await listRuns();
  const parsed = ListRunsResponseSchema.safeParse({ runs });
  if (!parsed.success) {
    return NextResponse.json({ runs });
  }
  return NextResponse.json(parsed.data);
}
