"""Team action governance and roadmap capacity-share enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TeamActionRequest:
    role: str
    action: str
    strategy_id: str
    venue: str
    approved_by: list[str]


def evaluate_team_action(request: TeamActionRequest) -> dict[str, Any]:
    role = str(request.role).strip().lower()
    action = str(request.action).strip().lower()
    approvals = list(request.approved_by)
    if action in {"promote", "kill"} and len(approvals) < 1:
        return {"allowed": False, "reason": "approval_required"}
    if role not in {"author", "reviewer", "operator", "risk_officer", "admin"}:
        return {"allowed": False, "reason": "role_not_allowed"}
    return {"allowed": True, "reason": "policy_pass"}


@dataclass(frozen=True)
class RoadmapItem:
    item_id: str
    track: str  # parity|moat
    points: int


def enforce_moat_capacity_share(
    *,
    items: list[RoadmapItem],
    min_moat_share: float,
) -> dict[str, Any]:
    total = sum(max(0, int(item.points)) for item in items)
    moat = sum(max(0, int(item.points)) for item in items if item.track == "moat")
    share = (float(moat) / float(total)) if total > 0 else 0.0
    passed = share >= float(min_moat_share)
    return {"passed": passed, "moat_share": share, "min_moat_share": float(min_moat_share)}
