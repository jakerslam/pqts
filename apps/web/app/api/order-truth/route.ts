import { proxyApi } from "@/lib/api/server-proxy";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const orderId = url.searchParams.get("order_id") ?? "";
  const qs = new URLSearchParams();
  if (orderId) {
    qs.set("order_id", orderId);
  }
  const suffix = qs.toString();
  return proxyApi(suffix ? `/v1/ops/order-truth?${suffix}` : "/v1/ops/order-truth");
}
