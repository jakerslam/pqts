import { NextResponse } from "next/server";

import { proxyApi } from "@/lib/api/server-proxy";

export const runtime = "nodejs";
type PromotionAction = "advance" | "hold" | "rollback" | "halt";

interface PromotionBody {
  strategy_id?: string;
  action?: PromotionAction;
  actor?: string;
  note?: string;
}

const VALID_ACTIONS = new Set<PromotionAction>(["advance", "hold", "rollback", "halt"]);

export async function GET() {
  return proxyApi("/v1/promotions");
}

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => ({}))) as PromotionBody;
  const action = String(payload.action ?? "").trim() as PromotionAction;
  if (!VALID_ACTIONS.has(action)) {
    return NextResponse.json({ error: "invalid action" }, { status: 400 });
  }
  const strategyId = String(payload.strategy_id ?? "").trim();
  if (!strategyId) {
    return NextResponse.json({ error: "strategy_id is required" }, { status: 400 });
  }
  return proxyApi("/v1/promotions/actions", {
    method: "POST",
    body: {
      strategy_id: strategyId,
      action,
      actor: String(payload.actor ?? "web_operator"),
      note: String(payload.note ?? ""),
    },
  });
}
