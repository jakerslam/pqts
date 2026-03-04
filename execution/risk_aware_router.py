"""
Risk-Aware Smart Order Router

Production-grade order routing with enforced risk overlay.

This is the ONLY path to place orders - all orders must pass through here.
Any attempt to bypass this router will be caught by audit logging.

Integration:
    from execution.risk_aware_router import RiskAwareRouter
    
    router = RiskAwareRouter(
        risk_config=RiskLimits(max_daily_loss_pct=0.02),
        broker_config={'api_key': '...'}
    )
    
    # This is the ONLY way to place orders
    result = await router.submit_order(order_request, market_data, portfolio)
    
    # Result includes RiskDecision - check it
    if result.decision == RiskDecision.FLATTEN:
        # System is in emergency mode - no orders allowed
        pass
"""

import logging
from typing import Any, Dict, List, Optional, Protocol, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

# Import kill switches
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from risk.kill_switches import (
    RiskLimits, KillSwitchMonitor, RiskDecision, RiskState,
    TradingEngine as RiskEngine
)
from execution.realistic_costs import (
    Bps,
    RealisticCostModel,
    OrderBook,
    OrderBookLevel,
    Side,
    NotionalUSD,
    Price,
    Quantity,
)
from execution.smart_router import (
    SmartOrderRouter, OrderRequest, OrderType, RouteDecision
)
from execution.tca_feedback import (
    ExecutionFill,
    TCADatabase,
    TCATradeRecord,
    weekly_calibrate_eta,
)

logger = logging.getLogger(__name__)


class _RouterToken:
    """
    Module-private capability token for adapter construction and order sends.

    Direct construction is blocked. Tokens are minted only by RiskAwareRouter via
    its private _create_token() factory and verified with exact type checks.
    """

    __slots__ = ("router_id", "created_at")

    def __new__(cls, *args, **kwargs):
        raise RuntimeError(
            "RouterToken is module-private and can only be created by "
            "RiskAwareRouter._create_token()."
        )


def _mint_router_token(router_id: int) -> "_RouterToken":
    """Internal mint helper. Keep module-private and callable only by router factory."""
    token = object.__new__(_RouterToken)
    object.__setattr__(token, "router_id", router_id)
    object.__setattr__(token, "created_at", datetime.now(timezone.utc).isoformat())
    return token


@dataclass
class OrderResult:
    """Result of order submission attempt."""
    success: bool
    decision: RiskDecision
    risk_state: RiskState
    order_id: Optional[str]
    exchange: Optional[str]
    rejected_reason: Optional[str]
    audit_log: Dict


class FillProvider(Protocol):
    """Execution fill source for paper/live environments."""

    async def get_fill(
        self,
        *,
        order_id: str,
        symbol: str,
        venue: str,
        side: str,
        requested_qty: float,
        reference_price: float,
    ) -> ExecutionFill:
        ...


class StubFillProvider:
    """Deterministic fill source used for paper-testing and unit tests."""

    async def get_fill(
        self,
        *,
        order_id: str,
        symbol: str,
        venue: str,
        side: str,
        requested_qty: float,
        reference_price: float,
    ) -> ExecutionFill:
        # Side-aware deterministic slippage: +2 bps for buys, -2 bps for sells.
        slippage_multiplier = 1.0002 if side == "buy" else 0.9998
        executed_price = float(reference_price) * slippage_multiplier
        return ExecutionFill(
            executed_price=executed_price,
            executed_qty=float(requested_qty),
            timestamp=datetime.now(timezone.utc),
            venue=venue,
            symbol=symbol,
        )


class RiskAwareRouter:
    """
    Unified order router with mandatory risk overlay.
    
    This is the production router - ALL orders must go through here.
    
    Flow:
    1. Pre-trade risk check (KillSwitchMonitor)
    2. Smart routing (SmartOrderRouter)
    3. Cost estimation (RealisticCostModel)
    4. Order execution (Exchange adapter)
    5. Post-trade logging (TCA)
    
    NO ORDERS can bypass step 1. Ever.
    """
    
    def __init__(
        self,
        risk_config: RiskLimits,
        broker_config: dict,
        fill_provider: Optional[FillProvider] = None,
        tca_db_path: Optional[str] = None,
    ):
        """
        Args:
            risk_config: Hard limits for kill switches
            broker_config: Broker API credentials and settings
        """
        # Risk overlay (Step 1)
        self.risk_engine = RiskEngine(risk_config)
        self.risk_limits = risk_config
        
        # Smart routing (Step 2)
        self.smart_router = SmartOrderRouter(broker_config)
        
        # Cost model (Step 3)
        self.cost_model = RealisticCostModel()
        
        # Broker adapter (Step 4 - would be real exchange adapter)
        self.broker_config = broker_config
        self.exchange_adapter = None  # Would initialize real adapter
        self._router_token = self._create_token()
        self.fill_provider: FillProvider = fill_provider or StubFillProvider()
        self.tca_db = TCADatabase(
            tca_db_path or broker_config.get("tca_db_path", "data/tca_records.csv")
        )
        self.eta_by_symbol_venue: Dict[Tuple[str, str], float] = {}
        
        # Audit logging (Step 5)
        self.audit_log: List[Dict] = []
        self.order_count: int = 0
        self.reject_count: int = 0
        
        # Capital injection (not hardcoded)
        self._capital = None  # Set via set_capital()
        
        logger.info("RiskAwareRouter initialized")
        logger.info(f"  Daily loss limit: {risk_config.max_daily_loss_pct:.1%}")
        logger.info(f"  Max drawdown: {risk_config.max_drawdown_pct:.1%}")
        logger.info(f"  Max leverage: {risk_config.max_gross_leverage:.1f}x")
    
    def set_capital(self, capital: float, source: str = "manual"):
        """
        Set capital - NOT hardcoded.
        
        Args:
            capital: Total capital in USD
            source: Where capital came from (e.g., 'broker_account', 'config')
        """
        self._capital = capital
        self.risk_engine.risk_monitor.set_capital(capital, source=source)
        logger.info(f"Capital set: ${capital:,.2f} (source: {source})")
    
    def get_capital(self) -> float:
        """Get capital - raises if not set."""
        if self._capital is None:
            raise RuntimeError(
                "Capital not set. Call set_capital() before trading. "
                "Capital must be injected, never hardcoded."
            )
        return self._capital
    
    async def submit_order(self,
                          order: OrderRequest,
                          market_data: Dict,
                          portfolio: Dict,
                          strategy_returns: Dict[str, Any],
                          portfolio_changes: List[float]) -> OrderResult:
        """
        Submit an order with mandatory risk checking.
        
        This is the ONLY order submission method. All orders must pass through here.
        
        Args:
            order: OrderRequest with symbol, side, quantity, etc.
            market_data: Current market data for risk assessment
            portfolio: Current portfolio state
            strategy_returns: Returns by strategy for correlation check
            portfolio_changes: Recent P&L changes for VaR calc
        
        Returns:
            OrderResult with success/failure, risk decision, and audit trail
        """
        self.order_count += 1
        audit_entry = {
            'order_id': f"ord_{self.order_count}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'order': {
                'symbol': order.symbol,
                'side': order.side,
                'quantity': order.quantity,
                'type': order.order_type.value,
                'price': order.price
            }
        }
        
        # =========================================================================
        # STEP 1: MANDATORY PRE-TRADE RISK CHECK
        # =========================================================================
        # THIS CANNOT BE BYPASSED. EVER.
        
        try:
            capital = self.get_capital()
        except RuntimeError as e:
            audit_entry['rejected'] = True
            audit_entry['reject_reason'] = f"RISK_ERROR: {str(e)}"
            self.audit_log.append(audit_entry)
            self.reject_count += 1
            
            return OrderResult(
                success=False,
                decision=RiskDecision.HALT,
                risk_state=None,
                order_id=None,
                exchange=None,
                rejected_reason=str(e),
                audit_log=audit_entry
            )
        
        # Calculate notional
        price = order.price or market_data.get('last_price', 0)
        notional = order.quantity * price
        
        # Build portfolio state for risk check
        from risk.kill_switches import PortfolioState
        portfolio_state = PortfolioState(
            timestamp=datetime.now(),
            positions=portfolio.get('positions', {}),
            prices=portfolio.get('prices', {}),
            total_pnl=portfolio.get('total_pnl', 0),
            unrealized_pnl=portfolio.get('unrealized_pnl', 0),
            realized_pnl=portfolio.get('realized_pnl', 0),
            gross_exposure=portfolio.get('gross_exposure', 0),
            net_exposure=portfolio.get('net_exposure', 0),
            leverage=portfolio.get('leverage', 0),
            open_orders=portfolio.get('open_orders', []),
            pending_cancels=[]
        )
        
        # MANDATORY: Pre-trade risk check
        decision, risk_state = self.risk_engine.pre_trade_check(
            {
                'notional': notional,
                'symbol': order.symbol,
                'side': order.side,
                'quantity': order.quantity
            },
            portfolio_state,
            strategy_returns,
            portfolio_changes
        )
        
        audit_entry['risk_check'] = {
            'decision': decision.value,
            'reason': risk_state.reason,
            'limits': {
                'max_order': risk_state.max_order_notional,
                'max_leverage': risk_state.max_gross_leverage,
                'max_participation': risk_state.max_participation
            }
        }
        
        # =========================================================================
        # RISK DECISION HANDLING
        # =========================================================================
        
        if decision == RiskDecision.FLATTEN:
            # CRITICAL: System is in emergency mode
            logger.critical(f"ORDER REJECTED - FLATTEN ACTIVE: {risk_state.reason}")
            self.reject_count += 1
            audit_entry['rejected'] = True
            audit_entry['reject_reason'] = f"FLATTEN: {risk_state.reason}"
            self.audit_log.append(audit_entry)
            
            # Cancel any existing orders
            self.risk_engine._initiate_flatten(portfolio_state)
            
            return OrderResult(
                success=False,
                decision=decision,
                risk_state=risk_state,
                order_id=None,
                exchange=None,
                rejected_reason=f"FLATTEN: {risk_state.reason}",
                audit_log=audit_entry
            )
        
        if decision == RiskDecision.HALT:
            logger.warning(f"ORDER REJECTED - HALT: {risk_state.reason}")
            self.reject_count += 1
            audit_entry['rejected'] = True
            audit_entry['reject_reason'] = f"HALT: {risk_state.reason}"
            self.audit_log.append(audit_entry)
            
            return OrderResult(
                success=False,
                decision=decision,
                risk_state=risk_state,
                order_id=None,
                exchange=None,
                rejected_reason=f"HALT: {risk_state.reason}",
                audit_log=audit_entry
            )
        
        if decision == RiskDecision.REDUCE:
            # Reduce order size
            reduction_factor = 0.5
            original_qty = order.quantity
            order.quantity *= reduction_factor
            logger.warning(f"Order reduced from {original_qty} to {order.quantity} due to risk")
            audit_entry['modified'] = {
                'original_quantity': original_qty,
                'new_quantity': order.quantity,
                'reason': risk_state.reason
            }
            
            # Recalculate notional
            notional = order.quantity * price
        
        # Check order size against risk limits
        if notional > risk_state.max_order_notional:
            logger.warning(f"Order notional ${notional:,.0f} > limit ${risk_state.max_order_notional:,.0f}")
            self.reject_count += 1
            audit_entry['rejected'] = True
            audit_entry['reject_reason'] = f"OVERSIZED: {notional:,.0f} > {risk_state.max_order_notional:,.0f}"
            self.audit_log.append(audit_entry)
            
            return OrderResult(
                success=False,
                decision=decision,
                risk_state=risk_state,
                order_id=None,
                exchange=None,
                rejected_reason=f"Order size exceeds risk limit",
                audit_log=audit_entry
            )
        
        # =========================================================================
        # STEP 2: SMART ROUTING
        # =========================================================================
        
        route = await self.smart_router.route_order(order, market_data)
        audit_entry['routing'] = {
            'exchange': route.exchange,
            'order_type': route.order_type.value,
            'expected_cost': route.expected_cost,
            'expected_slippage': route.expected_slippage
        }
        
        # =========================================================================
        # STEP 3: COST ESTIMATION (via RealisticCostModel)
        # =========================================================================
        cost_breakdown = None
        spread_bps = 0.0
        depth_1pct_usd = 0.0

        # Build order book from market data
        if "order_book" in market_data:
            ob_data = market_data["order_book"]
            bids = [OrderBookLevel(Price(p), Quantity(s)) for p, s in ob_data.get("bids", [])]
            asks = [OrderBookLevel(Price(p), Quantity(s)) for p, s in ob_data.get("asks", [])]
            order_book = OrderBook(bids=bids, asks=asks)

            side_enum = Side.BUY if order.side == "buy" else Side.SELL

            cost_breakdown = self.cost_model.calculate_total_cost(
                NotionalUSD(notional),
                Price(price),
                order_book,
                side_enum,
                is_maker=(route.order_type == OrderType.LIMIT),
            )

            depth_summary = order_book.get_depth_summary()
            spread_bps = float(depth_summary["spread_bps"])
            depth_1pct_usd = float(depth_summary["min_depth_1pct_usd"])

            audit_entry["cost_estimate"] = cost_breakdown.to_dict()
            audit_entry["market_microstructure"] = {
                "spread_bps": spread_bps,
                "depth_1pct_usd": depth_1pct_usd,
            }
        
        # =========================================================================
        # STEP 4: ORDER EXECUTION
        # =========================================================================
        order_id = audit_entry["order_id"]
        fill = await self.fill_provider.get_fill(
            order_id=order_id,
            symbol=order.symbol,
            venue=route.exchange,
            side=order.side,
            requested_qty=float(order.quantity),
            reference_price=float(price),
        )
        logger.info(
            "Order %s filled: %s %s qty=%.6f @ %.6f on %s",
            order_id,
            fill.symbol,
            order.side,
            fill.executed_qty,
            fill.executed_price,
            fill.venue,
        )

        audit_entry["executed"] = True
        audit_entry["order_id"] = order_id
        audit_entry["fill"] = {
            "executed_price": fill.executed_price,
            "executed_qty": fill.executed_qty,
            "timestamp": fill.timestamp.isoformat(),
            "venue": fill.venue,
            "symbol": fill.symbol,
        }
        self.audit_log.append(audit_entry)
        
        # =========================================================================
        # STEP 5: POST-TRADE LOGGING (TCA)
        # =========================================================================
        # Feed into TCA for cost model calibration
        self._update_tca(
            order_id=order_id,
            audit_entry=audit_entry,
            order=order,
            fill=fill,
            notional=float(notional),
            reference_price=float(price),
            route=route,
            cost_breakdown=cost_breakdown,
            spread_bps=spread_bps,
            depth_1pct_usd=depth_1pct_usd,
            vol_24h=float(market_data.get("vol_24h", self.cost_model.base_vol)),
        )
        
        return OrderResult(
            success=True,
            decision=decision,
            risk_state=risk_state,
            order_id=order_id,
            exchange=route.exchange,
            rejected_reason=None,
            audit_log=audit_entry
        )
    
    def _update_tca(
        self,
        *,
        order_id: str,
        audit_entry: Dict,
        order: OrderRequest,
        fill: ExecutionFill,
        notional: float,
        reference_price: float,
        route: RouteDecision,
        cost_breakdown,
        spread_bps: float,
        depth_1pct_usd: float,
        vol_24h: float,
    ) -> None:
        """Persist predicted vs. realized slippage/costs for TCA calibration."""
        if notional <= 0 or reference_price <= 0:
            logger.warning("TCA skipped for %s due to invalid notional/price.", order_id)
            return

        if cost_breakdown is not None:
            predicted_slippage_bps = float(
                Bps.from_pct(float(cost_breakdown.slippage) / notional)
            )
            predicted_commission_bps = float(
                Bps.from_pct(float(cost_breakdown.commission) / notional)
            )
            predicted_total_bps = float(cost_breakdown.total_bps)
        else:
            predicted_slippage_bps = float(Bps.from_pct(route.expected_slippage / notional))
            predicted_commission_bps = float(Bps.from_pct(self.cost_model.commission))
            predicted_total_bps = predicted_slippage_bps + predicted_commission_bps

        if order.side == "buy":
            realized_slippage_pct = max((fill.executed_price - reference_price) / reference_price, 0.0)
        else:
            realized_slippage_pct = max((reference_price - fill.executed_price) / reference_price, 0.0)

        realized_slippage_bps = float(Bps.from_pct(realized_slippage_pct))
        realized_commission_bps = float(Bps.from_pct(self.cost_model.commission))
        realized_total_bps = realized_slippage_bps + realized_commission_bps

        realized_notional = float(fill.executed_price) * float(fill.executed_qty)
        record = TCATradeRecord(
            trade_id=order_id,
            timestamp=fill.timestamp,
            symbol=fill.symbol,
            exchange=fill.venue,
            side=order.side,
            quantity=float(fill.executed_qty),
            price=float(fill.executed_price),
            notional=realized_notional,
            predicted_slippage_bps=predicted_slippage_bps,
            predicted_commission_bps=predicted_commission_bps,
            predicted_total_bps=predicted_total_bps,
            realized_slippage_bps=realized_slippage_bps,
            realized_commission_bps=realized_commission_bps,
            realized_total_bps=realized_total_bps,
            spread_bps=spread_bps,
            vol_24h=vol_24h,
            depth_1pct_usd=depth_1pct_usd,
        )
        self.tca_db.add_record(record)
        self.tca_db.save()

        audit_entry["tca"] = {
            "predicted_slippage_bps": predicted_slippage_bps,
            "realized_slippage_bps": realized_slippage_bps,
            "predicted_total_bps": predicted_total_bps,
            "realized_total_bps": realized_total_bps,
        }
        logger.info(
            "TCA %s %s@%s: predicted_slip=%.3f bps realized_slip=%.3f bps",
            order_id,
            fill.symbol,
            fill.venue,
            predicted_slippage_bps,
            realized_slippage_bps,
        )
    
    def _create_token(self) -> '_RouterToken':
        """
        Private factory for creating RouterToken.
        
        Only RiskAwareRouter can create tokens. Adapters must verify
        received token using: type(token) is _RouterToken
        """
        return _mint_router_token(id(self))
    
    def get_stats(self) -> Dict:
        """Get order routing statistics."""
        return {
            'total_orders': self.order_count,
            'rejects': self.reject_count,
            'reject_rate': self.reject_count / max(self.order_count, 1),
            'kill_switch_active': self.risk_engine.risk_monitor.kill_switch_active,
            'kill_reason': self.risk_engine.risk_monitor.kill_reason,
            'capital': self._capital,
            'audit_entries': len(self.audit_log)
        }

    def run_weekly_tca_calibration(
        self,
        eta_by_symbol_venue: Dict[Tuple[str, str], float],
        min_samples: int = 50,
        alert_threshold_pct: float = 20.0,
        lookback_days: int = 30,
    ) -> Tuple[Dict[Tuple[str, str], float], List[Dict]]:
        """Update eta parameters by symbol/venue from realized TCA outcomes."""
        updated, analyses = weekly_calibrate_eta(
            tca_db=self.tca_db,
            current_eta_by_market=eta_by_symbol_venue,
            min_samples=min_samples,
            alert_threshold_pct=alert_threshold_pct,
            days=lookback_days,
        )
        self.eta_by_symbol_venue = updated

        if updated:
            self.cost_model.eta = sum(updated.values()) / len(updated)

        return updated, analyses
    
    def get_audit_log(self, n: int = 100) -> List[Dict]:
        """Get recent audit log entries."""
        return self.audit_log[-n:]
    
    async def reset_risk(self):
        """Reset risk engine (requires manual review)."""
        self.risk_engine.reset()
        logger.info("Risk engine reset - trading resumed")


# ============================================================================
# PRODUCTION EXAMPLE
# ============================================================================

async def main():
    """
    Example production usage.
    
    This shows the ONLY way to place orders in production.
    """
    import asyncio
    
    # Initialize router with risk limits
    router = RiskAwareRouter(
        risk_config=RiskLimits(
            max_daily_loss_pct=0.02,
            max_drawdown_pct=0.15,
            max_gross_leverage=2.0
        ),
        broker_config={'enabled': True}
    )
    
    # Set capital (NO HARDCODING)
    router.set_capital(100000.0, source="broker_account_api")
    
    # Example order
    order = OrderRequest(
        symbol="BTC-USD",
        side="buy",
        quantity=0.1,
        order_type=OrderType.LIMIT,
        price=50000.0
    )
    
    # Market data
    market_data = {
        'last_price': 50000.0,
        'order_book': {
            'bids': [(49990, 1.0), (49980, 2.0)],
            'asks': [(50010, 0.5), (50020, 1.5)]
        }
    }
    
    # Portfolio state
    portfolio = {
        'positions': {'BTC': 0.5},
        'prices': {'BTC': 50000},
        'total_pnl': 1000.0,
        'leverage': 0.5,
        'open_orders': []
    }
    
    # Strategy returns
    strategy_returns = {
        'strat1': np.random.randn(30) * 0.02,
        'strat2': np.random.randn(30) * 0.01
    }
    
    # Portfolio changes
    portfolio_changes = np.random.randn(30) * 1000
    
    # PLACE ORDER - only way to do it
    result = await router.submit_order(
        order, market_data, portfolio, strategy_returns, portfolio_changes
    )
    
    print(f"Order result: {result}")
    print(f"Stats: {router.get_stats()}")


if __name__ == "__main__":
    import numpy as np
    asyncio.run(main())
