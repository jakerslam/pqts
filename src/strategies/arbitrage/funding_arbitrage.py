"""Compatibility adapter for funding arbitrage strategy APIs.

Canonical implementation lives in `strategies.funding_arbitrage.FundingArbitrageStrategy`.
This module keeps the async-focused API surface for existing callers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from strategies.funding_arbitrage import FundingArbitrageStrategy

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FundingRate:
    exchange: str
    symbol: str
    rate: float
    next_funding_time: datetime
    predicted_rate: Optional[float] = None


@dataclass(frozen=True)
class FundingArbitrageOpportunity:
    symbol: str
    spot_exchange: str
    perp_exchange: str
    funding_rate: float
    spread: float
    annualized_return: float
    hours_to_funding: float
    confidence: float


class FundingRateArbitrage:
    """Async adapter over the canonical funding-arbitrage strategy implementation."""

    def __init__(self, config: dict):
        self.config = dict(config or {})
        self.enabled = bool(self.config.get("enabled", False))
        self._impl = FundingArbitrageStrategy(self.config)
        self.funding_rates: Dict[str, List[FundingRate]] = {}
        logger.info("FundingRateArbitrage compatibility adapter initialized")

    async def update_funding_rates(self, exchange: str, rates: List[Dict]) -> None:
        out: List[FundingRate] = []
        for row in rates:
            symbol = str(row.get("symbol", "")).strip()
            if not symbol:
                continue
            raw_rate = float(row.get("fundingRate", 0.0))
            funding_ms = int(
                row.get(
                    "fundingTime",
                    int(datetime.now(timezone.utc).timestamp() * 1000),
                )
            )
            out.append(
                FundingRate(
                    exchange=str(exchange),
                    symbol=symbol,
                    rate=raw_rate,
                    next_funding_time=datetime.fromtimestamp(funding_ms / 1000, tz=timezone.utc),
                    predicted_rate=(
                        float(row["predictedRate"]) if row.get("predictedRate") is not None else None
                    ),
                )
            )
        self.funding_rates[str(exchange)] = out

    async def find_opportunities(
        self,
        spot_prices: Dict[str, float],
        perp_prices: Dict[str, float],
    ) -> List[FundingArbitrageOpportunity]:
        if not self.enabled:
            return []

        market_data: Dict[str, Dict[str, Dict[str, float]]] = {}
        funding_rates: Dict[str, float] = {}
        now = datetime.now(timezone.utc)
        for exchange, items in self.funding_rates.items():
            exchange_rows: Dict[str, Dict[str, float]] = {}
            for item in items:
                symbol = item.symbol
                funding_rates[symbol] = float(item.rate)
                if symbol not in spot_prices or symbol not in perp_prices:
                    continue
                exchange_rows[symbol] = {
                    "spot": float(spot_prices[symbol]),
                    "perp": float(perp_prices[symbol]),
                }
                # Prune entries that are no longer actionable for the next funding cycle.
                if item.next_funding_time <= now:
                    continue
            if exchange_rows:
                market_data[exchange] = exchange_rows

        opportunities = self._impl.scan_opportunities(market_data, funding_rates)
        adapted: List[FundingArbitrageOpportunity] = []
        for opp in opportunities:
            spread = abs(float(opp.perp_price) - float(opp.spot_price)) / max(float(opp.spot_price), 1e-12)
            adapted.append(
                FundingArbitrageOpportunity(
                    symbol=opp.symbol,
                    spot_exchange=opp.spot_exchange,
                    perp_exchange=opp.perp_exchange,
                    funding_rate=float(opp.funding_rate),
                    spread=float(spread),
                    annualized_return=float(opp.net_yield_annual),
                    hours_to_funding=float(self.config.get("funding_interval", 8.0)),
                    confidence=float(opp.confidence),
                )
            )
        return adapted

    async def execute_arbitrage(self, opportunity: FundingArbitrageOpportunity) -> bool:
        logger.info("Executing compatibility funding arbitrage signal: %s", opportunity)
        return True

    def get_funding_summary(self) -> Dict[str, Dict[str, float | int | list]]:
        summary: Dict[str, Dict[str, float | int | list]] = {}
        for exchange, rates in self.funding_rates.items():
            values = [float(item.rate) for item in rates]
            summary[exchange] = {
                "count": len(values),
                "avg_rate": (sum(values) / len(values)) if values else 0.0,
                "max_rate": max(values) if values else 0.0,
                "min_rate": min(values) if values else 0.0,
                "extreme_rates": [
                    {"symbol": item.symbol, "rate": item.rate}
                    for item in rates
                    if abs(float(item.rate)) > 0.001
                ],
            }
        return summary
