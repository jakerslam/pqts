from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from tools.check_native_latency_regression import evaluate_native_latency


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_native_latency_regression_passes_with_recent_artifacts(tmp_path: Path) -> None:
    results = tmp_path / "bench"
    results.mkdir(parents=True, exist_ok=True)
    now = datetime(2026, 3, 10, tzinfo=timezone.utc)
    _write(
        results / "execution_latency_benchmark_a.json",
        {
            "timestamp_utc": "2026-03-09T12:00:00+00:00",
            "environment": {"native_available": False},
            "result": {"latency_ms": {"p95": 40.0}},
        },
    )
    _write(
        results / "execution_latency_benchmark_b.json",
        {
            "timestamp_utc": "2026-03-09T12:05:00+00:00",
            "environment": {"native_available": True},
            "result": {"latency_ms": {"p95": 14.0}},
        },
    )
    policy = _write(
        tmp_path / "policy.json",
        {"max_native_p95_ms": 25.0, "min_speedup_vs_fallback": 1.5, "max_artifact_age_days": 30},
    )

    errors, summary = evaluate_native_latency(results_dir=results, policy_path=policy, now=now)
    assert errors == []
    assert summary["validated"] is True


def test_native_latency_regression_flags_speedup_and_age_violations(tmp_path: Path) -> None:
    results = tmp_path / "bench"
    results.mkdir(parents=True, exist_ok=True)
    now = datetime(2026, 3, 10, tzinfo=timezone.utc)
    _write(
        results / "execution_latency_benchmark_old_fallback.json",
        {
            "timestamp_utc": "2025-01-01T12:00:00+00:00",
            "environment": {"native_available": False},
            "result": {"latency_ms": {"p95": 22.0}},
        },
    )
    _write(
        results / "execution_latency_benchmark_old_native.json",
        {
            "timestamp_utc": "2025-01-01T12:05:00+00:00",
            "environment": {"native_available": True},
            "result": {"latency_ms": {"p95": 20.0}},
        },
    )
    policy = _write(
        tmp_path / "policy.json",
        {"max_native_p95_ms": 18.0, "min_speedup_vs_fallback": 2.0, "max_artifact_age_days": 10},
    )

    errors, summary = evaluate_native_latency(results_dir=results, policy_path=policy, now=now)
    assert summary["validated"] is False
    assert any("exceeds policy" in item for item in errors)
    assert any("below policy minimum" in item for item in errors)
    assert any("too old" in item for item in errors)
