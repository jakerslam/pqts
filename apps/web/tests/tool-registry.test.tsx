import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { getRegisteredToolTypes, renderToolEvent } from "../lib/tools/registry";

describe("tool renderer registry", () => {
  it("contains expected core renderer keys", () => {
    const keys = getRegisteredToolTypes();
    expect(keys).toContain("account_summary");
    expect(keys).toContain("orders_tape");
    expect(keys).toContain("risk_state");
  });

  it("falls back for unknown tool type", () => {
    render(
      renderToolEvent({
        toolType: "unknown_type",
        status: "complete",
        payload: { foo: "bar" },
      }),
    );

    expect(screen.getByText("Unsupported tool type")).toBeInTheDocument();
    expect(screen.getByText("Type: unknown_type")).toBeInTheDocument();
  });
});
