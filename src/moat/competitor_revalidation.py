"""Competitor-source freshness checks for periodic revalidation workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class CompetitorSource:
    name: str
    url: str
    last_validated: str  # YYYY-MM-DD


def evaluate_source_freshness(
    *,
    sources: list[CompetitorSource],
    today: date,
    max_age_days: int,
) -> dict[str, Any]:
    stale: list[str] = []
    for source in sources:
        token = date.fromisoformat(source.last_validated)
        age = (today - token).days
        if age > int(max_age_days):
            stale.append(source.name)
    return {"passed": len(stale) == 0, "stale_sources": stale}
