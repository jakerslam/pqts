"""Venue execution-intelligence store and adaptive routing recommendation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from statistics import fmean
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ExecutionIntelligenceSample:
    venue: str
    strategy: str
    reject_rate: float
    slippage_bps: float
    cancel_replace_latency_ms: float
    queue_score: float
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionIntelligenceStore:
    samples: list[ExecutionIntelligenceSample] = field(default_factory=list)

    def add_sample(
        self,
        *,
        venue: str,
        strategy: str,
        reject_rate: float,
        slippage_bps: float,
        cancel_replace_latency_ms: float,
        queue_score: float,
    ) -> ExecutionIntelligenceSample:
        sample = ExecutionIntelligenceSample(
            venue=str(venue),
            strategy=str(strategy),
            reject_rate=float(reject_rate),
            slippage_bps=float(slippage_bps),
            cancel_replace_latency_ms=float(cancel_replace_latency_ms),
            queue_score=float(queue_score),
            timestamp=_utc_now_iso(),
        )
        self.samples.append(sample)
        return sample

    def summarize(self, venue: str) -> dict[str, Any]:
        rows = [row for row in self.samples if row.venue == venue]
        if not rows:
            return {
                "venue": venue,
                "count": 0,
                "reject_rate": 1.0,
                "slippage_bps": 9999.0,
                "cancel_replace_latency_ms": 9999.0,
                "queue_score": 0.0,
            }
        return {
            "venue": venue,
            "count": len(rows),
            "reject_rate": float(fmean([row.reject_rate for row in rows])),
            "slippage_bps": float(fmean([row.slippage_bps for row in rows])),
            "cancel_replace_latency_ms": float(
                fmean([row.cancel_replace_latency_ms for row in rows])
            ),
            "queue_score": float(fmean([row.queue_score for row in rows])),
        }


def recommend_route_from_intelligence(
    *,
    venue_summaries: list[dict[str, Any]],
    max_reject_rate: float,
) -> dict[str, Any]:
    candidates = [
        row
        for row in venue_summaries
        if float(row.get("reject_rate", 1.0)) <= float(max_reject_rate)
    ]
    if not candidates:
        return {"recommended_venue": "", "reason": "no_candidate_within_reject_rate_bound"}
    ranked = sorted(
        candidates,
        key=lambda row: (
            float(row.get("reject_rate", 1.0)),
            float(row.get("slippage_bps", 9999.0)),
            float(row.get("cancel_replace_latency_ms", 9999.0)),
            -float(row.get("queue_score", 0.0)),
        ),
    )
    top = ranked[0]
    return {"recommended_venue": str(top.get("venue", "")), "reason": "best_execution_profile"}
