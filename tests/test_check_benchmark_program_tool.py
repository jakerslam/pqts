from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tools.check_benchmark_program import evaluate_benchmark_program


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_benchmark_program_evaluation_passes_minimal_matrix(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    _write_json(
        policy_path,
        {
            "min_bundles": 1,
            "min_markets": 1,
            "min_strategies": 1,
            "min_venues": 1,
            "min_month_buckets": 1,
            "allow_single_month_bootstrap": True,
        },
    )

    tca_path = tmp_path / "results" / "bundle_a" / "tca" / "x.csv"
    tca_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "exchange": ["binance"],
            "realized_slippage_bps": [1.0],
            "predicted_slippage_bps": [0.5],
        }
    ).to_csv(tca_path, index=False)

    suite_path = tmp_path / "results" / "bundle_a" / "simulation_suite.json"
    _write_json(
        suite_path,
        {
            "created_at": "2026-03-10T00:00:00+00:00",
            "results": [
                {
                    "scenario": {"market": "crypto", "strategy": "trend_following"},
                    "tca_path": str(tca_path.relative_to(tmp_path)),
                }
            ],
        },
    )

    ref_path = tmp_path / "results" / "reference_performance_latest.json"
    _write_json(
        ref_path,
        {
            "generated_at": "2026-03-10T00:00:00+00:00",
            "bundles": [
                {
                    "bundle": "bundle_a",
                    "markets": "crypto",
                    "strategies": "trend_following",
                    "report_path": str(suite_path.relative_to(tmp_path)),
                }
            ],
        },
    )

    errors, report = evaluate_benchmark_program(
        reference_performance_path=ref_path,
        results_root=tmp_path,
        policy_path=policy_path,
        report_out=tmp_path / "report.json",
    )
    assert errors == []
    assert report["bundle_count"] == 1
    assert report["venues"] == ["binance"]


def test_benchmark_program_flags_insufficient_coverage(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    _write_json(
        policy_path,
        {
            "min_bundles": 2,
            "min_markets": 2,
            "min_strategies": 2,
            "min_venues": 2,
            "min_month_buckets": 1,
            "allow_single_month_bootstrap": True,
        },
    )
    ref_path = tmp_path / "reference.json"
    _write_json(ref_path, {"generated_at": "2026-03-10T00:00:00+00:00", "bundles": []})

    errors, _ = evaluate_benchmark_program(
        reference_performance_path=ref_path,
        results_root=tmp_path,
        policy_path=policy_path,
    )
    assert any("bundle_count" in item for item in errors)
