"""Copy-trade signal safety envelope with canonical router-only execution path."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol

from execution.smart_router import OrderRequest, OrderType


class RouterSubmitProtocol(Protocol):
    async def submit_order(self, order: OrderRequest, market_data: dict, portfolio: dict, **kwargs: Any) -> Any:
        ...


@dataclass(frozen=True)
class CopyTradeSignal:
    leader_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    strategy_id: str = "copytrade_follow"
    expected_alpha_bps: float = 0.0


@dataclass(frozen=True)
class CopyTradePolicy:
    allowed_leaders: tuple[str, ...]
    max_signal_notional_usd: float = 1_000.0
    max_total_follow_notional_usd: float = 10_000.0
    drawdown_kill_switch_pct: float = 0.15
    require_allowlist: bool = True


@dataclass(frozen=True)
class CopyTradeDecision:
    accepted: bool
    notional_usd: float
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CopyTradeSafetyEnvelope:
    """Validate and optionally submit copy-trade follow signals."""

    def __init__(self, policy: CopyTradePolicy) -> None:
        self.policy = policy
        self._follow_notional_by_leader: dict[str, float] = {}

    def evaluate(
        self,
        *,
        signal: CopyTradeSignal,
        current_drawdown_pct: float,
        kill_switch_active: bool,
    ) -> CopyTradeDecision:
        reason_codes: list[str] = []
        leader = str(signal.leader_id).strip().lower()
        if self.policy.require_allowlist and leader not in {
            str(item).strip().lower() for item in self.policy.allowed_leaders
        }:
            reason_codes.append("leader_not_allowlisted")

        notional = abs(float(signal.quantity) * float(signal.price))
        if notional > float(self.policy.max_signal_notional_usd):
            reason_codes.append("signal_notional_limit_exceeded")

        aggregate = float(self._follow_notional_by_leader.get(leader, 0.0)) + notional
        if aggregate > float(self.policy.max_total_follow_notional_usd):
            reason_codes.append("leader_follow_budget_exceeded")

        if bool(kill_switch_active):
            reason_codes.append("kill_switch_active")
        if float(current_drawdown_pct) >= float(self.policy.drawdown_kill_switch_pct):
            reason_codes.append("drawdown_kill_switch_triggered")

        return CopyTradeDecision(
            accepted=not reason_codes,
            notional_usd=notional,
            reason_codes=tuple(reason_codes),
        )

    async def submit_follow_signal(
        self,
        *,
        router: RouterSubmitProtocol,
        signal: CopyTradeSignal,
        market_data: dict,
        portfolio: dict,
        current_drawdown_pct: float,
        kill_switch_active: bool,
    ) -> tuple[CopyTradeDecision, Any | None]:
        decision = self.evaluate(
            signal=signal,
            current_drawdown_pct=current_drawdown_pct,
            kill_switch_active=kill_switch_active,
        )
        if not decision.accepted:
            return decision, None

        order = OrderRequest(
            symbol=str(signal.symbol),
            side=str(signal.side),
            quantity=float(signal.quantity),
            order_type=OrderType.LIMIT,
            price=float(signal.price),
            strategy_id=str(signal.strategy_id),
            expected_alpha_bps=float(signal.expected_alpha_bps),
            client_order_id=f"copytrade_{signal.leader_id}_{signal.symbol}",
            decision_context={
                "copytrade_leader_id": str(signal.leader_id),
                "copytrade_notional_usd": float(decision.notional_usd),
            },
        )
        result = await router.submit_order(order=order, market_data=market_data, portfolio=portfolio)
        if bool(getattr(result, "success", False)):
            leader = str(signal.leader_id).strip().lower()
            self._follow_notional_by_leader[leader] = (
                float(self._follow_notional_by_leader.get(leader, 0.0)) + float(decision.notional_usd)
            )
        return decision, result
