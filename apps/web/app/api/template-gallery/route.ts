import { NextResponse } from "next/server";

import { listTemplateRunArtifacts } from "@/lib/ops/template-gallery";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const mode = (url.searchParams.get("mode") ?? "").trim() || undefined;
  const limitRaw = Number(url.searchParams.get("limit") ?? "40");
  const limit = Number.isFinite(limitRaw) ? Math.min(Math.max(Math.floor(limitRaw), 1), 200) : 40;
  const artifacts = listTemplateRunArtifacts(mode, limit);
  return NextResponse.json({
    count: artifacts.length,
    artifacts,
  });
}
