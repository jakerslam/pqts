from risk.cognitive_traps import CognitiveGuardrailInputs, evaluate_cognitive_guardrails


def test_cognitive_guardrails_hold_on_revenge_and_drawdown_breach() -> None:
    decision = evaluate_cognitive_guardrails(
        CognitiveGuardrailInputs(
            consecutive_losses=4,
            seconds_since_last_trade=120,
            requested_fraction=0.2,
            confidence_score=0.97,
            current_drawdown_pct=0.16,
            max_drawdown_pct=0.15,
            kill_switch_active=False,
        )
    )
    assert decision.decision == "HOLD"
    assert decision.approved_fraction == 0.0
    assert "revenge_reentry_risk" in decision.reason_codes
    assert "drawdown_limit_breached" in decision.reason_codes


def test_cognitive_guardrails_reduce_overconfidence_sizing() -> None:
    decision = evaluate_cognitive_guardrails(
        CognitiveGuardrailInputs(
            consecutive_losses=0,
            seconds_since_last_trade=4_000,
            requested_fraction=0.18,
            confidence_score=0.96,
            current_drawdown_pct=0.05,
            max_drawdown_pct=0.20,
            max_fraction_soft=0.10,
        )
    )
    assert decision.decision == "REDUCE"
    assert decision.approved_fraction <= 0.10
    assert "overconfidence_sizing" in decision.reason_codes
