from __future__ import annotations

from analytics.noisy_ops import build_dislocation_candidates, summarize_bot_ops, wallet_boundary_check


def test_dislocation_candidates_and_summary() -> None:
    rows = [
        {"market_id": "m1", "edge": 0.05, "ev": 0.02, "liquidity": 100},
        {"market_id": "m2", "edge": -0.01, "ev": -0.01, "liquidity": 10},
    ]
    candidates = build_dislocation_candidates(rows, min_ev=0.0, min_liquidity=50)
    assert candidates[0].gate_outcome == "allow"
    summary = summarize_bot_ops(
        [
            {"market_id": "m1", "pnl": 1.0, "trades": 3},
            {"market_id": "m2", "pnl": -0.5, "trades": 2},
        ]
    )
    assert summary["markets"] == 2


def test_wallet_boundary_check() -> None:
    result = wallet_boundary_check(custody_enabled=False, verification_ok=True)
    assert result.allowed is True
