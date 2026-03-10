"""Live-vs-expected divergence classification and prescriptive actioning."""

from __future__ import annotations

from typing import Any


def classify_divergence(
    *,
    expected_fill_rate: float,
    actual_fill_rate: float,
    expected_latency_ms: float,
    actual_latency_ms: float,
    reject_rate: float,
) -> dict[str, Any]:
    expected_fill = float(expected_fill_rate)
    actual_fill = float(actual_fill_rate)
    latency_expected = float(expected_latency_ms)
    latency_actual = float(actual_latency_ms)
    rejects = float(reject_rate)

    if rejects >= 0.5:
        reason = "venue_reject"
        action = "reroute"
        confidence = 0.9
    elif latency_actual > max(latency_expected * 1.5, latency_expected + 50.0):
        reason = "latency_breach"
        action = "hold_canary"
        confidence = 0.8
    elif actual_fill < max(expected_fill * 0.7, expected_fill - 0.2):
        reason = "liquidity_miss"
        action = "resize"
        confidence = 0.75
    else:
        reason = "nominal"
        action = "continue"
        confidence = 0.7

    return {
        "reason": reason,
        "recommended_action": action,
        "confidence": float(confidence),
        "metrics": {
            "expected_fill_rate": expected_fill,
            "actual_fill_rate": actual_fill,
            "expected_latency_ms": latency_expected,
            "actual_latency_ms": latency_actual,
            "reject_rate": rejects,
        },
    }
