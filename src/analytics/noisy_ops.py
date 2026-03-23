"""No-code dislocation scanner and bot-ops telemetry helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class DislocationCandidate:
    market_id: str
    edge: float
    ev: float
    liquidity: float
    gate_outcome: str


def build_dislocation_candidates(
    rows: Iterable[Mapping[str, Any]],
    *,
    min_ev: float = 0.0,
    min_liquidity: float = 50.0,
) -> list[DislocationCandidate]:
    candidates: list[DislocationCandidate] = []
    for row in rows:
        edge = float(row.get("edge", 0.0))
        ev = float(row.get("ev", 0.0))
        liquidity = float(row.get("liquidity", 0.0))
        gate = "allow" if ev > min_ev and liquidity >= min_liquidity else "block"
        candidates.append(
            DislocationCandidate(
                market_id=str(row.get("market_id", "")),
                edge=edge,
                ev=ev,
                liquidity=liquidity,
                gate_outcome=gate,
            )
        )
    return candidates


@dataclass(frozen=True)
class BotTelemetry:
    pnl: float
    trades: int
    markets: int
    state: str


def summarize_bot_ops(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows_list = list(rows)
    total_pnl = sum(float(row.get("pnl", 0.0)) for row in rows_list)
    total_trades = sum(int(row.get("trades", 0)) for row in rows_list)
    unique_markets = len({row.get("market_id") for row in rows_list})
    return {
        "total_pnl": float(total_pnl),
        "total_trades": int(total_trades),
        "markets": int(unique_markets),
        "bots": int(len(rows_list)),
    }


@dataclass(frozen=True)
class WalletSafetyResult:
    mode: str
    allowed: bool
    reason: str


def wallet_boundary_check(*, custody_enabled: bool, verification_ok: bool) -> WalletSafetyResult:
    if not custody_enabled:
        return WalletSafetyResult(mode="non_custodial", allowed=verification_ok, reason="non_custodial_policy")
    return WalletSafetyResult(mode="custodial", allowed=verification_ok, reason="custody_policy")
