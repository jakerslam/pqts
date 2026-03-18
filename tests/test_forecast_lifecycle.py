from __future__ import annotations

from execution.forecast_lifecycle import (
    ForecastArtifact,
    ForecastArtifactRegistry,
    ForecastRevisionPolicy,
    ResolutionRiskInputs,
    classify_forecast_revision,
    detect_resolution_state_deterioration,
    determine_position_action,
    evaluate_resolution_gate,
)


def _artifact(*, version: int = 1, low: float = 0.40, high: float = 0.55) -> ForecastArtifact:
    return ForecastArtifact(
        forecast_id="f_1",
        version=version,
        market_id="mkt_1",
        outcome_id="YES",
        horizon_end_ts="2026-03-31T12:00:00+00:00",
        issued_at=f"2026-03-1{version}T00:00:00+00:00",
        producer_id="model_a",
        workflow_version="wf.v1",
        estimate_low=low,
        estimate_high=high,
        evidence_refs=("artifact://e1",),
        supersedes_version=(version - 1 if version > 1 else None),
        supersession_reason=("revision" if version > 1 else ""),
    )


def test_registry_issue_revision_and_decision_binding() -> None:
    registry = ForecastArtifactRegistry()
    first = registry.issue(_artifact(version=1, low=0.35, high=0.50))
    assert first.version == 1

    revised, revision = registry.revise(
        forecast_id="f_1",
        estimate_low=0.55,
        estimate_high=0.70,
        reason_code="fresh_feed_update",
    )
    assert revised.version == 2
    assert revision.classification == "strengthen"
    assert registry.latest("f_1").version == 2

    registry.bind_decision(decision_id="d_1", forecast_id="f_1", version=2)
    bound = registry.resolve_decision_binding("d_1")
    assert bound.version == 2
    assert bound.forecast_id == "f_1"


def test_revision_classification_and_position_policy() -> None:
    baseline = _artifact(version=1, low=0.60, high=0.72)
    assert classify_forecast_revision(baseline, estimate_low=0.40, estimate_high=0.45) == "weaken"
    assert (
        classify_forecast_revision(
            baseline,
            estimate_low=0.58,
            estimate_high=0.60,
            material_delta=0.10,
        )
        == "supersede"
    )
    assert (
        classify_forecast_revision(
            baseline,
            estimate_low=0.01,
            estimate_high=0.02,
            invalidated=True,
        )
        == "invalidate"
    )

    policy = ForecastRevisionPolicy(
        on_strengthen="hold",
        on_weaken="reduce",
        on_invalidate="exit",
        on_supersede="reprice",
    )
    assert determine_position_action(revision_classification="strengthen", policy=policy) == "hold"
    assert determine_position_action(revision_classification="weaken", policy=policy) == "reduce"
    assert determine_position_action(revision_classification="invalidate", policy=policy) == "exit"
    assert determine_position_action(revision_classification="supersede", policy=policy) == "reprice"


def test_resolution_ambiguity_gate_and_deterioration() -> None:
    low_risk = ResolutionRiskInputs(
        rule_clarity=0.90,
        source_finality=0.95,
        dispute_history_score=0.05,
        settlement_caveat_count=0,
    )
    high_risk = ResolutionRiskInputs(
        rule_clarity=0.25,
        source_finality=0.40,
        dispute_history_score=0.70,
        settlement_caveat_count=4,
    )

    allow = evaluate_resolution_gate(low_risk)
    assert allow.allow_entry is True
    assert allow.policy_action == "allow"

    blocked = evaluate_resolution_gate(high_risk)
    assert blocked.allow_entry is False
    assert blocked.policy_action in {"block", "shadow_only"}

    deteriorated, reason, metrics = detect_resolution_state_deterioration(
        baseline=low_risk,
        current=high_risk,
        deterioration_delta=0.10,
    )
    assert deteriorated is True
    assert reason == "resolution_risk_deteriorated"
    assert metrics["score_delta"] > 0.10
