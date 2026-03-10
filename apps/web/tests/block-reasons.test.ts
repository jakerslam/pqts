import { describe, expect, it } from "vitest";

import { explainBlockReason, listBlockReasonEntries } from "@/lib/ops/block-reasons";

describe("block reasons", () => {
  it("lists deterministic block-reason rows", () => {
    const rows = listBlockReasonEntries();
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.find((row) => row.code === "net_ev_non_positive")).toBeDefined();
  });

  it("returns fallback message for unknown codes", () => {
    const text = explainBlockReason("missing_code");
    expect(text).toContain("Unknown block reason code");
  });
});
