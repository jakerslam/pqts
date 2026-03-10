from __future__ import annotations

import json
from pathlib import Path

from analytics.autonomous_artifacts import write_autonomous_review_artifacts


def _read_last_jsonl(path: Path) -> dict:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    return json.loads(lines[-1])


def test_write_autonomous_review_artifacts_emits_memory_journal_judge(tmp_path: Path) -> None:
    review = {
        "metrics": {
            "reject_rate": 0.42,
            "slippage_mape_pct": 28.0,
            "realized_net_alpha_bps": -1.0,
            "fills": 120,
        },
        "actions": [
            {
                "rule": "reject_rate_guard",
                "triggered": True,
                "reason": "reject_rate too high",
            }
        ],
        "deltas": {"execution.profitability_gate.min_edge_bps": {"before": 0.5, "after": 0.75}},
        "proposed_overrides": {"execution": {"profitability_gate": {"min_edge_bps": 0.75}}},
    }
    paths = write_autonomous_review_artifacts(
        base_dir=tmp_path / "autonomous",
        run_id="nightly_review_20260310T000000Z",
        review=review,
        snapshot_path="data/reports/paper/snapshot.json",
        review_path="data/reports/nightly_review/review.json",
    )
    memory_path = Path(paths["memory_path"])
    journal_path = Path(paths["journal_path"])
    judge_path = Path(paths["judge_path"])
    assert memory_path.exists()
    assert journal_path.exists()
    assert judge_path.exists()

    memory = _read_last_jsonl(memory_path)
    journal = _read_last_jsonl(journal_path)
    judge = _read_last_jsonl(judge_path)
    assert memory["artifact_type"] == "memory"
    assert journal["artifact_type"] == "trade_journal"
    assert judge["artifact_type"] == "judge_report"
    assert judge["verdict"] == "tighten"
