import { NextResponse } from "next/server";

import { PostQaRequestSchema } from "@/lib/api-contract";
import { appendQaReview } from "@/lib/queries";

export async function POST(request: Request) {
  const body = await request.json();
  const parsed = PostQaRequestSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.format() }, { status: 400 });
  }
  const review_id = await appendQaReview(parsed.data);
  return NextResponse.json({
    ok: true,
    review_id,
    written_to: "data/output/qa_reviews.parquet",
  });
}
