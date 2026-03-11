import { webEnv } from "@/lib/env";
import type { AccountSummary, Fill, Order, Position, RiskState } from "@/lib/api/types";

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${webEnv.NEXT_PUBLIC_API_BASE_URL}${path}`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${webEnv.NEXT_PUBLIC_API_TOKEN}`,
      Accept: "application/json",
    },
  });
  if (!response.ok) {
    throw new Error(`API request failed (${response.status}): ${path}`);
  }
  return (await response.json()) as T;
}

interface AccountEnvelope {
  account: {
    account_id: string;
    equity: number;
    cash: number;
    buying_power: number;
  };
}

interface PositionEnvelope {
  positions: Array<{
    symbol: string;
    quantity: number;
    avg_price: number;
    mark_price: number;
    unrealized_pnl: number;
  }>;
}

interface OrderEnvelope {
  orders: Array<{
    order_id: string;
    symbol: string;
    side: "buy" | "sell";
    quantity: number;
    status: string;
    submitted_at: string;
  }>;
}

interface FillEnvelope {
  fills: Array<{
    fill_id: string;
    order_id: string;
    symbol: string;
    quantity: number;
    price: number;
    executed_at: string;
  }>;
}

interface RiskEnvelope {
  risk_state: {
    kill_switch_active: boolean;
    reasons: string[];
    current_drawdown: number;
    metadata?: Record<string, unknown>;
  };
}

export async function getAccountSummary(): Promise<AccountSummary> {
  const payload = await apiGet<AccountEnvelope>(`/v1/accounts/${webEnv.NEXT_PUBLIC_ACCOUNT_ID}`);
  return payload.account;
}

export async function getPositions(): Promise<Position[]> {
  const payload = await apiGet<PositionEnvelope>(
    `/v1/portfolio/positions?account_id=${encodeURIComponent(webEnv.NEXT_PUBLIC_ACCOUNT_ID)}`,
  );
  return payload.positions.map((row) => ({
    symbol: row.symbol,
    qty: Number(row.quantity),
    avg_price: Number(row.avg_price),
    market_price: Number(row.mark_price),
    unrealized_pnl: Number(row.unrealized_pnl),
  }));
}

export async function getOrders(): Promise<Order[]> {
  const payload = await apiGet<OrderEnvelope>(
    `/v1/execution/orders?account_id=${encodeURIComponent(webEnv.NEXT_PUBLIC_ACCOUNT_ID)}`,
  );
  return payload.orders.map((row) => ({
    order_id: row.order_id,
    symbol: row.symbol,
    side: row.side,
    quantity: Number(row.quantity),
    status: row.status,
    created_at: row.submitted_at,
  }));
}

export async function getFills(): Promise<Fill[]> {
  const payload = await apiGet<FillEnvelope>(
    `/v1/execution/fills?account_id=${encodeURIComponent(webEnv.NEXT_PUBLIC_ACCOUNT_ID)}`,
  );
  return payload.fills.map((row) => ({
    fill_id: row.fill_id,
    order_id: row.order_id,
    symbol: row.symbol,
    quantity: Number(row.quantity),
    price: Number(row.price),
    timestamp: row.executed_at,
  }));
}

export async function getRiskState(): Promise<RiskState> {
  const payload = await apiGet<RiskEnvelope>(`/v1/risk/state/${webEnv.NEXT_PUBLIC_ACCOUNT_ID}`);
  return {
    kill_switch_active: Boolean(payload.risk_state.kill_switch_active),
    kill_switch_reason: String(payload.risk_state.reasons?.[0] ?? ""),
    current_drawdown: Number(payload.risk_state.current_drawdown),
    daily_pnl: Number(payload.risk_state.metadata?.daily_pnl ?? 0),
  };
}
