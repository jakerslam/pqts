"""Pure execution-math helpers for profitability and routing calculations."""

from __future__ import annotations

from dataclasses import dataclass

from core.hotpath_runtime import profitability_net_alpha_bps


@dataclass(frozen=True)
class ProfitabilityPreview:
    expected_alpha_bps: float
    predicted_total_router_bps: float
    predicted_net_alpha_bps: float
    required_alpha_bps: float


def build_profitability_preview(
    *,
    expected_alpha_bps: float,
    expected_cost_usd: float,
    expected_slippage_usd: float,
    notional_usd: float,
    min_edge_bps: float,
) -> ProfitabilityPreview:
    """Build a consistent profitability preview using native hotpath when available."""
    predicted_total_bps, predicted_net_bps, required_alpha_bps = profitability_net_alpha_bps(
        expected_alpha_bps=float(expected_alpha_bps),
        expected_cost_usd=float(expected_cost_usd),
        expected_slippage_usd=float(expected_slippage_usd),
        notional_usd=float(notional_usd),
        min_edge_bps=float(min_edge_bps),
    )
    return ProfitabilityPreview(
        expected_alpha_bps=float(expected_alpha_bps),
        predicted_total_router_bps=float(predicted_total_bps),
        predicted_net_alpha_bps=float(predicted_net_bps),
        required_alpha_bps=float(required_alpha_bps),
    )
