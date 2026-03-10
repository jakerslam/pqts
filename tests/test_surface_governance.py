from __future__ import annotations

import pytest

from contracts.surface_governance import (
    ActionMapping,
    OneEngineTwoSurfaceContract,
    SurfaceDescriptor,
    UIMigrationGateInput,
    evaluate_ui_migration_gate,
    validate_action_parity,
)


def test_one_engine_two_surface_contract_validates() -> None:
    contract = OneEngineTwoSurfaceContract(engine_id="core-engine")
    contract.add_surface(
        SurfaceDescriptor(
            name="studio-web",
            surface_type="studio",
            framework="dash",
            entrypoint="src/dashboard/start.py",
            consumes_control_plane=True,
        )
    )
    contract.add_surface(
        SurfaceDescriptor(
            name="core-cli",
            surface_type="core",
            framework="python-cli",
            entrypoint="src/app/runtime.py",
            consumes_control_plane=True,
        )
    )
    report = contract.validate()
    assert report["validated"] is True
    assert report["active_surface_count"] == 2


def test_one_engine_two_surface_contract_rejects_multiple_studio_frameworks() -> None:
    contract = OneEngineTwoSurfaceContract(engine_id="core-engine")
    contract.add_surface(
        SurfaceDescriptor(
            name="studio-a",
            surface_type="studio",
            framework="dash",
            entrypoint="a",
            consumes_control_plane=True,
        )
    )
    contract.add_surface(
        SurfaceDescriptor(
            name="studio-b",
            surface_type="studio",
            framework="streamlit",
            entrypoint="b",
            consumes_control_plane=True,
        )
    )
    contract.add_surface(
        SurfaceDescriptor(
            name="core-cli",
            surface_type="core",
            framework="python-cli",
            entrypoint="c",
            consumes_control_plane=True,
        )
    )
    with pytest.raises(ValueError, match="one primary framework"):
        contract.validate()


def test_validate_action_parity_accepts_complete_mapping() -> None:
    report = validate_action_parity(
        [
            ActionMapping(
                action="pause",
                ui_route="/ops/pause",
                cli_command="pqts run --pause",
                api_endpoint="/v1/operator/pause",
            )
        ]
    )
    assert report["validated"] is True


def test_validate_action_parity_rejects_missing_command() -> None:
    with pytest.raises(ValueError, match="missing cli_command"):
        validate_action_parity(
            [
                ActionMapping(
                    action="pause",
                    ui_route="/ops/pause",
                    cli_command="",
                    api_endpoint="/v1/operator/pause",
                )
            ]
        )


def test_ui_migration_gate_blocks_when_checks_fail() -> None:
    report = evaluate_ui_migration_gate(
        UIMigrationGateInput(
            parity_passed=True,
            risk_controls_passed=False,
            operator_actions_passed=True,
            rollback_playbook_present=True,
        )
    )
    assert report["passed"] is False
    assert report["decision"] == "block_cutover"
