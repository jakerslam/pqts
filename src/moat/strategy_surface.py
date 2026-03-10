"""Canonical strategy object and cross-surface transparency mapping contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CanonicalStrategyObject:
    strategy_id: str
    name: str
    mode: str
    config: dict[str, Any]
    code_ref: str


def validate_transparency_mapping(mapping: dict[str, dict[str, str]]) -> dict[str, Any]:
    if not mapping:
        raise ValueError("at least one mapping is required")
    for action, payload in mapping.items():
        ui = str(payload.get("ui", "")).strip()
        cli = str(payload.get("cli", "")).strip()
        api = str(payload.get("api", "")).strip()
        if not ui or not cli or not api:
            raise ValueError(f"incomplete transparency mapping for action: {action}")
    return {"validated": True, "mapped_actions": len(mapping)}
