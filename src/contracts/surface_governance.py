"""Contracts for one-engine/two-surface governance and migration safety gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SurfaceDescriptor:
    """One user-facing or operator-facing surface bound to the canonical engine."""

    name: str
    surface_type: str  # studio | core | admin
    framework: str
    entrypoint: str
    consumes_control_plane: bool = True
    active: bool = True


@dataclass
class OneEngineTwoSurfaceContract:
    """Enforce that multiple surfaces share one canonical engine identifier."""

    engine_id: str
    surfaces: list[SurfaceDescriptor] = field(default_factory=list)

    def add_surface(self, surface: SurfaceDescriptor) -> None:
        self.surfaces.append(surface)

    def validate(self) -> dict[str, Any]:
        active = [s for s in self.surfaces if s.active]
        if len(active) < 2:
            raise ValueError("at least two active surfaces are required (studio/core)")
        surface_types = {s.surface_type for s in active}
        if "studio" not in surface_types or "core" not in surface_types:
            raise ValueError("active surfaces must include both studio and core")
        frameworks = {s.framework.strip().lower() for s in active if s.surface_type == "studio"}
        if len(frameworks) != 1:
            raise ValueError("studio surface must resolve to one primary framework per release phase")
        non_api = [s.name for s in active if not s.consumes_control_plane]
        if non_api:
            raise ValueError(f"surfaces must consume control plane APIs: {non_api}")
        return {
            "engine_id": self.engine_id,
            "active_surface_count": len(active),
            "studio_framework": next(iter(frameworks)),
            "validated": True,
        }


@dataclass(frozen=True)
class ActionMapping:
    action: str
    ui_route: str
    cli_command: str
    api_endpoint: str


def validate_action_parity(mappings: list[ActionMapping]) -> dict[str, Any]:
    if not mappings:
        raise ValueError("at least one action mapping is required")
    seen: set[str] = set()
    for mapping in mappings:
        key = mapping.action.strip().lower()
        if not key:
            raise ValueError("action cannot be empty")
        if key in seen:
            raise ValueError(f"duplicate action mapping: {mapping.action}")
        seen.add(key)
        if not mapping.ui_route.strip():
            raise ValueError(f"missing ui_route for action {mapping.action}")
        if not mapping.cli_command.strip():
            raise ValueError(f"missing cli_command for action {mapping.action}")
        if not mapping.api_endpoint.strip():
            raise ValueError(f"missing api_endpoint for action {mapping.action}")
    return {"mapped_actions": len(mappings), "validated": True}


@dataclass(frozen=True)
class UIMigrationGateInput:
    parity_passed: bool
    risk_controls_passed: bool
    operator_actions_passed: bool
    rollback_playbook_present: bool


def evaluate_ui_migration_gate(payload: UIMigrationGateInput) -> dict[str, Any]:
    checks = {
        "parity_passed": bool(payload.parity_passed),
        "risk_controls_passed": bool(payload.risk_controls_passed),
        "operator_actions_passed": bool(payload.operator_actions_passed),
        "rollback_playbook_present": bool(payload.rollback_playbook_present),
    }
    passed = all(checks.values())
    return {
        "passed": passed,
        "checks": checks,
        "decision": "allow_cutover" if passed else "block_cutover",
    }
