#!/usr/bin/env python3
"""Gate native hotpath latency regressions using committed benchmark artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BenchmarkArtifact:
    path: Path
    timestamp: datetime
    native_available: bool
    p95_ms: float


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _parse_iso(value: str) -> datetime:
    token = str(value).strip()
    if token.endswith("Z"):
        token = token.replace("Z", "+00:00")
    dt = datetime.fromisoformat(token)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _collect_artifacts(results_dir: Path) -> list[BenchmarkArtifact]:
    artifacts: list[BenchmarkArtifact] = []
    for path in sorted(results_dir.glob("execution_latency_benchmark_*.json")):
        payload = _load_json(path)
        env = dict(payload.get("environment") or {})
        result = dict(payload.get("result") or {})
        lat = dict(result.get("latency_ms") or {})
        timestamp = _parse_iso(str(payload.get("timestamp_utc", "")))
        artifacts.append(
            BenchmarkArtifact(
                path=path,
                timestamp=timestamp,
                native_available=bool(env.get("native_available", False)),
                p95_ms=float(lat.get("p95", 0.0)),
            )
        )
    return artifacts


def evaluate_native_latency(
    *,
    results_dir: Path,
    policy_path: Path,
    now: datetime | None = None,
) -> tuple[list[str], dict[str, Any]]:
    policy = _load_json(policy_path)
    artifacts = _collect_artifacts(results_dir)
    errors: list[str] = []

    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    max_native_p95 = float(policy.get("max_native_p95_ms", 25.0))
    min_speedup = float(policy.get("min_speedup_vs_fallback", 1.0))
    max_age_days = int(policy.get("max_artifact_age_days", 30))

    native_rows = [row for row in artifacts if row.native_available]
    fallback_rows = [row for row in artifacts if not row.native_available]
    if not native_rows:
        errors.append("missing native benchmark artifact")
    if not fallback_rows:
        errors.append("missing python fallback benchmark artifact")

    latest_native = max(native_rows, key=lambda row: row.timestamp) if native_rows else None
    latest_fallback = max(fallback_rows, key=lambda row: row.timestamp) if fallback_rows else None

    if latest_native is not None and latest_native.p95_ms > max_native_p95:
        errors.append(
            f"native p95 latency {latest_native.p95_ms:.3f}ms exceeds policy {max_native_p95:.3f}ms"
        )

    speedup = 0.0
    if latest_native is not None and latest_fallback is not None and latest_native.p95_ms > 0.0:
        speedup = float(latest_fallback.p95_ms / latest_native.p95_ms)
        if speedup < min_speedup:
            errors.append(f"native speedup {speedup:.3f}x is below policy minimum {min_speedup:.3f}x")

    for row in [latest_native, latest_fallback]:
        if row is None:
            continue
        age_days = int((now_utc - row.timestamp).days)
        if age_days > max_age_days:
            errors.append(
                f"benchmark artifact too old ({age_days} days): {row.path.name} > {max_age_days} days"
            )

    summary = {
        "validated": len(errors) == 0,
        "artifact_count": len(artifacts),
        "latest_native": (
            {
                "path": str(latest_native.path),
                "timestamp_utc": latest_native.timestamp.isoformat(),
                "p95_ms": latest_native.p95_ms,
            }
            if latest_native is not None
            else None
        ),
        "latest_fallback": (
            {
                "path": str(latest_fallback.path),
                "timestamp_utc": latest_fallback.timestamp.isoformat(),
                "p95_ms": latest_fallback.p95_ms,
            }
            if latest_fallback is not None
            else None
        ),
        "speedup_x": speedup,
        "policy": policy,
    }
    return errors, summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="results/native_benchmarks")
    parser.add_argument("--policy", default="config/native/latency_policy.json")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    errors, summary = evaluate_native_latency(
        results_dir=Path(args.results_dir),
        policy_path=Path(args.policy),
    )
    if errors:
        for item in errors:
            print(f"FAIL {item}")
        print(json.dumps(summary, sort_keys=True))
        return 2
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
