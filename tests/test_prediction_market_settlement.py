from __future__ import annotations

from pathlib import Path

import pytest

from adapters.prediction_market_settlement import (
    TypedOrder,
    evaluate_settlement_invariants,
    validate_deployment_registry,
    validate_typed_order,
    verify_fee_symmetry,
)


def test_validate_typed_order_passes_for_valid_payload() -> None:
    order = TypedOrder(
        maker="a",
        taker="b",
        maker_asset="USDC",
        taker_asset="YES",
        maker_amount=10.0,
        taker_amount=20.0,
        chain_id=137,
        domain_separator="pmkt",
        signature="0xabc",
    )
    report = validate_typed_order(order)
    assert report["validated"] is True
    assert report["chain_id"] == 137


def test_settlement_invariants_cover_normal_mint_merge() -> None:
    assert evaluate_settlement_invariants(scenario="normal", maker_amount=1, taker_amount=1)["passed"]
    assert evaluate_settlement_invariants(scenario="mint", maker_amount=2, taker_amount=2)["passed"]
    assert evaluate_settlement_invariants(
        scenario="merge", maker_amount=3, taker_amount=1, complement_amount=3
    )["passed"]


def test_fee_symmetry_passes_for_complementary_pricing() -> None:
    report = verify_fee_symmetry(price=0.10, size=100.0, base_fee_rate=0.02)
    assert report["passed"] is True


def test_validate_deployment_registry_approves_known_address() -> None:
    path = Path("config/integrations/settlement_registry.json")
    report = validate_deployment_registry(
        registry_path=path,
        environment="prod",
        chain="polygon",
        address="0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",
    )
    assert report["validated"] is True


def test_validate_deployment_registry_rejects_unknown_address() -> None:
    path = Path("config/integrations/settlement_registry.json")
    with pytest.raises(ValueError, match="not approved"):
        validate_deployment_registry(
            registry_path=path,
            environment="prod",
            chain="polygon",
            address="0x0000000000000000000000000000000000000000",
        )
