"""Tests for durable event-stream backbone and replay semantics."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytics.event_stream_backbone import DurableEventStreamBackbone


def test_backbone_appends_and_replays_by_sequence(tmp_path: Path) -> None:
    stream = DurableEventStreamBackbone(events_path=str(tmp_path / "events.jsonl"))
    stream.append(event_id="evt_1", category="orders", payload={"side": "buy"})
    stream.append(event_id="evt_2", category="fills", payload={"qty": 1})
    stream.append(event_id="evt_3", category="orders", payload={"side": "sell"})

    rows = stream.replay(since_sequence=1)
    assert [row.event_id for row in rows] == ["evt_2", "evt_3"]


def test_backbone_replay_filters_category_and_limit(tmp_path: Path) -> None:
    stream = DurableEventStreamBackbone(events_path=str(tmp_path / "events.jsonl"))
    for idx in range(5):
        stream.append(event_id=f"ord_{idx}", category="orders", payload={"i": idx})
        stream.append(event_id=f"fill_{idx}", category="fills", payload={"i": idx})

    rows = stream.replay(category="fills", limit=3)
    assert len(rows) == 3
    assert all(row.category == "fills" for row in rows)


def test_backbone_sequence_persists_across_restarts(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    first = DurableEventStreamBackbone(events_path=str(path))
    first.append(event_id="evt_1", category="ops")
    first.append(event_id="evt_2", category="ops")

    second = DurableEventStreamBackbone(events_path=str(path))
    event = second.append(event_id="evt_3", category="ops")
    assert event.sequence == 3
