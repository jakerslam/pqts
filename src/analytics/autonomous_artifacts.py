"""Standardized autonomous memory/journal/judge artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(*parts: str) -> str:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _judge_verdict(actions: List[Dict[str, Any]]) -> str:
    rules = [str(item.get("rule", "")) for item in actions if isinstance(item, dict)]
    if any(rule.endswith("_guard") for rule in rules):
        return "tighten"
    if "healthy_relaxation" in rules:
        return "relax"
    return "hold"


def write_autonomous_review_artifacts(
    *,
    base_dir: str | Path,
    run_id: str,
    review: Dict[str, Any],
    snapshot_path: str,
    review_path: str,
) -> Dict[str, Any]:
    root = Path(base_dir)
    created_at = _utc_now_iso()
    metrics = dict(review.get("metrics", {}) or {})
    deltas = dict(review.get("deltas", {}) or {})
    actions = list(review.get("actions", []) or [])
    verdict = _judge_verdict(actions)

    memory_file = root / "memory.jsonl"
    journal_file = root / "trade_journal.jsonl"
    judge_file = root / "judge_report.jsonl"

    memory_row = {
        "schema_version": "1.0",
        "artifact_type": "memory",
        "artifact_id": _stable_id(run_id, "memory", created_at),
        "created_at": created_at,
        "run_id": run_id,
        "summary": {
            "verdict": verdict,
            "action_count": int(len(actions)),
            "metric_digest": {
                "reject_rate": float(metrics.get("reject_rate", 0.0)),
                "slippage_mape_pct": float(metrics.get("slippage_mape_pct", 0.0)),
                "realized_net_alpha_bps": float(metrics.get("realized_net_alpha_bps", 0.0)),
            },
        },
        "links": {
            "snapshot_path": str(snapshot_path),
            "review_path": str(review_path),
        },
    }
    _append_jsonl(memory_file, memory_row)

    journal_row = {
        "schema_version": "1.0",
        "artifact_type": "trade_journal",
        "artifact_id": _stable_id(run_id, "journal", created_at),
        "created_at": created_at,
        "run_id": run_id,
        "actions": actions,
        "deltas": deltas,
        "proposed_overrides": dict(review.get("proposed_overrides", {}) or {}),
        "links": {
            "snapshot_path": str(snapshot_path),
            "review_path": str(review_path),
        },
    }
    _append_jsonl(journal_file, journal_row)

    fills = float(metrics.get("fills", 0.0))
    confidence = min(0.99, 0.50 + min(fills / 500.0, 0.45))
    judge_row = {
        "schema_version": "1.0",
        "artifact_type": "judge_report",
        "artifact_id": _stable_id(run_id, "judge", created_at),
        "created_at": created_at,
        "run_id": run_id,
        "verdict": verdict,
        "confidence": float(confidence),
        "rationale": [str(item.get("reason", "")) for item in actions if isinstance(item, dict)],
        "links": {
            "snapshot_path": str(snapshot_path),
            "review_path": str(review_path),
        },
    }
    _append_jsonl(judge_file, judge_row)

    return {
        "base_dir": str(root),
        "memory_path": str(memory_file),
        "journal_path": str(journal_file),
        "judge_path": str(judge_file),
        "verdict": verdict,
    }
