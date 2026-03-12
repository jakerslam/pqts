"""Decision explainability card contracts and persistence helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class DecisionExplainabilityCard:
    card_id: str
    strategy_id: str
    market_id: str
    generated_at: str
    p_market: float
    p_model: float
    posterior_before: float
    posterior_after: float
    posterior_delta: float
    gross_edge_bps: float
    total_penalty_bps: float
    net_edge_bps: float
    expected_value_bps: float
    full_kelly_fraction: float
    approved_fraction: float
    stage: str
    gate_passed: bool
    gate_reason_codes: tuple[str, ...]
    trust_label: str = "unverified"
    evidence_source: str = ""
    evidence_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["gate_reason_codes"] = list(self.gate_reason_codes)
        return payload


def build_decision_card(
    *,
    card_id: str,
    strategy_id: str,
    market_id: str,
    p_market: float,
    p_model: float,
    posterior_before: float,
    posterior_after: float,
    gross_edge_bps: float,
    total_penalty_bps: float,
    net_edge_bps: float,
    expected_value_bps: float,
    full_kelly_fraction: float,
    approved_fraction: float,
    stage: str,
    gate_passed: bool,
    gate_reason_codes: list[str] | tuple[str, ...],
    trust_label: str = "unverified",
    evidence_source: str = "",
    evidence_ref: str = "",
    generated_at: str | None = None,
) -> DecisionExplainabilityCard:
    posterior_before = float(posterior_before)
    posterior_after = float(posterior_after)
    return DecisionExplainabilityCard(
        card_id=str(card_id),
        strategy_id=str(strategy_id),
        market_id=str(market_id),
        generated_at=str(generated_at or _utc_now_iso()),
        p_market=float(p_market),
        p_model=float(p_model),
        posterior_before=posterior_before,
        posterior_after=posterior_after,
        posterior_delta=posterior_after - posterior_before,
        gross_edge_bps=float(gross_edge_bps),
        total_penalty_bps=float(total_penalty_bps),
        net_edge_bps=float(net_edge_bps),
        expected_value_bps=float(expected_value_bps),
        full_kelly_fraction=float(full_kelly_fraction),
        approved_fraction=float(approved_fraction),
        stage=str(stage),
        gate_passed=bool(gate_passed),
        gate_reason_codes=tuple(str(item) for item in gate_reason_codes),
        trust_label=str(trust_label),
        evidence_source=str(evidence_source),
        evidence_ref=str(evidence_ref),
    )


def persist_decision_card(card: DecisionExplainabilityCard, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(card.to_dict(), sort_keys=True) + "\n")
    return target


def load_decision_cards(path: str | Path, *, limit: int = 100) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    cards: list[dict[str, Any]] = []
    for raw in reversed(target.read_text(encoding="utf-8").splitlines()):
        line = raw.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(parsed, dict):
            cards.append(parsed)
        if len(cards) >= max(1, int(limit)):
            break
    cards.reverse()
    return cards
