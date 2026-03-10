from __future__ import annotations

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
