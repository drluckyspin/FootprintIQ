/**
 * POST /api/qa — append a QA review to qa_reviews.parquet. OWNED BY LANE D.
 *
 * Wave 0 stub validates the request body against the contract; returns 501 for actual writes.
 */

import { type NextRequest, NextResponse } from "next/server";

import { PostQaRequestSchema } from "@/lib/api-contract";

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }
  const parsed = PostQaRequestSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.format() }, { status: 400 });
  }
  // Lane D: const reviewId = await appendQaReview(parsed.data);
  return NextResponse.json({ error: "not implemented" }, { status: 501 });
}
