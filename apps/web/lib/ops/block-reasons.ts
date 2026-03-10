export interface BlockReasonEntry {
  code: string;
  explanation: string;
}

const BLOCK_REASON_GUIDE: Record<string, string> = {
  not_underdog: "Signal was rejected because market-implied probability is not in underdog range.",
  insufficient_depth: "Signal blocked because orderbook depth is below configured minimum.",
  liquidity_gate: "Signal blocked by liquidity policy; market quality is not sufficient.",
  capacity_gate: "Signal blocked by capacity limits to avoid over-allocation.",
  edge_below_threshold: "Model edge did not exceed minimum threshold after calibration.",
  net_ev_non_positive: "Expected value after cost assumptions is non-positive.",
  rolling_edge_disable: "Strategy auto-disabled because rolling realized edge degraded below floor.",
  orders_per_minute_exceeded: "High-frequency guardrail blocked flow due to order-rate breach.",
  p95_submit_to_ack_slo_breach: "Execution latency exceeded configured p95 budget.",
  p99_submit_to_ack_slo_breach: "Execution latency exceeded configured p99 budget.",
  public_admin_ingress_disallowed: "Security gate requires private control-plane access only.",
};

export function listBlockReasonEntries(): BlockReasonEntry[] {
  return Object.entries(BLOCK_REASON_GUIDE)
    .map(([code, explanation]) => ({ code, explanation }))
    .sort((left, right) => left.code.localeCompare(right.code));
}

export function explainBlockReason(code: string): string {
  const key = String(code).trim();
  return (
    BLOCK_REASON_GUIDE[key] ||
    "Unknown block reason code. Inspect readiness report and router telemetry for exact gate payload and threshold."
  );
}
