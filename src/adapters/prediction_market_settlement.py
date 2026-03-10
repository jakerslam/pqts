"""Settlement invariants and registry gates for prediction-market adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TypedOrder:
    """Typed structured order contract equivalent to EIP-712-style binding."""

    maker: str
    taker: str
    maker_asset: str
    taker_asset: str
    maker_amount: float
    taker_amount: float
    chain_id: int
    domain_separator: str
    signature: str


def validate_typed_order(order: TypedOrder) -> dict[str, Any]:
    if order.chain_id <= 0:
        raise ValueError("chain_id must be > 0")
    if not order.domain_separator.strip():
        raise ValueError("domain_separator is required")
    if not order.signature.strip():
        raise ValueError("signature is required")
    if order.maker_amount <= 0 or order.taker_amount <= 0:
        raise ValueError("maker_amount and taker_amount must be > 0")
    return {"validated": True, "chain_id": int(order.chain_id)}


def evaluate_settlement_invariants(
    *,
    scenario: str,
    maker_amount: float,
    taker_amount: float,
    complement_amount: float = 0.0,
) -> dict[str, Any]:
    token_a = float(maker_amount)
    token_b = float(taker_amount)
    comp = float(complement_amount)
    scenario_token = str(scenario).strip().lower()

    if scenario_token == "normal":
        passed = token_a > 0 and token_b > 0
    elif scenario_token == "mint":
        passed = token_a > 0 and token_b > 0 and abs(token_a - token_b) <= 1e-9
    elif scenario_token == "merge":
        passed = token_a > 0 and comp > 0 and abs(token_a - comp) <= 1e-9
    else:
        raise ValueError(f"unsupported scenario: {scenario}")
    return {"scenario": scenario_token, "passed": passed}


def symmetric_fee(
    *,
    side: str,
    price: float,
    size: float,
    base_fee_rate: float,
) -> float:
    token = str(side).strip().lower()
    p = max(0.0, min(1.0, float(price)))
    q = max(0.0, float(size))
    rate = max(0.0, float(base_fee_rate))
    core = rate * min(p, 1.0 - p) * q
    if token == "sell":
        return core
    if token == "buy":
        return core / p if p > 0 else 0.0
    raise ValueError(f"unsupported side: {side}")


def verify_fee_symmetry(
    *,
    price: float,
    size: float,
    base_fee_rate: float,
    tolerance: float = 1e-6,
) -> dict[str, Any]:
    p = max(0.0, min(1.0, float(price)))
    buy_a = symmetric_fee(side="buy", price=p, size=size, base_fee_rate=base_fee_rate) * p
    sell_complement = symmetric_fee(
        side="sell", price=(1.0 - p), size=size, base_fee_rate=base_fee_rate
    )
    delta = abs(buy_a - sell_complement)
    return {
        "passed": delta <= float(tolerance),
        "delta": float(delta),
        "buy_value_fee": float(buy_a),
        "sell_complement_fee": float(sell_complement),
    }


def validate_deployment_registry(
    *,
    registry_path: str | Path,
    environment: str,
    chain: str,
    address: str,
) -> dict[str, Any]:
    payload = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    env_map = payload.get("environments", {})
    chain_map = env_map.get(str(environment), {}).get(str(chain), {})
    expected = str(chain_map.get("exchange_address", "")).lower()
    actual = str(address).strip().lower()
    if not expected:
        raise ValueError("missing expected exchange_address in registry")
    if expected != actual:
        raise ValueError("configured settlement address is not approved in registry")
    audits = chain_map.get("audits", [])
    if not isinstance(audits, list) or not audits:
        raise ValueError("missing audit artifact links for registry entry")
    return {"validated": True, "environment": str(environment), "chain": str(chain)}
