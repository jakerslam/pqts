"""LMSR liquidity sensitivity and thin-pool impact guardrails."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


_STAGES = {"paper", "canary", "live"}


@dataclass(frozen=True)
class LMSRImpactScenario:
    size_label: str
    order_size: float
    projected_probability_shift: float
    projected_slippage_bps: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "size_label": self.size_label,
            "order_size": float(self.order_size),
            "projected_probability_shift": float(self.projected_probability_shift),
            "projected_slippage_bps": float(self.projected_slippage_bps),
        }


@dataclass(frozen=True)
class LMSRSensitivityReport:
    market_id: str
    liquidity_b: float
    base_probability_yes: float
    local_price_impact_per_unit: float
    scenarios: tuple[LMSRImpactScenario, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "market_id": self.market_id,
            "liquidity_b": float(self.liquidity_b),
            "base_probability_yes": float(self.base_probability_yes),
            "local_price_impact_per_unit": float(self.local_price_impact_per_unit),
            "scenarios": [row.as_dict() for row in self.scenarios],
        }


@dataclass(frozen=True)
class LMSREligibilityDecision:
    allow_trade: bool
    stage: str
    max_projected_shift: float
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "allow_trade": bool(self.allow_trade),
            "stage": self.stage,
            "max_projected_shift": float(self.max_projected_shift),
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class DepthRegimeDecision:
    regime: str
    tightened_size_cap: float
    tightened_repricing_limit: int
    tightened_min_net_edge_bps: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "regime": self.regime,
            "tightened_size_cap": float(self.tightened_size_cap),
            "tightened_repricing_limit": int(self.tightened_repricing_limit),
            "tightened_min_net_edge_bps": float(self.tightened_min_net_edge_bps),
        }


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _lmsr_probability_yes(q_yes: float, q_no: float, b: float) -> float:
    if b <= 0.0:
        raise ValueError("liquidity parameter b must be > 0")
    return _sigmoid((float(q_yes) - float(q_no)) / float(b))


def build_lmsr_sensitivity_report(
    *,
    market_id: str,
    liquidity_b: float,
    q_yes: float,
    q_no: float,
    scenario_sizes: dict[str, float],
) -> LMSRSensitivityReport:
    """Compute local LMSR price impact and scenario shifts/slippage."""

    b = float(liquidity_b)
    if b <= 0.0:
        raise ValueError("liquidity_b must be > 0")
    base = _lmsr_probability_yes(float(q_yes), float(q_no), b)
    local_impact = (base * (1.0 - base)) / b

    scenarios: list[LMSRImpactScenario] = []
    for label, size in scenario_sizes.items():
        order = float(size)
        post = _lmsr_probability_yes(float(q_yes) + order, float(q_no), b)
        shift = abs(post - base)
        slippage_bps = shift * 10_000.0
        scenarios.append(
            LMSRImpactScenario(
                size_label=str(label),
                order_size=order,
                projected_probability_shift=shift,
                projected_slippage_bps=slippage_bps,
            )
        )
    return LMSRSensitivityReport(
        market_id=str(market_id).strip(),
        liquidity_b=b,
        base_probability_yes=base,
        local_price_impact_per_unit=local_impact,
        scenarios=tuple(scenarios),
    )


def evaluate_lmsr_execution_eligibility(
    *,
    stage: str,
    report: LMSRSensitivityReport,
    impact_thresholds_by_stage: dict[str, float],
) -> LMSREligibilityDecision:
    """Fail closed when projected impact exceeds stage threshold."""

    token = str(stage).strip().lower()
    if token not in _STAGES:
        raise ValueError(f"unsupported stage: {stage}")
    threshold = float(impact_thresholds_by_stage[token])
    max_shift = max((row.projected_probability_shift for row in report.scenarios), default=0.0)
    reasons: list[str] = []
    if max_shift > threshold:
        reasons.append("projected_lmsr_impact_exceeds_stage_threshold")
    return LMSREligibilityDecision(
        allow_trade=not bool(reasons),
        stage=token,
        max_projected_shift=max_shift,
        reason_codes=tuple(sorted(set(reasons))),
    )


def classify_depth_regime_and_tighten_guards(
    *,
    realized_slippage_bps: float,
    projected_slippage_bps: float,
    depth_score: float,
    base_size_cap: float,
    base_repricing_limit: int,
    base_min_net_edge_bps: float,
) -> DepthRegimeDecision:
    """Classify depth regime and tighten pre-trade guardrails for thin pools."""

    ratio = float(realized_slippage_bps) / max(float(projected_slippage_bps), 1e-9)
    score = float(depth_score)
    if score < 0.35 or ratio > 1.5:
        return DepthRegimeDecision(
            regime="thin",
            tightened_size_cap=float(base_size_cap) * 0.35,
            tightened_repricing_limit=max(int(base_repricing_limit * 0.5), 1),
            tightened_min_net_edge_bps=float(base_min_net_edge_bps) * 1.8,
        )
    if score < 0.70 or ratio > 1.15:
        return DepthRegimeDecision(
            regime="normal",
            tightened_size_cap=float(base_size_cap) * 0.70,
            tightened_repricing_limit=max(int(base_repricing_limit * 0.75), 1),
            tightened_min_net_edge_bps=float(base_min_net_edge_bps) * 1.25,
        )
    return DepthRegimeDecision(
        regime="deep",
        tightened_size_cap=float(base_size_cap),
        tightened_repricing_limit=int(base_repricing_limit),
        tightened_min_net_edge_bps=float(base_min_net_edge_bps),
    )


def compute_realized_vs_projected_impact_error(
    *,
    projected_shift: float,
    realized_shift: float,
) -> float:
    """Return absolute impact-model error for depth-regime falsification loops."""

    return abs(float(realized_shift) - float(projected_shift))
