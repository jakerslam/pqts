"""Durable event-stream backbone with deterministic replay support."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class DurableEvent:
    sequence: int
    event_id: str
    category: str
    timestamp: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DurableEventStreamBackbone:
    """Append-only JSONL event stream with category/time/sequence replay filters."""

    def __init__(self, *, events_path: str = "data/analytics/durable_event_stream.jsonl") -> None:
        self.events_path = Path(events_path)
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        self._next_sequence = self._load_next_sequence()

    def _load_next_sequence(self) -> int:
        if not self.events_path.exists():
            return 1
        last_sequence = 0
        with self.events_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                last_sequence = max(last_sequence, int(row.get("sequence", 0) or 0))
        return last_sequence + 1

    def append(
        self,
        *,
        event_id: str,
        category: str,
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> DurableEvent:
        event = DurableEvent(
            sequence=self._next_sequence,
            event_id=str(event_id),
            category=str(category),
            timestamp=str(timestamp or _utc_now_iso()),
            payload=dict(payload or {}),
        )
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
        self._next_sequence += 1
        return event

    def replay(
        self,
        *,
        category: str | None = None,
        since_sequence: int = 0,
        until_sequence: int | None = None,
        limit: int = 1000,
    ) -> list[DurableEvent]:
        cap = max(int(limit), 1)
        since = max(int(since_sequence), 0)
        until = int(until_sequence) if until_sequence is not None else None
        out: list[DurableEvent] = []
        if not self.events_path.exists():
            return out

        with self.events_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sequence = int(row.get("sequence", 0) or 0)
                if sequence <= since:
                    continue
                if until is not None and sequence > until:
                    continue
                if category is not None and str(row.get("category", "")) != str(category):
                    continue
                out.append(
                    DurableEvent(
                        sequence=sequence,
                        event_id=str(row.get("event_id", "")),
                        category=str(row.get("category", "")),
                        timestamp=str(row.get("timestamp", "")),
                        payload=dict(row.get("payload", {}) or {}),
                    )
                )
                if len(out) >= cap:
                    break
        return out
