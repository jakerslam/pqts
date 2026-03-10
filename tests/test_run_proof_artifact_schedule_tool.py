from __future__ import annotations

import json
from pathlib import Path

from tools import run_proof_artifact_schedule


def test_run_proof_artifact_schedule_tool_publishes_when_due(tmp_path: Path, monkeypatch) -> None:
    cfg = {
        "artifact_id": "a1",
        "artifact_type": "benchmark",
        "cadence_hours": 24,
        "last_run_at": "",
        "provenance_ref": "data/reports/provenance/benchmark_provenance.jsonl",
        "reproducible_command": "make sim-suite",
        "result_class": "reference",
    }
    config_path = tmp_path / "proof_schedule.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    out_path = tmp_path / "proof_manifest.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_proof_artifact_schedule.py",
            "--config",
            str(config_path),
            "--out",
            str(out_path),
        ],
    )
    assert run_proof_artifact_schedule.main() == 0
    assert out_path.exists()
