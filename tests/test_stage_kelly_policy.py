from execution.stage_kelly_policy import StageKellyPolicy, evaluate_stage_kelly


def test_stage_kelly_caps_fraction_by_stage_and_hard_caps() -> None:
    decision = evaluate_stage_kelly(
        posterior_probability=0.62,
        payout_multiple=1.1,
        stage="canary",
        policy=StageKellyPolicy(
            base_fraction=0.5,
            hard_per_trade_cap=0.04,
            hard_per_event_cap=0.03,
            stage_caps={"canary": 0.025},
        ),
    )
    assert decision.blocked is False
    assert decision.approved_fraction <= 0.025
    assert "fraction_capped" in decision.reason_codes


def test_stage_kelly_requires_audited_override_for_full_kelly() -> None:
    denied = evaluate_stage_kelly(
        posterior_probability=0.65,
        payout_multiple=1.2,
        stage="live",
        request_full_kelly=True,
    )
    assert denied.blocked is True
    assert "full_kelly_override_missing_audit" in denied.reason_codes

    allowed = evaluate_stage_kelly(
        posterior_probability=0.65,
        payout_multiple=1.2,
        stage="live",
        request_full_kelly=True,
        override_actor="risk_officer",
        override_reason="manual_exception_ticket_123",
    )
    assert allowed.blocked is False
    assert allowed.audit["override_actor"] == "risk_officer"
