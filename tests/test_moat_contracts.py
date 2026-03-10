from __future__ import annotations

from datetime import date, datetime, timezone

from moat.autonomous_operator import OperatorActionRequest, OperatorPolicy, evaluate_operator_action
from moat.competitor_revalidation import CompetitorSource, evaluate_source_freshness
from moat.divergence import classify_divergence
from moat.execution_intelligence import (
    ExecutionIntelligenceStore,
    recommend_route_from_intelligence,
)
from moat.governance import (
    RoadmapItem,
    TeamActionRequest,
    enforce_moat_capacity_share,
    evaluate_team_action,
)
from moat.incident_copilot import IncidentContext, recommend_incident_response
from moat.order_truth_graph import OrderTruthGraph
from moat.promotion_os import (
    PromotionStateMachine,
    StageCapitalPolicy,
    build_promotion_memo,
    evaluate_capital_policy,
)
from moat.proof_pipeline import ProofArtifactPipeline, evaluate_trust_classification
from moat.proof_schedule import ProofSchedulePolicy, schedule_due
from moat.strategy_surface import CanonicalStrategyObject, validate_transparency_mapping


def test_order_truth_graph_query_filters() -> None:
    graph = OrderTruthGraph()
    graph.add_node(
        node_id="n1",
        order_id="o1",
        node_type="signal",
        strategy="mm",
        venue="v1",
        run_id="r1",
        payload={"x": 1},
    )
    graph.add_node(
        node_id="n2",
        order_id="o2",
        node_type="fill",
        strategy="arb",
        venue="v2",
        run_id="r2",
        payload={"x": 2},
    )
    assert len(graph.query(strategy="mm")) == 1
    assert len(graph.query(venue="v2")) == 1


def test_divergence_classification_returns_prescriptive_action() -> None:
    report = classify_divergence(
        expected_fill_rate=0.8,
        actual_fill_rate=0.1,
        expected_latency_ms=100,
        actual_latency_ms=120,
        reject_rate=0.6,
    )
    assert report["recommended_action"] in {"reroute", "resize", "hold_canary", "continue"}


def test_promotion_state_machine_and_memo() -> None:
    machine = PromotionStateMachine(current_stage="backtest")
    transition = machine.transition(target_stage="paper", checks_passed=True)
    assert transition["passed"] is True
    memo = build_promotion_memo(
        from_stage="backtest",
        to_stage="paper",
        metrics={"sharpe": 1.2},
        risk_delta={"drawdown": -0.01},
        approvals=["risk_officer"],
        rollback_criteria={"max_reject_rate": 0.4},
    )
    assert memo.to_stage == "paper"


def test_stage_capital_policy() -> None:
    policy = StageCapitalPolicy(stage_limits_usd={"paper": 1_000.0, "canary": 5_000.0})
    report = evaluate_capital_policy(
        stage="paper",
        current_allocation_usd=500.0,
        requested_allocation_usd=900.0,
        policy=policy,
    )
    assert report["allowed"] is True


def test_execution_intelligence_routing() -> None:
    store = ExecutionIntelligenceStore()
    store.add_sample(
        venue="a",
        strategy="mm",
        reject_rate=0.1,
        slippage_bps=5,
        cancel_replace_latency_ms=20,
        queue_score=0.8,
    )
    store.add_sample(
        venue="b",
        strategy="mm",
        reject_rate=0.3,
        slippage_bps=10,
        cancel_replace_latency_ms=40,
        queue_score=0.5,
    )
    choice = recommend_route_from_intelligence(
        venue_summaries=[store.summarize("a"), store.summarize("b")],
        max_reject_rate=0.25,
    )
    assert choice["recommended_venue"] == "a"


def test_strategy_surface_transparency() -> None:
    strategy = CanonicalStrategyObject(
        strategy_id="s1",
        name="Market Making",
        mode="paper",
        config={"spread_bps": 5},
        code_ref="src/strategies/market_making.py",
    )
    assert strategy.strategy_id == "s1"
    report = validate_transparency_mapping(
        {"pause": {"ui": "/ops/pause", "cli": "pqts run", "api": "/v1/operator/pause"}}
    )
    assert report["validated"] is True


def test_autonomous_operator_policy_enforced() -> None:
    policy = OperatorPolicy(allow_execute=True, require_human_approval_for_execute=True)
    denied = evaluate_operator_action(
        policy=policy,
        request=OperatorActionRequest(
            action_type="execute",
            capital_impact=True,
            human_approved=False,
        ),
    )
    assert denied["allowed"] is False


def test_proof_pipeline_and_trust_downgrade(tmp_path) -> None:
    pipeline = ProofArtifactPipeline()
    pipeline.publish(
        artifact_id="a1",
        artifact_type="benchmark",
        result_class="reference",
        command="python3 scripts/run_simulation_suite.py",
        provenance_ref="data/reports/provenance/benchmark_provenance.jsonl",
    )
    out = pipeline.write_manifest(tmp_path / "proof_manifest.json")
    assert out.exists()
    assert evaluate_trust_classification(has_reproducible_evidence=False, requested_class="reference") == "unverified"


def test_team_governance_and_roadmap_capacity() -> None:
    action = evaluate_team_action(
        TeamActionRequest(
            role="operator",
            action="promote",
            strategy_id="s1",
            venue="v1",
            approved_by=["risk_officer"],
        )
    )
    assert action["allowed"] is True
    capacity = enforce_moat_capacity_share(
        items=[
            RoadmapItem(item_id="p1", track="parity", points=4),
            RoadmapItem(item_id="m1", track="moat", points=6),
        ],
        min_moat_share=0.5,
    )
    assert capacity["passed"] is True


def test_competitor_source_revalidation() -> None:
    report = evaluate_source_freshness(
        sources=[
            CompetitorSource(
                name="QuantConnect",
                url="https://www.quantconnect.com/docs/v2/cloud-platform/welcome",
                last_validated="2026-03-05",
            )
        ],
        today=date(2026, 3, 10),
        max_age_days=10,
    )
    assert report["passed"] is True


def test_incident_copilot_recommends_rollback_on_severe_metrics() -> None:
    report = recommend_incident_response(
        IncidentContext(
            incident_id="inc-1",
            stage="live",
            strategy_id="market_making",
            venue="polygon",
            reject_rate=0.7,
            latency_ms=900.0,
            drawdown_pct=-0.08,
        )
    )
    assert report["recommendation"] == "rollback"
    assert report["rollback_stage"] == "canary"


def test_proof_schedule_due_logic() -> None:
    now = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)
    due = schedule_due(
        last_run_at="2026-03-09T00:00:00+00:00",
        now=now,
        policy=ProofSchedulePolicy(cadence_hours=24),
    )
    assert due is True
