"""No-code strategy constructor and EV/Kelly disclosure helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class NoCodeStrategySpec:
    name: str
    market_scope: str
    direction_policy: str
    template: str
    params: Mapping[str, Any]


def build_no_code_manifest(spec: NoCodeStrategySpec) -> dict[str, Any]:
    manifest = {
        "name": spec.name,
        "market_scope": spec.market_scope,
        "direction_policy": spec.direction_policy,
        "template": spec.template,
        "params": dict(spec.params),
        "runtime_path": "execution.RiskAwareRouter.submit_order",
    }
    return manifest


def manifest_cli_equivalent(manifest: Mapping[str, Any]) -> str:
    params = " ".join(f"--{k} {v}" for k, v in sorted(manifest.get("params", {}).items()))
    return (
        "pqts strategies create "
        f"--name {manifest.get('name')} "
        f"--scope {manifest.get('market_scope')} "
        f"--direction {manifest.get('direction_policy')} "
        f"--template {manifest.get('template')} {params}".strip()
    )


def manifest_json(manifest: Mapping[str, Any]) -> str:
    return json.dumps(manifest, indent=2)


def kelly_disclosure(
    *,
    win_probability: float,
    payout_multiple: float,
    fees: float,
    fractional_cap: float,
) -> dict[str, Any]:
    edge = win_probability * payout_multiple - (1.0 - win_probability)
    kelly = max(0.0, (edge / payout_multiple)) if payout_multiple > 0 else 0.0
    kelly = min(kelly, fractional_cap)
    return {
        "win_probability": float(win_probability),
        "payout_multiple": float(payout_multiple),
        "fees": float(fees),
        "fractional_cap": float(fractional_cap),
        "kelly_fraction": float(kelly),
        "edge": float(edge),
    }
