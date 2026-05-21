import { NextResponse } from "next/server";

import { getLocationDetail } from "@/lib/queries";

export async function GET(
  _request: Request,
  context: { params: { id: string } },
) {
  const detail = await getLocationDetail(context.params.id);
  if (!detail) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }
  return NextResponse.json(detail);
}
