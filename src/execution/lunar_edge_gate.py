"""LUNR edge decomposition and repricing-lag gate helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class NetEdgeGateInputs:
    model_probability: float
    market_probability: float
    fee_bps: float = 0.0
    spread_bps: float = 0.0
    slippage_bps: float = 0.0
    latency_penalty_bps: float = 0.0
    min_net_edge_bps: float = 0.0
    evidence_ts_ms: int | None = None
    market_ts_ms: int | None = None
    now_ts_ms: int | None = None
    max_repricing_lag_ms: int = 20_000
    max_data_age_ms: int = 15_000
    require_timestamps: bool = True


@dataclass(frozen=True)
class NetEdgeGateDecision:
    gross_edge_bps: float
    total_penalty_bps: float
    net_edge_bps: float
    repricing_lag_ms: int | None
    data_age_ms: int | None
    passed: bool
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_net_edge_gate(inputs: NetEdgeGateInputs) -> NetEdgeGateDecision:
    reason_codes: list[str] = []
    model_probability = float(inputs.model_probability)
    market_probability = float(inputs.market_probability)
    if not 0.0 <= model_probability <= 1.0:
        reason_codes.append("model_probability_out_of_range")
    if not 0.0 <= market_probability <= 1.0:
        reason_codes.append("market_probability_out_of_range")

    model_probability = _clamp_probability(model_probability)
    market_probability = _clamp_probability(market_probability)
    gross_edge_bps = (model_probability - market_probability) * 10_000.0

    total_penalty_bps = sum(
        max(0.0, float(x))
        for x in (
            inputs.fee_bps,
            inputs.spread_bps,
            inputs.slippage_bps,
            inputs.latency_penalty_bps,
        )
    )
    net_edge_bps = gross_edge_bps - total_penalty_bps
    if net_edge_bps < float(inputs.min_net_edge_bps):
        reason_codes.append("net_edge_below_threshold")

    repricing_lag_ms: int | None = None
    data_age_ms: int | None = None
    evidence_ts_ms = inputs.evidence_ts_ms
    market_ts_ms = inputs.market_ts_ms
    now_ts_ms = inputs.now_ts_ms

    if evidence_ts_ms is None or market_ts_ms is None:
        if inputs.require_timestamps:
            reason_codes.append("missing_repricing_timestamps")
    else:
        repricing_lag_ms = abs(int(market_ts_ms) - int(evidence_ts_ms))
        if repricing_lag_ms > int(inputs.max_repricing_lag_ms):
            reason_codes.append("repricing_lag_exceeded")

    if now_ts_ms is not None and market_ts_ms is not None:
        data_age_ms = max(0, int(now_ts_ms) - int(market_ts_ms))
        if data_age_ms > int(inputs.max_data_age_ms):
            reason_codes.append("stale_market_snapshot")
    elif now_ts_ms is not None and inputs.require_timestamps:
        reason_codes.append("missing_market_timestamp_for_age_check")

    return NetEdgeGateDecision(
        gross_edge_bps=float(gross_edge_bps),
        total_penalty_bps=float(total_penalty_bps),
        net_edge_bps=float(net_edge_bps),
        repricing_lag_ms=repricing_lag_ms,
        data_age_ms=data_age_ms,
        passed=not reason_codes,
        reason_codes=tuple(reason_codes),
    )
