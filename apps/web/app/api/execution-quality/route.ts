import { proxyApi } from "@/lib/api/server-proxy";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const limitRaw = Number(url.searchParams.get("limit") ?? "200");
  const limit = Number.isFinite(limitRaw) ? Math.min(Math.max(Math.floor(limitRaw), 1), 2000) : 200;
  return proxyApi(`/v1/ops/execution-quality?limit=${limit}`);
}
