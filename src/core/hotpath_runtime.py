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


def fill_metrics(
    *,
    side: str,
    reference_price: float,
    executed_price: float,
    requested_qty: float,
    executed_qty: float,
) -> tuple[float, float]:
    side_token = str(side).lower()
    ref = float(reference_price)
    exe = float(executed_price)
    req = float(requested_qty)
    filled = float(executed_qty)
    module = _load_native_module()
    if module is not None and hasattr(module, "fill_metrics"):
        try:
            slippage_bps, fill_ratio = module.fill_metrics(side_token, ref, exe, req, filled)
            return float(slippage_bps), float(fill_ratio)
        except Exception:
            pass

    ref_denom = max(ref, 1e-12)
    if side_token == "buy":
        slip_pct = max((exe - ref) / ref_denom, 0.0)
    else:
        slip_pct = max((ref - exe) / ref_denom, 0.0)
    slippage_bps = float(slip_pct * 10000.0)
    fill_ratio = float(filled / max(req, 1e-12))
    return slippage_bps, fill_ratio


def sequence_transition(
    *,
    expected_sequence: int | None,
    received_sequence: int,
    allow_auto_recover: bool,
    snapshot_sequence: int | None,
) -> tuple[str, int, int, bool, int | None, int]:
    expected = int(expected_sequence) if expected_sequence is not None else None
    received = int(received_sequence)
    snapshot = int(snapshot_sequence) if snapshot_sequence is not None else None
    can_recover = bool(allow_auto_recover)

    module = _load_native_module()
    if module is not None and hasattr(module, "sequence_transition"):
        try:
            mode, event_expected, gap_size, recovered, applied_snapshot, next_expected = (
                module.sequence_transition(expected, received, can_recover, snapshot)
            )
            return (
                str(mode),
                int(event_expected),
                int(gap_size),
                bool(recovered),
                int(applied_snapshot) if applied_snapshot is not None else None,
                int(next_expected),
            )
        except Exception:
            pass

    if expected is None:
        next_expected = received + 1
        return "seed", next_expected, 0, False, None, next_expected
    if received < expected:
        return "stale_drop", expected, 0, False, None, expected
    if received == expected:
        return "in_order", expected, 0, False, None, received + 1
    gap_size = received - expected
    if can_recover and snapshot is not None:
        return "gap_recovered_snapshot", expected, gap_size, True, snapshot, snapshot + 1
    return "gap_detected", expected, gap_size, False, None, expected
