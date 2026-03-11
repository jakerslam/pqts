import { proxyApi } from "@/lib/api/server-proxy";

export const runtime = "nodejs";

interface NotifyBody {
  channel?: "stdout" | "telegram" | "discord";
  message?: string;
  telegram_token?: string;
  telegram_chat_id?: string;
  discord_webhook?: string;
  execute?: boolean;
}

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => ({}))) as NotifyBody;
  return proxyApi("/v1/ops/notify/test", {
    method: "POST",
    body: {
      channel: payload.channel ?? "stdout",
      message: payload.message ?? "[PQTS TEST] Notifications channel check from web.",
      telegram_token: payload.telegram_token ?? "",
      telegram_chat_id: payload.telegram_chat_id ?? "",
      discord_webhook: payload.discord_webhook ?? "",
      execute: Boolean(payload.execute),
    },
  });
}
