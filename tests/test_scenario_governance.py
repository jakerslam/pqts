from __future__ import annotations

from research.scenario_governance import (
    CatalystEdge,
    CommitteeStage,
    EntityNode,
    PopulationArchetypeResult,
    PrivateDataSource,
    RolePolicy,
    ScenarioCandidate,
    SeedMaterial,
    build_committee_decision_lineage,
    build_entity_catalyst_graph,
    build_private_data_provenance_decision,
    can_claim_affect_promotion,
    compute_consensus_polarization_cascade,
    emit_agent_handoff_receipt,
    evaluate_scenario_winner_selection_bias,
    generate_evidence_memo,
    ingest_external_claim,
    ingest_seed_materials,
    run_counterfactual_simulation,
    run_structured_bull_bear_debate,
    simulate_heterogeneous_population,
    validate_role_segregated_pipeline_policy,
)


def test_seed_ingestion_graph_and_counterfactual_memo() -> None:
    ingestion = ingest_seed_materials(
        [
            SeedMaterial(
                material_id="m1",
                kind="research_note",
                source_ref="doc://r1",
                captured_at="2026-03-18T00:00:00+00:00",
                trust_label="verified_internal",
                parser_version="p1",
                verifiable=True,
            ),
            SeedMaterial(
                material_id="m2",
                kind="news_summary",
                source_ref="doc://r2",
                captured_at="2025-01-01T00:00:00+00:00",
                trust_label="unverified_external",
                parser_version="p1",
                verifiable=False,
            ),
        ],
        max_age_days=90,
    )
    assert "m1" in ingestion.accepted_material_ids
    assert "m2" in ingestion.rejected_material_ids

    graph = build_entity_catalyst_graph(
        nodes=[
            EntityNode(
                node_id="asset_btc",
                entity_kind="asset",
                confidence=0.9,
                source_refs=("doc://r1",),
                updated_at="2026-03-18T00:00:00+00:00",
                conflict_flags=(),
            ),
            EntityNode(
                node_id="catalyst_fomc",
                entity_kind="catalyst",
                confidence=0.8,
                source_refs=("doc://r1",),
                updated_at="2026-03-18T00:00:00+00:00",
                conflict_flags=(),
            ),
        ],
        edges=[
            CatalystEdge(
                edge_id="e1",
                from_node="catalyst_fomc",
                to_node="asset_btc",
                relation="impacts",
                confidence=0.7,
                source_refs=("doc://r1",),
                updated_at="2026-03-18T00:00:00+00:00",
                conflict_flags=(),
            )
        ],
    )
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1

    sim = run_counterfactual_simulation(
        scenario_id="scn1",
        changed_assumptions=["higher_rate_path"],
        affected_entities=["asset_btc"],
        expected_market_impact="probability_yes_down",
        uncertainty_notes="sensitive to policy timing",
    )
    assert sim.challenger_only is True

    memo = generate_evidence_memo(
        observed_facts=["Rates surprised higher"],
        inferred_scenarios=["Risk-off regime likely"],
        speculative_counterfactuals=["If no surprise, yes-probability may rise"],
        artifact_links=["artifact://sim/scn1"],
    )
    assert "Observed facts:" in memo.memo_text
    assert "Speculative counterfactuals:" in memo.memo_text


def test_population_claims_roles_handoffs_and_bias_gates() -> None:
    pop = simulate_heterogeneous_population(
        [
            PopulationArchetypeResult(
                archetype="momentum",
                participation_count=20,
                decision_distribution={"buy": 0.6, "hold": 0.4},
                confidence_low=0.45,
                confidence_high=0.7,
            ),
            PopulationArchetypeResult(
                archetype="mean_revert",
                participation_count=15,
                decision_distribution={"buy": 0.2, "hold": 0.8},
                confidence_low=0.4,
                confidence_high=0.65,
            ),
        ]
    )
    assert pop.challenger_evidence_only is True
    telemetry = compute_consensus_polarization_cascade(
        decision_distribution={"buy": 0.62, "hold": 0.38},
        subgroup_bias_scores=[0.3, 0.7],
        cascade_trigger_score=0.72,
        cascade_threshold=0.65,
    )
    assert telemetry.instability_flag is True

    claim = ingest_external_claim(
        claim_id="c1",
        source_url="https://x.com/example/status/1",
        claim_text="10x in 3 days",
    )
    assert claim.trust_label == "unverified_external_claim"
    assert can_claim_affect_promotion(claim) is False

    role_policy = validate_role_segregated_pipeline_policy(
        [
            RolePolicy("scanner", True, True, False, False, False),
            RolePolicy("signal_synth", True, True, True, False, False),
            RolePolicy("risk_filter", True, False, True, True, False),
            RolePolicy("execution_intent", True, False, False, True, False),
        ]
    )
    assert role_policy.valid is True

    handoff = emit_agent_handoff_receipt(
        candidate_id="cand_1",
        upstream_receipt_refs=["receipt://scan/1"],
        from_role="scanner",
        to_role="signal_synth",
        delta_summary="added catalyst weighting",
        latency_ms=180,
        queue_ms=24,
    )
    assert handoff.queue_ms == 24

    private = build_private_data_provenance_decision(
        [
            PrivateDataSource(
                source_ref="private://dataset/1",
                entitlement_scope="licensed_internal",
                permitted_use="simulation_only",
                retention_policy="30d",
                expires_at="2099-01-01T00:00:00+00:00",
            )
        ]
    )
    assert private.allowed is True

    biased = evaluate_scenario_winner_selection_bias(
        candidates=[
            ScenarioCandidate(
                scenario_id="a",
                ranking_score=0.9,
                oos_score=0.2,
                used_post_event_data=True,
                has_verifiable_private_labels=True,
            ),
            ScenarioCandidate(
                scenario_id="b",
                ranking_score=0.8,
                oos_score=0.4,
                used_post_event_data=False,
                has_verifiable_private_labels=True,
            ),
        ],
        chosen_scenario_id="a",
        ranking_objective="max_sharpe",
        oos_window="2026Q1",
    )
    assert biased.allowed is False
    assert "post_event_information_detected" in biased.reason_codes
    assert "winner_not_oos_superior" in biased.reason_codes


def test_debate_and_committee_lineage_contracts() -> None:
    debate = run_structured_bull_bear_debate(
        affirmative_case="Catalyst implies repricing",
        counter_case="Signal stale and crowded",
        evidence_refs=["artifact://scan/1", "artifact://risk/4"],
        rounds_run=2,
        unresolved_contradiction_score=0.6,
        max_unresolved_score=0.4,
    )
    assert debate.action == "hold"
    assert "material_contradictions_unresolved" in debate.reason_codes

    lineage = build_committee_decision_lineage(
        [
            CommitteeStage("analyst", ("artifact://a",), "initial thesis", "2026-03-18T00:00:00+00:00", "advance"),
            CommitteeStage("debate", ("artifact://d",), "debated thesis", "2026-03-18T00:01:00+00:00", "revise"),
            CommitteeStage("trader", ("artifact://t",), "trade proposal", "2026-03-18T00:02:00+00:00", "advance"),
            CommitteeStage("risk", ("artifact://r",), "risk review", "2026-03-18T00:03:00+00:00", "advance"),
            CommitteeStage("portfolio_manager", ("artifact://pm",), "final verdict", "2026-03-18T00:04:00+00:00", "hold"),
        ]
    )
    assert lineage.reconstructable is True
    assert lineage.reason_codes == ()
