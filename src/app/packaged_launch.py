"""Packaged desktop launch diagnostics for no-toolchain flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class PackagedLaunchDiagnostics:
    ok: bool
    python_required: bool
    unpack_ok: bool
    warnings: list[str] = field(default_factory=list)
    enforcement: list[str] = field(default_factory=list)


def evaluate_packaged_launch(*, flags: Mapping[str, bool]) -> PackagedLaunchDiagnostics:
    python_required = bool(flags.get("python_required", False))
    unpack_ok = bool(flags.get("unpack_ok", False))
    risk_router_ok = bool(flags.get("risk_router_ok", False))
    provenance_ok = bool(flags.get("provenance_ok", False))
    warnings: list[str] = []
    enforcement: list[str] = []

    if python_required:
        warnings.append("python_toolchain_required")
    if not unpack_ok:
        warnings.append("unpack_failed")
    if not risk_router_ok:
        enforcement.append("risk_router_missing")
    if not provenance_ok:
        enforcement.append("provenance_missing")

    ok = unpack_ok and risk_router_ok and provenance_ok and not python_required
    return PackagedLaunchDiagnostics(
        ok=ok,
        python_required=python_required,
        unpack_ok=unpack_ok,
        warnings=warnings,
        enforcement=enforcement,
    )
