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
