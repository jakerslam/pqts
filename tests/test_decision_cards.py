from execution.decision_cards import build_decision_card, load_decision_cards, persist_decision_card


def test_decision_card_build_and_persist_roundtrip(tmp_path) -> None:
    card = build_decision_card(
        card_id="card_1",
        strategy_id="trend_following",
        market_id="BTCUSDT",
        p_market=0.51,
        p_model=0.57,
        posterior_before=0.54,
        posterior_after=0.57,
        gross_edge_bps=60.0,
        total_penalty_bps=15.0,
        net_edge_bps=45.0,
        expected_value_bps=12.0,
        full_kelly_fraction=0.18,
        approved_fraction=0.05,
        stage="paper",
        gate_passed=True,
        gate_reason_codes=[],
        trust_label="reference",
        evidence_source="unit_test",
        evidence_ref="bundle_1",
    )
    path = tmp_path / "cards.jsonl"
    persist_decision_card(card, path)
    loaded = load_decision_cards(path, limit=10)
    assert len(loaded) == 1
    assert loaded[0]["card_id"] == "card_1"
    assert loaded[0]["gate_passed"] is True
