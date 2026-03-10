import { NextResponse } from "next/server";

import { loadReplayEvents, replayHash } from "@/lib/ops/reference-data";

export const runtime = "nodejs";

function summarizeEventTypes(events: Array<Record<string, unknown>>): Array<{ event_type: string; count: number }> {
  const counter = new Map<string, number>();
  for (const event of events) {
    const key = String(event.event_type ?? "unknown").trim() || "unknown";
    counter.set(key, (counter.get(key) ?? 0) + 1);
  }
  return [...counter.entries()]
    .map(([event_type, count]) => ({ event_type, count }))
    .sort((left, right) => right.count - left.count || left.event_type.localeCompare(right.event_type));
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const limitRaw = Number(url.searchParams.get("limit") ?? "120");
  const limit = Number.isFinite(limitRaw) ? Math.min(Math.max(Math.floor(limitRaw), 1), 1000) : 120;
  const events = loadReplayEvents(limit);
  return NextResponse.json({
    hash: replayHash(events),
    count: events.length,
    event_types: summarizeEventTypes(events),
    events,
  });
}
