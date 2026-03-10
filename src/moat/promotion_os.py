"""Promotion state machine, memo generation, and stage-aware capital policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

STAGES = ("backtest", "paper", "shadow", "canary", "live")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PromotionStateMachine:
    current_stage: str = "backtest"

    def transition(self, *, target_stage: str, checks_passed: bool) -> dict[str, Any]:
        target = str(target_stage).strip().lower()
        if target not in STAGES:
            raise ValueError(f"unsupported stage: {target_stage}")
        cur_idx = STAGES.index(self.current_stage)
        tgt_idx = STAGES.index(target)
        if tgt_idx != cur_idx + 1:
            raise ValueError(
                f"invalid stage jump: {self.current_stage} -> {target}; must advance sequentially"
            )
        if not checks_passed:
            return {"passed": False, "from": self.current_stage, "to": target, "blocked": True}
        previous = self.current_stage
        self.current_stage = target
        return {"passed": True, "from": previous, "to": self.current_stage, "blocked": False}


@dataclass(frozen=True)
class PromotionMemo:
    from_stage: str
    to_stage: str
    metrics: dict[str, Any]
    risk_delta: dict[str, Any]
    approvals: list[str]
    rollback_criteria: dict[str, Any]
    generated_at: str


def build_promotion_memo(
    *,
    from_stage: str,
    to_stage: str,
    metrics: dict[str, Any],
    risk_delta: dict[str, Any],
    approvals: list[str],
    rollback_criteria: dict[str, Any],
) -> PromotionMemo:
    return PromotionMemo(
        from_stage=str(from_stage),
        to_stage=str(to_stage),
        metrics=dict(metrics),
        risk_delta=dict(risk_delta),
        approvals=list(approvals),
        rollback_criteria=dict(rollback_criteria),
        generated_at=_utc_now_iso(),
    )


@dataclass(frozen=True)
class StageCapitalPolicy:
    stage_limits_usd: dict[str, float]
    expansion_window_days: int = 7


def evaluate_capital_policy(
    *,
    stage: str,
    current_allocation_usd: float,
    requested_allocation_usd: float,
    policy: StageCapitalPolicy,
) -> dict[str, Any]:
    stage_token = str(stage).strip().lower()
    limit = float(policy.stage_limits_usd.get(stage_token, 0.0))
    current = float(current_allocation_usd)
    requested = float(requested_allocation_usd)
    allowed = requested <= limit
    action = "expand" if requested > current else "contract_or_hold"
    return {
        "stage": stage_token,
        "limit_usd": limit,
        "current_allocation_usd": current,
        "requested_allocation_usd": requested,
        "allowed": bool(allowed),
        "action": action,
    }
