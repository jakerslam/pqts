import { NextResponse } from "next/server";

import { loadExecutionQualityRows } from "@/lib/ops/reference-data";

export const runtime = "nodejs";

function mean(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((total, value) => total + value, 0) / values.length;
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const limitRaw = Number(url.searchParams.get("limit") ?? "200");
  const limit = Number.isFinite(limitRaw) ? Math.min(Math.max(Math.floor(limitRaw), 1), 2000) : 200;
  const rows = loadExecutionQualityRows(limit);
  const realized = rows.map((row) => row.realized_slippage_bps);
  const predicted = rows.map((row) => row.predicted_slippage_bps);
  const alpha = rows.map((row) => row.realized_net_alpha_usd);
  return NextResponse.json({
    summary: {
      rows: rows.length,
      avg_realized_slippage_bps: mean(realized),
      avg_predicted_slippage_bps: mean(predicted),
      avg_realized_net_alpha_usd: mean(alpha),
      total_realized_net_alpha_usd: alpha.reduce((total, value) => total + value, 0),
    },
    rows,
  });
}
