"""Orderbook sequence-gap detection with deterministic recovery workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from core.hotpath_runtime import sequence_transition


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SequenceEvent:
    stream_id: str
    expected_sequence: int
    received_sequence: int
    mode: str
    gap_size: int
    recovered: bool
    snapshot_sequence: int | None
    timestamp: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OrderBookSequenceTracker:
    """Track per-stream sequence integrity and perform deterministic recovery."""

    def __init__(self, *, allow_auto_recover: bool = True) -> None:
        self.allow_auto_recover = bool(allow_auto_recover)
        self._expected_next: dict[str, int] = {}
        self._gap_open: dict[str, bool] = {}

    def expected_next(self, stream_id: str) -> int | None:
        return self._expected_next.get(str(stream_id))

    def apply_snapshot(self, *, stream_id: str, snapshot_sequence: int) -> SequenceEvent:
        key = str(stream_id)
        next_seq = int(snapshot_sequence) + 1
        self._expected_next[key] = next_seq
        self._gap_open[key] = False
        return SequenceEvent(
            stream_id=key,
            expected_sequence=next_seq,
            received_sequence=int(snapshot_sequence),
            mode="snapshot_sync",
            gap_size=0,
            recovered=True,
            snapshot_sequence=int(snapshot_sequence),
            timestamp=_utc_now_iso(),
            metadata={},
        )

    def process_update(
        self,
        *,
        stream_id: str,
        sequence: int,
        snapshot_sequence: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SequenceEvent:
        key = str(stream_id)
        seq = int(sequence)
        info = dict(metadata or {})
        mode, event_expected, gap_size, recovered, snap_seq, next_expected = sequence_transition(
            expected_sequence=self._expected_next.get(key),
            received_sequence=seq,
            allow_auto_recover=self.allow_auto_recover,
            snapshot_sequence=snapshot_sequence,
        )

        if mode in {"seed", "in_order", "gap_recovered_snapshot"}:
            self._expected_next[key] = int(next_expected)
            self._gap_open[key] = False
        elif mode == "gap_detected":
            self._gap_open[key] = True

        return SequenceEvent(
            stream_id=key,
            expected_sequence=int(event_expected),
            received_sequence=seq,
            mode=mode,
            gap_size=int(gap_size),
            recovered=bool(recovered),
            snapshot_sequence=snap_seq,
            timestamp=_utc_now_iso(),
            metadata=info,
        )

    def has_open_gap(self, stream_id: str) -> bool:
        return bool(self._gap_open.get(str(stream_id), False))
