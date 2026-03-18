from __future__ import annotations

from analytics.skew_payoff import (
    SkewTradeObservation,
    evaluate_loss_cluster_tolerance,
    evaluate_positive_skew_basket_expectancy,
    falsify_hit_rate_illusion,
)


def test_positive_skew_metrics_and_tail_dependency_flag() -> None:
    trades = [
        SkewTradeObservation(trade_id="t1", pnl=-10.0),
        SkewTradeObservation(trade_id="t2", pnl=-9.0),
        SkewTradeObservation(trade_id="t3", pnl=-8.0),
        SkewTradeObservation(trade_id="t4", pnl=4.0),
        SkewTradeObservation(trade_id="t5", pnl=120.0),
    ]
    metrics = evaluate_positive_skew_basket_expectancy(trades, top_tail_n=1, max_top_win_concentration=0.7)
    assert metrics.expectancy > 0.0
    assert metrics.hit_rate < 0.5
    assert metrics.unrealistic_tail_dependency is True


def test_loss_cluster_tolerance_and_hit_rate_illusion_falsification() -> None:
    loss_cluster = evaluate_loss_cluster_tolerance(
        outcomes=[-1.0, -2.0, -3.0, -1.0, 2.0],
        max_consecutive_losses=2,
        max_drawdown_pct=0.25,
    )
    assert loss_cluster.action in {"reduce", "halt"}
    assert "loss_cluster_tolerance_breached" in loss_cluster.reason_codes

    check = falsify_hit_rate_illusion(
        observed_hit_rate=0.80,
        observed_payoff_ratio=0.90,
        expected_hit_rate_band=(0.20, 0.40),
        expected_payoff_ratio_band=(2.0, 8.0),
    )
    assert check.pass_check is False
    assert "hit_rate_outside_declared_skew_band" in check.reason_codes
    assert "payoff_ratio_outside_declared_skew_band" in check.reason_codes
