import { describe, expect, it } from "vitest";

import { loadReferenceProvenance } from "@/lib/ops/reference-data";

describe("reference provenance", () => {
  it("returns trust label with provenance metadata fields", () => {
    const provenance = loadReferenceProvenance();
    expect(provenance.trust_label).toMatch(/reference|diagnostic_only|unverified/);
    expect(typeof provenance.generated_at).toBe("string");
    expect(typeof provenance.bundle).toBe("string");
    expect(typeof provenance.report_path).toBe("string");
  });
});

