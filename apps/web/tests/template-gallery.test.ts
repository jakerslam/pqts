import { describe, expect, it } from "vitest";

import { listTemplateRunArtifacts } from "@/lib/ops/template-gallery";

describe("template gallery", () => {
  it("returns bounded artifact rows", () => {
    const rows = listTemplateRunArtifacts(undefined, 20);
    expect(rows.length).toBeLessThanOrEqual(20);
    for (const row of rows) {
      expect(row.mode.length).toBeGreaterThan(0);
      expect(row.artifact_path.length).toBeGreaterThan(0);
      expect(Array.isArray(row.command)).toBe(true);
    }
  });
});
