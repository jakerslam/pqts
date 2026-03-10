from __future__ import annotations

import pytest

from contracts.control_plane_contract import ControlPlaneContract, validate_control_plane_contract


def test_control_plane_contract_validates_with_required_routes() -> None:
    contract = ControlPlaneContract(
        base_url="http://localhost:8000",
        required_health_endpoints=("/health", "/ready"),
        required_action_endpoints=("/v1/operator/pause", "/v1/admin/kill-switch"),
    )
    report = validate_control_plane_contract(
        contract=contract,
        available_routes=["/health", "/ready", "/v1/operator/pause", "/v1/admin/kill-switch"],
    )
    assert report["validated"] is True


def test_control_plane_contract_rejects_missing_route() -> None:
    contract = ControlPlaneContract(
        base_url="http://localhost:8000",
        required_health_endpoints=("/health", "/ready"),
        required_action_endpoints=("/v1/operator/pause",),
    )
    with pytest.raises(ValueError, match="control-plane contract violation"):
        validate_control_plane_contract(contract=contract, available_routes=["/health", "/ready"])
