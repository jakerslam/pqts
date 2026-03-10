from __future__ import annotations

from core.trace_context import ensure_trace_fields, new_trace_id


def test_new_trace_id_prefix() -> None:
    trace_id = new_trace_id("order", 123)
    assert trace_id.startswith("trc_")
    assert len(trace_id) > 8


def test_ensure_trace_fields_sets_defaults() -> None:
    payload: dict[str, object] = {"order_id": "ord_1"}
    resolved = ensure_trace_fields(payload)
    assert resolved == payload["trace_id"]
    assert str(payload["trace_timestamp"]).strip()


def test_ensure_trace_fields_respects_explicit_trace_id() -> None:
    payload: dict[str, object] = {"order_id": "ord_2"}
    resolved = ensure_trace_fields(payload, trace_id="trc_custom")
    assert resolved == "trc_custom"
    assert payload["trace_id"] == "trc_custom"

