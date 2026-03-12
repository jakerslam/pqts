from execution.lunar_edge_gate import NetEdgeGateInputs, evaluate_net_edge_gate


def test_net_edge_gate_passes_when_edge_and_timing_are_valid() -> None:
    decision = evaluate_net_edge_gate(
        NetEdgeGateInputs(
            model_probability=0.57,
            market_probability=0.51,
            fee_bps=4.0,
            spread_bps=2.0,
            slippage_bps=3.0,
            latency_penalty_bps=1.0,
            min_net_edge_bps=10.0,
            evidence_ts_ms=1_000,
            market_ts_ms=1_200,
            now_ts_ms=2_000,
            max_repricing_lag_ms=1_000,
            max_data_age_ms=1_500,
        )
    )
    assert decision.passed is True
    assert decision.net_edge_bps > 10.0
    assert decision.reason_codes == ()


def test_net_edge_gate_fails_closed_on_missing_timestamps_and_low_edge() -> None:
    decision = evaluate_net_edge_gate(
        NetEdgeGateInputs(
            model_probability=0.5205,
            market_probability=0.52,
            fee_bps=2.0,
            spread_bps=2.0,
            slippage_bps=2.0,
            latency_penalty_bps=0.5,
            min_net_edge_bps=5.0,
            require_timestamps=True,
            now_ts_ms=5_000,
        )
    )
    assert decision.passed is False
    assert "net_edge_below_threshold" in decision.reason_codes
    assert "missing_repricing_timestamps" in decision.reason_codes
    assert "missing_market_timestamp_for_age_check" in decision.reason_codes
