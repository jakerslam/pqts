from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from execution.copy_follow_state import CopyEventWatermarkStore, CopyFollowIdentityResolver


def test_identity_resolution_rejects_ambiguous_and_detects_identity_drift() -> None:
    resolver = CopyFollowIdentityResolver(ambiguity_margin=0.03, min_confidence=0.70)
    with pytest.raises(RuntimeError):
        resolver.resolve(
            handle="@alpha",
            candidates=[("0xabc", 0.78), ("0xdef", 0.76)],
            evidence_source="profile_page",
        )

    record = resolver.resolve(
        handle="@alpha",
        candidates=[("0xabc", 0.84), ("0xdef", 0.50)],
        evidence_source="profile_page",
        resolved_at="2026-03-18T00:00:00+00:00",
        validity_window_seconds=3600,
    )
    assert record.execution_identity == "0xabc"

    ok, reason = resolver.require_stable_identity(
        handle="@alpha",
        proposed_identity="0xabc",
        now_ts="2026-03-18T00:10:00+00:00",
    )
    assert ok is True
    assert reason == "ok"

    changed_ok, changed_reason = resolver.require_stable_identity(
        handle="@alpha",
        proposed_identity="0x999",
        now_ts="2026-03-18T00:15:00+00:00",
    )
    assert changed_ok is False
    assert changed_reason == "identity_changed_requires_reapproval"


def test_restart_safe_watermark_persists_and_blocks_on_corruption(tmp_path: Path) -> None:
    state_path = tmp_path / "watermark_state.json"
    store = CopyEventWatermarkStore(path=state_path, max_events=100, max_age_seconds=3600)
    now_iso = datetime.now(timezone.utc).isoformat()

    key = store.event_key(
        source_venue="polymarket",
        source_identity="0xabc",
        tx_hash="0xtx",
        asset="asset_1",
        side="BUY",
        event_timestamp=now_iso,
    )
    assert store.has_event(event_key=key) is False
    store.record_event(event_key=key, recorded_at=now_iso)
    assert store.has_event(event_key=key) is True

    restarted = CopyEventWatermarkStore(path=state_path, max_events=100, max_age_seconds=3600)
    assert restarted.can_trade() is True
    assert restarted.has_event(event_key=key) is True

    state_path.write_text("{ this-is-not-json", encoding="utf-8")
    broken = CopyEventWatermarkStore(path=state_path, max_events=100, max_age_seconds=3600)
    ok, reason = broken.integrity_status()
    assert ok is False
    assert reason == "watermark_state_corrupt"
    with pytest.raises(RuntimeError):
        broken.record_event(event_key=key)
