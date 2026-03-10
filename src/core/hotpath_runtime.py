"""Runtime bridge for optional native hot-path kernels with safe Python fallback."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Iterable


def _to_level_tuple(level: Any) -> tuple[float, float]:
    if not isinstance(level, (list, tuple)) or len(level) < 2:
        return 0.0, 0.0
    try:
        price = float(level[0])
        size = float(level[1])
    except (TypeError, ValueError):
        return 0.0, 0.0
    return max(price, 0.0), max(size, 0.0)


def _normalize_levels(levels: Iterable[Any], *, max_levels: int) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    max_rows = max(int(max_levels), 1)
    for level in levels:
        if len(out) >= max_rows:
            break
        out.append(_to_level_tuple(level))
    return out


@lru_cache(maxsize=1)
def _load_native_module() -> Any | None:
    env = os.getenv("PQTS_NATIVE_HOTPATH", "").strip().lower()
    if env in {"0", "false", "off", "no"}:
        return None
    try:
        import pqts_hotpath as module  # type: ignore
    except Exception:
        return None
    if not hasattr(module, "sum_notional"):
        return None
    return module


def native_available() -> bool:
    return _load_native_module() is not None


def sum_notional(levels: Iterable[Any], *, max_levels: int = 5) -> float:
    normalized = _normalize_levels(levels, max_levels=max_levels)
    module = _load_native_module()
    if module is not None:
        try:
            return float(module.sum_notional(normalized, int(max(int(max_levels), 1))))
        except Exception:
            pass
    total = 0.0
    for price, size in normalized:
        total += price * size
    return float(total)
