import { NextResponse } from "next/server";

interface RequestBody {
  message?: string;
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => ({}))) as RequestBody;
  const message = (body.message ?? "").trim();
  if (!message) {
    return NextResponse.json({ error: "message is required" }, { status: 400 });
  }

  // Mock response for local optimistic/reconciliation UX flow.
  const assistantMessage = `Acknowledged. Summary generated for: ${message}`;
  return NextResponse.json({ assistant_message: assistantMessage });
}
