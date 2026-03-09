import { describe, expect, it } from "vitest";

import {
  applyAssistantStreamEvent,
  createAssistantTurnState,
  reduceAssistantStream,
} from "../lib/stream/orchestrator";

describe("stream orchestrator", () => {
  it("applies token and tool lifecycle events deterministically", () => {
    const events = [
      { eventId: "1", kind: "token", value: "hello " } as const,
      {
        eventId: "2",
        kind: "tool_started",
        toolType: "risk_state",
        toolCallId: "call_1",
      } as const,
      {
        eventId: "3",
        kind: "tool_completed",
        toolCallId: "call_1",
        payload: { kill_switch_active: false },
      } as const,
      { eventId: "4", kind: "token", value: "world" } as const,
      { eventId: "5", kind: "turn_completed" } as const,
    ];

    const state = reduceAssistantStream("t1", events);
    expect(state.text).toBe("hello world");
    expect(state.isComplete).toBe(true);
    expect(state.orderedToolCallIds).toEqual(["call_1"]);
    expect(state.toolEvents.call_1.status).toBe("complete");
  });

  it("ignores duplicate event ids", () => {
    const start = createAssistantTurnState("t2");
    const first = applyAssistantStreamEvent(start, {
      eventId: "dup",
      kind: "token",
      value: "abc",
    });
    const second = applyAssistantStreamEvent(first, {
      eventId: "dup",
      kind: "token",
      value: "xyz",
    });

    expect(second.text).toBe("abc");
    expect(second.processedEventIds).toEqual(["dup"]);
  });
});
