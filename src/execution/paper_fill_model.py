"""Deterministic microstructure-aware paper fill provider."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from core.hotpath_runtime import paper_fill_metrics, uniform_from_seed
from execution.tca_feedback import ExecutionFill


@dataclass(frozen=True)
class PaperFillModelConfig:
    """Configuration for deterministic paper execution simulation."""

    base_latency_ms: float = 35.0
    latency_jitter_ms: float = 45.0
    partial_fill_notional_usd: float = 25000.0
    min_partial_fill_ratio: float = 0.55
    adverse_selection_bps: float = 1.5
    min_slippage_bps: float = 1.0
    reality_stress_mode: bool = False
    stress_slippage_multiplier: float = 2.5
    stress_fill_ratio_multiplier: float = 0.70
    hard_reject_notional_usd: float = 250000.0
    queue_penalty_floor: float = 0.20
    queue_slippage_bps_per_turnover: float = 0.10


class MicrostructurePaperFillProvider:
    """Generate deterministic fills with partial-fill and impact realism."""

    def __init__(self, config: PaperFillModelConfig | None = None):
        self.config = config or PaperFillModelConfig()

    @staticmethod
    def _uniform(*parts: object) -> float:
        payload = "|".join(str(p) for p in parts)
        return uniform_from_seed(payload)

    def _latency_ms(self, *, order_id: str, symbol: str, venue: str) -> float:
        u = self._uniform(order_id, symbol, venue, "latency")
        return float(self.config.base_latency_ms + (self.config.latency_jitter_ms * u))

    def _fill_ratio(
        self,
        *,
        order_id: str,
        symbol: str,
        venue: str,
        notional: float,
    ) -> float:
        if notional <= self.config.partial_fill_notional_usd:
            return 1.0

        capacity_ratio = self.config.partial_fill_notional_usd / max(notional, 1e-9)
        capacity_ratio = max(min(capacity_ratio, 1.0), self.config.min_partial_fill_ratio)
        u = self._uniform(order_id, symbol, venue, "fill_ratio")
        jitter = 0.9 + (0.2 * u)
        return float(max(min(capacity_ratio * jitter, 1.0), self.config.min_partial_fill_ratio))

    def _estimate_queue_ahead_qty(
        self,
        *,
        side: str,
        order_book: Optional[Dict[str, Any]],
        queue_ahead_qty: Optional[float],
    ) -> float:
        if queue_ahead_qty is not None:
            return float(max(queue_ahead_qty, 0.0))

        if not isinstance(order_book, dict):
            return 0.0
        try:
            bids = list(order_book.get("bids", []))
            asks = list(order_book.get("asks", []))
        except Exception:
            return 0.0

        side_token = str(side).lower()
        if side_token == "buy" and bids:
            return float(max(float(bids[0][1]), 0.0))
        if side_token == "sell" and asks:
            return float(max(float(asks[0][1]), 0.0))
        return 0.0

    def estimate_expected_slippage_bps(
        self,
        *,
        symbol: str,
        venue: str,
        side: str,
        requested_qty: float,
        reference_price: float,
        order_book: Optional[Dict[str, Any]] = None,
        queue_ahead_qty: Optional[float] = None,
    ) -> float:
        """Deterministic expected slippage estimate (excludes random jitter)."""
        _ = (symbol, venue)
        notional = float(requested_qty) * float(reference_price)
        impact_scale = max((notional / max(self.config.partial_fill_notional_usd, 1e-9)) - 1.0, 0.0)

        queue_qty = self._estimate_queue_ahead_qty(
            side=side,
            order_book=order_book,
            queue_ahead_qty=queue_ahead_qty,
        )
        queue_notional = queue_qty * float(reference_price)
        order_notional = max(float(requested_qty) * float(reference_price), 1e-9)
        if queue_notional <= 0.0:
            queue_turnover = 0.0
        else:
            queue_turnover = order_notional / queue_notional

        slip_bps = self.config.adverse_selection_bps * (0.5 + impact_scale)
        slip_bps += float(self.config.queue_slippage_bps_per_turnover) * max(queue_turnover, 0.0)
        slip_bps = max(float(slip_bps), float(self.config.min_slippage_bps))
        if bool(self.config.reality_stress_mode):
            slip_bps *= float(self.config.stress_slippage_multiplier)
        return float(slip_bps)

    async def get_fill(
        self,
        *,
        order_id: str,
        symbol: str,
        venue: str,
        side: str,
        requested_qty: float,
        reference_price: float,
        order_book: Optional[Dict[str, Any]] = None,
        queue_ahead_qty: Optional[float] = None,
    ) -> ExecutionFill:
        notional = float(requested_qty) * float(reference_price)
        if notional >= self.config.hard_reject_notional_usd:
            latency_ms = self._latency_ms(order_id=order_id, symbol=symbol, venue=venue)
            timestamp = datetime.now(timezone.utc) + timedelta(milliseconds=latency_ms)
            return ExecutionFill(
                executed_price=float(reference_price),
                executed_qty=0.0,
                timestamp=timestamp,
                venue=venue,
                symbol=symbol,
            )

        queue_qty = self._estimate_queue_ahead_qty(
            side=side,
            order_book=order_book,
            queue_ahead_qty=queue_ahead_qty,
        )
        fill_uniform = self._uniform(order_id, symbol, venue, "fill_ratio")
        slippage_uniform = self._uniform(order_id, symbol, venue, "slippage")
        _fill_ratio, _slip_bps, executed_qty, executed_price, _queue_turnover = paper_fill_metrics(
            side=str(side),
            requested_qty=float(requested_qty),
            reference_price=float(reference_price),
            queue_qty=float(queue_qty),
            partial_fill_notional_usd=float(self.config.partial_fill_notional_usd),
            min_partial_fill_ratio=float(self.config.min_partial_fill_ratio),
            queue_penalty_floor=float(self.config.queue_penalty_floor),
            adverse_selection_bps=float(self.config.adverse_selection_bps),
            min_slippage_bps=float(self.config.min_slippage_bps),
            queue_slippage_bps_per_turnover=float(self.config.queue_slippage_bps_per_turnover),
            reality_stress_mode=bool(self.config.reality_stress_mode),
            stress_fill_ratio_multiplier=float(self.config.stress_fill_ratio_multiplier),
            stress_slippage_multiplier=float(self.config.stress_slippage_multiplier),
            fill_uniform=float(fill_uniform),
            slippage_uniform=float(slippage_uniform),
        )

        latency_ms = self._latency_ms(order_id=order_id, symbol=symbol, venue=venue)
        timestamp = datetime.now(timezone.utc) + timedelta(milliseconds=latency_ms)

        return ExecutionFill(
            executed_price=float(executed_price),
            executed_qty=float(executed_qty),
            timestamp=timestamp,
            venue=venue,
            symbol=symbol,
        )
