import { proxyApi } from "@/lib/api/server-proxy";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const mode = (url.searchParams.get("mode") ?? "").trim() || undefined;
  const limitRaw = Number(url.searchParams.get("limit") ?? "40");
  const limit = Number.isFinite(limitRaw) ? Math.min(Math.max(Math.floor(limitRaw), 1), 200) : 40;
  const qs = new URLSearchParams({ limit: String(limit) });
  if (mode) {
    qs.set("mode", mode);
  }
  return proxyApi(`/v1/ops/template-gallery?${qs.toString()}`);
}
