"""Incident copilot recommendations with safe rollback assistance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IncidentContext:
    incident_id: str
    stage: str
    strategy_id: str
    venue: str
    reject_rate: float
    latency_ms: float
    drawdown_pct: float


def recommend_incident_response(context: IncidentContext) -> dict[str, Any]:
    stage = str(context.stage).strip().lower()
    if stage not in {"paper", "shadow", "canary", "live"}:
        raise ValueError(f"unsupported stage for incident response: {context.stage}")

    actions: list[str] = []
    if context.reject_rate >= 0.40:
        actions.append("reroute_venue")
    if context.latency_ms >= 500.0:
        actions.append("throttle_size")
    if context.drawdown_pct <= -0.03:
        actions.append("reduce_risk_limits")

    rollback_stage = ""
    if stage == "live" and (context.reject_rate >= 0.50 or context.drawdown_pct <= -0.05):
        rollback_stage = "canary"
    elif stage == "canary" and (context.reject_rate >= 0.50 or context.drawdown_pct <= -0.05):
        rollback_stage = "shadow"

    recommendation = "monitor"
    if rollback_stage:
        recommendation = "rollback"
    elif actions:
        recommendation = "mitigate"

    return {
        "incident_id": context.incident_id,
        "strategy_id": context.strategy_id,
        "venue": context.venue,
        "recommendation": recommendation,
        "rollback_stage": rollback_stage,
        "actions": actions,
        "requires_human_approval": recommendation in {"rollback", "mitigate"},
    }
