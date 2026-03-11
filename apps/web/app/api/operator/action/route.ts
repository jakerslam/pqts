import { NextResponse } from "next/server";

import { proxyApi } from "@/lib/api/server-proxy";

interface Body {
  kind?:
    | "pause_trading"
    | "resume_trading"
    | "canary_promote"
    | "canary_hold"
    | "ack_incident";
  actor?: string;
  note?: string;
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => ({}))) as Body;
  const kind = body.kind;
  const actor = (body.actor ?? "operator").trim();
  const note = (body.note ?? "").trim();

  if (!kind) {
    return NextResponse.json({ error: "kind is required" }, { status: 400 });
  }

  return proxyApi("/v1/operator/actions", {
    method: "POST",
    body: { kind, actor, note },
  });
}
