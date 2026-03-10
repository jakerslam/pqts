from __future__ import annotations

from execution.profitability_math import build_profitability_preview


def test_build_profitability_preview_returns_consistent_math() -> None:
    preview = build_profitability_preview(
        expected_alpha_bps=12.0,
        expected_cost_usd=1.5,
        expected_slippage_usd=2.5,
        notional_usd=1_000.0,
        min_edge_bps=0.5,
    )
    assert preview.expected_alpha_bps == 12.0
    assert preview.predicted_total_router_bps == 40.0
    assert preview.predicted_net_alpha_bps == -28.0
    assert preview.required_alpha_bps == 40.5

