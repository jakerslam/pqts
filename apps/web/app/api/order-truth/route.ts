import { NextResponse } from "next/server";

import { buildOrderTruth } from "@/lib/ops/reference-data";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const orderId = url.searchParams.get("order_id") ?? "";
  const payload = buildOrderTruth(orderId);
  return NextResponse.json({
    selected: payload.selected,
    explanation: payload.explanation,
    rows: payload.rows.slice(0, 100),
  });
}
