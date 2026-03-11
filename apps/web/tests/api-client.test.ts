import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getAccountSummary,
  getFills,
  getOrders,
  getPositions,
  getRiskState,
} from "@/lib/api/client";

function mockJsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

describe("api client contract mapping", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("maps account envelope from /v1/accounts/{account_id}", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      mockJsonResponse({
        account: {
          account_id: "paper-main",
          equity: 101000,
          cash: 100500,
          buying_power: 301500,
        },
      }),
    );

    const account = await getAccountSummary();
    expect(account.account_id).toBe("paper-main");
    expect(account.equity).toBe(101000);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/v1/accounts/paper-main",
      expect.objectContaining({
        cache: "no-store",
        headers: expect.objectContaining({
          Authorization: "Bearer pqts-dev-viewer-token",
        }),
      }),
    );
  });

  it("maps positions envelope into ui position model", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      mockJsonResponse({
        positions: [
          {
            symbol: "BTC-USD",
            quantity: 0.75,
            avg_price: 50000,
            mark_price: 51000,
            unrealized_pnl: 750,
          },
        ],
      }),
    );
    const positions = await getPositions();
    expect(positions).toEqual([
      {
        symbol: "BTC-USD",
        qty: 0.75,
        avg_price: 50000,
        market_price: 51000,
        unrealized_pnl: 750,
      },
    ]);
  });

  it("maps orders and fills from execution endpoints", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        mockJsonResponse({
          orders: [
            {
              order_id: "o1",
              symbol: "BTC-USD",
              side: "buy",
              quantity: 0.2,
              status: "filled",
              submitted_at: "2026-03-10T00:00:00Z",
            },
          ],
        }),
      )
      .mockResolvedValueOnce(
        mockJsonResponse({
          fills: [
            {
              fill_id: "f1",
              order_id: "o1",
              symbol: "BTC-USD",
              quantity: 0.2,
              price: 50200,
              executed_at: "2026-03-10T00:00:02Z",
            },
          ],
        }),
      );

    const orders = await getOrders();
    const fills = await getFills();
    expect(orders[0]?.created_at).toBe("2026-03-10T00:00:00Z");
    expect(fills[0]?.timestamp).toBe("2026-03-10T00:00:02Z");
  });

  it("maps risk state envelope and daily pnl metadata", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      mockJsonResponse({
        risk_state: {
          kill_switch_active: false,
          reasons: ["none"],
          current_drawdown: 0.021,
          metadata: {
            daily_pnl: 152.33,
          },
        },
      }),
    );

    const risk = await getRiskState();
    expect(risk.kill_switch_reason).toBe("none");
    expect(risk.current_drawdown).toBeCloseTo(0.021);
    expect(risk.daily_pnl).toBeCloseTo(152.33);
  });
});
