import { proxyApi } from "@/lib/api/server-proxy";

export const runtime = "nodejs";

interface SeedBody {
  venue?: "binance" | "coinbase" | "all";
  interval?: string;
  start?: string;
  end?: string;
  format?: "csv" | "parquet";
  cache_mode?: "use" | "refresh";
  max_retries?: number;
  execute?: boolean;
}

export async function GET() {
  return proxyApi("/v1/ops/data-seed/presets");
}

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => ({}))) as SeedBody;
  return proxyApi("/v1/ops/data-seed/run", {
    method: "POST",
    body: {
      venue: payload.venue ?? "all",
      interval: payload.interval ?? "1h",
      start: payload.start ?? "2026-01-01",
      end: payload.end ?? "2026-03-01",
      format: payload.format ?? "csv",
      cache_mode: payload.cache_mode ?? "use",
      max_retries: Number(payload.max_retries ?? 3),
      execute: Boolean(payload.execute),
    },
  });
}
