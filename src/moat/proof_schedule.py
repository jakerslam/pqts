"""Scheduling helpers for proof-as-product artifact publication."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class ProofSchedulePolicy:
    cadence_hours: int = 24


def schedule_due(*, last_run_at: str | None, now: datetime, policy: ProofSchedulePolicy) -> bool:
    if last_run_at is None or not str(last_run_at).strip():
        return True
    last = datetime.fromisoformat(str(last_run_at).replace("Z", "+00:00"))
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return now >= (last + timedelta(hours=int(policy.cadence_hours)))
