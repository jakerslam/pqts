"""Policy-constrained autonomous operator permission checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OperatorPolicy:
    allow_propose: bool = True
    allow_simulate: bool = True
    allow_execute: bool = False
    require_human_approval_for_execute: bool = True


@dataclass(frozen=True)
class OperatorActionRequest:
    action_type: str  # propose|simulate|execute
    capital_impact: bool
    human_approved: bool


def evaluate_operator_action(
    *,
    policy: OperatorPolicy,
    request: OperatorActionRequest,
) -> dict[str, Any]:
    token = str(request.action_type).strip().lower()
    if token == "propose":
        allowed = bool(policy.allow_propose)
    elif token == "simulate":
        allowed = bool(policy.allow_simulate)
    elif token == "execute":
        allowed = bool(policy.allow_execute)
        if allowed and request.capital_impact and policy.require_human_approval_for_execute:
            allowed = bool(request.human_approved)
    else:
        raise ValueError(f"unsupported action_type: {request.action_type}")
    return {"action_type": token, "allowed": bool(allowed)}
