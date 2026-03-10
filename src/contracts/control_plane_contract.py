"""Control-plane contract validation for active user/operator surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ControlPlaneContract:
    base_url: str
    required_health_endpoints: tuple[str, ...] = ("/health", "/ready")
    required_action_endpoints: tuple[str, ...] = ()


def _normalize_path(path: str) -> str:
    token = str(path).strip()
    if not token.startswith("/"):
        token = f"/{token}"
    if token != "/":
        token = token.rstrip("/")
    return token


def validate_control_plane_contract(
    *,
    contract: ControlPlaneContract,
    available_routes: Iterable[str],
) -> dict[str, Any]:
    available = {_normalize_path(path) for path in available_routes}

    missing_health = [
        path
        for path in (_normalize_path(item) for item in contract.required_health_endpoints)
        if path not in available
    ]
    missing_actions = [
        path
        for path in (_normalize_path(item) for item in contract.required_action_endpoints)
        if path not in available
    ]

    if missing_health or missing_actions:
        raise ValueError(
            "control-plane contract violation: "
            f"missing_health={missing_health} missing_actions={missing_actions}"
        )

    return {
        "validated": True,
        "base_url": contract.base_url,
        "required_health_count": len(contract.required_health_endpoints),
        "required_action_count": len(contract.required_action_endpoints),
        "route_count": len(available),
    }
