import { webEnv } from "@/lib/env";
import type { AccountSummary, Fill, Order, Position, RiskState } from "@/lib/api/types";

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${webEnv.NEXT_PUBLIC_API_BASE_URL}${path}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`API request failed (${response.status}): ${path}`);
  }
  return (await response.json()) as T;
}

export async function getAccountSummary(): Promise<AccountSummary> {
  return apiGet<AccountSummary>("/api/v1/account");
}

export async function getPositions(): Promise<Position[]> {
  return apiGet<Position[]>("/api/v1/positions");
}

export async function getOrders(): Promise<Order[]> {
  return apiGet<Order[]>("/api/v1/orders");
}

export async function getFills(): Promise<Fill[]> {
  return apiGet<Fill[]>("/api/v1/fills");
}

export async function getRiskState(): Promise<RiskState> {
  return apiGet<RiskState>("/api/v1/risk");
}
