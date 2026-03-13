"""Behavioral pre-trade guardrails for deterministic hold/reduce decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CognitiveGuardrailInputs:
    consecutive_losses: int
    seconds_since_last_trade: int
    requested_fraction: float
    confidence_score: float
    current_drawdown_pct: float
    max_drawdown_pct: float
    kill_switch_active: bool = False
    revenge_cooldown_seconds: int = 900
    max_fraction_soft: float = 0.10


@dataclass(frozen=True)
class CognitiveGuardrailDecision:
    decision: str  # ALLOW | REDUCE | HOLD
    approved_fraction: float
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_cognitive_guardrails(inputs: CognitiveGuardrailInputs) -> CognitiveGuardrailDecision:
    hold_reasons: list[str] = []
    reduce_reasons: list[str] = []
    approved_fraction = max(0.0, float(inputs.requested_fraction))

    if bool(inputs.kill_switch_active):
        hold_reasons.append("kill_switch_active")
    if int(inputs.consecutive_losses) >= 3 and int(inputs.seconds_since_last_trade) < int(
        inputs.revenge_cooldown_seconds
    ):
        hold_reasons.append("revenge_reentry_risk")

    if float(inputs.max_drawdown_pct) > 0:
        drawdown_ratio = float(inputs.current_drawdown_pct) / float(inputs.max_drawdown_pct)
        if drawdown_ratio >= 1.0:
            hold_reasons.append("drawdown_limit_breached")
        elif drawdown_ratio >= 0.8:
            reduce_reasons.append("near_drawdown_limit")

    if approved_fraction > float(inputs.max_fraction_soft):
        reduce_reasons.append("overconfidence_sizing")
        approved_fraction = min(approved_fraction, float(inputs.max_fraction_soft))

    if (
        float(inputs.confidence_score) > 0.95
        and approved_fraction > float(inputs.max_fraction_soft) * 0.8
    ):
        reduce_reasons.append("confidence_extreme_clamp")
        approved_fraction = min(approved_fraction, float(inputs.max_fraction_soft) * 0.8)

    if hold_reasons:
        return CognitiveGuardrailDecision(
            decision="HOLD",
            approved_fraction=0.0,
            reason_codes=tuple(dict.fromkeys(hold_reasons + reduce_reasons)),
        )
    if reduce_reasons:
        return CognitiveGuardrailDecision(
            decision="REDUCE",
            approved_fraction=max(0.0, float(approved_fraction)),
            reason_codes=tuple(dict.fromkeys(reduce_reasons)),
        )
    return CognitiveGuardrailDecision(
        decision="ALLOW",
        approved_fraction=max(0.0, float(approved_fraction)),
        reason_codes=(),
    )
