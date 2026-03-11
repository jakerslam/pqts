import { describe, expect, it } from "vitest";

import { buildTrustStatusSnapshot } from "@/lib/system/trust-status";

describe("trust status snapshot", () => {
  it("returns required status fields for global trust bar", () => {
    const snapshot = buildTrustStatusSnapshot();
    expect(snapshot.environment).toMatch(/demo|paper|shadow|canary|live/);
    expect(snapshot.accountId.length).toBeGreaterThan(0);
    expect(snapshot.traceId.startsWith("trc_")).toBe(true);
    expect(snapshot.runId.startsWith("run_")).toBe(true);
    expect(snapshot.nativeHotpath).toMatch(/native|fallback/);
    expect(snapshot.trustLabel).toMatch(/reference|diagnostic_only|unverified/);
  });
});

