import { proxyApi } from "@/lib/api/server-proxy";

export async function GET() {
  return proxyApi("/v1/operator/actions?limit=100");
}
