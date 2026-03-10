from __future__ import annotations

import sys

import pytest

from core import hotpath_runtime


class _NativeStub:
    @staticmethod
    def sum_notional(levels, max_levels):
        total = 0.0
        for idx, (price, size) in enumerate(levels):
            if idx >= max_levels:
                break
            total += (price * size) + 1.0
        return total

    @staticmethod
    def fill_metrics(side, reference_price, executed_price, requested_qty, executed_qty):
        _ = side
        _ = reference_price
        _ = executed_price
        _ = requested_qty
        _ = executed_qty
        return 7.0, 0.7

    @staticmethod
    def sequence_transition(expected_sequence, received_sequence, allow_auto_recover, snapshot_sequence):
        _ = expected_sequence
        _ = received_sequence
        _ = allow_auto_recover
        _ = snapshot_sequence
        return "native_mode", 42, 3, True, 100, 101

    @staticmethod
    def uniform_from_seed(seed):
        _ = seed
        return 0.123

    @staticmethod
    def event_id_hash(prefix, payload, hex_len):
        _ = payload
        _ = hex_len
        return f"{prefix}_nativehash"

    @staticmethod
    def paper_fill_metrics(
        side,
        requested_qty,
        reference_price,
        queue_qty,
        partial_fill_notional_usd,
        min_partial_fill_ratio,
        queue_penalty_floor,
        adverse_selection_bps,
        min_slippage_bps,
        queue_slippage_bps_per_turnover,
        reality_stress_mode,
        stress_fill_ratio_multiplier,
        stress_slippage_multiplier,
        fill_uniform,
        slippage_uniform,
    ):
        _ = (
            side,
            requested_qty,
            reference_price,
            queue_qty,
            partial_fill_notional_usd,
            min_partial_fill_ratio,
            queue_penalty_floor,
            adverse_selection_bps,
            min_slippage_bps,
            queue_slippage_bps_per_turnover,
            reality_stress_mode,
            stress_fill_ratio_multiplier,
            stress_slippage_multiplier,
            fill_uniform,
            slippage_uniform,
        )
        return 0.5, 2.5, 1.0, 101.0, 0.2

    @staticmethod
    def smart_router_score(spread, volume_24h, fee_bps, slippage_ratio, fill_ratio, latency_ms):
        _ = (spread, volume_24h, fee_bps, slippage_ratio, fill_ratio, latency_ms)
        return 0.88

    @staticmethod
    def quote_state(price, age_seconds, stale_after_seconds):
        _ = (price, age_seconds, stale_after_seconds)
        return True, False


class _IncompleteNativeStub:
    @staticmethod
    def sum_notional(levels, max_levels):
        _ = levels
        _ = max_levels
        return 0.0


def test_sum_notional_uses_python_fallback_when_native_missing(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: None)
    value = hotpath_runtime.sum_notional([(100.0, 2.0), (99.0, 3.0)], max_levels=2)
    assert value == 100.0 * 2.0 + 99.0 * 3.0


def test_sum_notional_uses_native_module_when_available(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: _NativeStub())
    value = hotpath_runtime.sum_notional([(100.0, 2.0), (99.0, 3.0)], max_levels=2)
    assert value == (100.0 * 2.0 + 1.0) + (99.0 * 3.0 + 1.0)


def test_fill_metrics_uses_python_fallback_when_native_missing(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: None)
    slippage_bps, fill_ratio = hotpath_runtime.fill_metrics(
        side="buy",
        reference_price=100.0,
        executed_price=100.2,
        requested_qty=2.0,
        executed_qty=1.0,
    )
    assert slippage_bps == pytest.approx(20.0)
    assert fill_ratio == 0.5


def test_fill_metrics_uses_native_module_when_available(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: _NativeStub())
    slippage_bps, fill_ratio = hotpath_runtime.fill_metrics(
        side="sell",
        reference_price=100.0,
        executed_price=99.9,
        requested_qty=2.0,
        executed_qty=1.0,
    )
    assert slippage_bps == 7.0
    assert fill_ratio == 0.7


def test_sequence_transition_uses_python_fallback_when_native_missing(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: None)
    mode, event_expected, gap_size, recovered, snap_seq, next_expected = (
        hotpath_runtime.sequence_transition(
            expected_sequence=10,
            received_sequence=13,
            allow_auto_recover=True,
            snapshot_sequence=20,
        )
    )
    assert mode == "gap_recovered_snapshot"
    assert event_expected == 10
    assert gap_size == 3
    assert recovered is True
    assert snap_seq == 20
    assert next_expected == 21


def test_sequence_transition_uses_native_module_when_available(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: _NativeStub())
    mode, event_expected, gap_size, recovered, snap_seq, next_expected = (
        hotpath_runtime.sequence_transition(
            expected_sequence=10,
            received_sequence=13,
            allow_auto_recover=True,
            snapshot_sequence=20,
        )
    )
    assert mode == "native_mode"
    assert event_expected == 42
    assert gap_size == 3
    assert recovered is True
    assert snap_seq == 100
    assert next_expected == 101


def test_loader_rejects_native_module_missing_required_symbols(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.delenv("PQTS_NATIVE_HOTPATH", raising=False)
    monkeypatch.setitem(sys.modules, "pqts_hotpath", _IncompleteNativeStub())
    assert hotpath_runtime._load_native_module() is None


def test_uniform_from_seed_uses_python_fallback_when_native_missing(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: None)
    value = hotpath_runtime.uniform_from_seed("seed")
    assert 0.0 <= value <= 1.0


def test_uniform_from_seed_uses_native_module_when_available(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: _NativeStub())
    assert hotpath_runtime.uniform_from_seed("seed") == 0.123


def test_event_id_uses_python_fallback_when_native_missing(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: None)
    event_id = hotpath_runtime.event_id("ws", ("a", 1), hex_len=12)
    assert event_id.startswith("ws_")
    assert len(event_id.split("_", maxsplit=1)[1]) == 12


def test_event_id_uses_native_module_when_available(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: _NativeStub())
    assert hotpath_runtime.event_id("ws", ("a", 1), hex_len=12) == "ws_nativehash"


def test_paper_fill_metrics_uses_native_module_when_available(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: _NativeStub())
    fill_ratio, slip_bps, executed_qty, executed_price, queue_turnover = hotpath_runtime.paper_fill_metrics(
        side="buy",
        requested_qty=2.0,
        reference_price=100.0,
        queue_qty=1.0,
        partial_fill_notional_usd=1000.0,
        min_partial_fill_ratio=0.5,
        queue_penalty_floor=0.2,
        adverse_selection_bps=2.0,
        min_slippage_bps=1.0,
        queue_slippage_bps_per_turnover=0.1,
        reality_stress_mode=False,
        stress_fill_ratio_multiplier=0.7,
        stress_slippage_multiplier=2.5,
        fill_uniform=0.5,
        slippage_uniform=0.5,
    )
    assert (fill_ratio, slip_bps, executed_qty, executed_price, queue_turnover) == (
        0.5,
        2.5,
        1.0,
        101.0,
        0.2,
    )


def test_smart_router_score_uses_native_module_when_available(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: _NativeStub())
    score = hotpath_runtime.smart_router_score(
        spread=0.001,
        volume_24h=1_000_000.0,
        fee_bps=5.0,
        slippage_ratio=1.1,
        fill_ratio=0.9,
        latency_ms=20.0,
    )
    assert score == 0.88


def test_quote_state_uses_native_module_when_available(monkeypatch) -> None:
    hotpath_runtime._load_native_module.cache_clear()
    monkeypatch.setattr(hotpath_runtime, "_load_native_module", lambda: _NativeStub())
    stale, usable = hotpath_runtime.quote_state(price=100.0, age_seconds=3.0, stale_after_seconds=1.0)
    assert stale is True
    assert usable is False
