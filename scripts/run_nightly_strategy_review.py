#!/usr/bin/env python3
"""Nightly strategy review with bounded auto-tuning proposals."""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if SRC.exists():
    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path[:] = [src_str, *sys.path]
if str(ROOT) not in sys.path:
    sys.path[:] = [str(ROOT), *sys.path]

from analytics.autonomous_artifacts import write_autonomous_review_artifacts
from analytics.nightly_strategy_review import (
    NightlyReviewThresholds,
    apply_overrides_to_config,
    build_nightly_review,
    resolve_snapshot_path,
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_yaml(path: Path) -> Dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default="auto", help="Path to paper snapshot JSON or 'auto'.")
    parser.add_argument("--reports-dir", default="data/reports")
    parser.add_argument("--config", default="config/paper.yaml")
    parser.add_argument("--out-dir", default="data/reports/nightly_review")
    parser.add_argument(
        "--artifact-dir",
        default="data/analytics/autonomous",
        help="Directory for memory/journal/judge artifacts.",
    )
    parser.add_argument("--write-overrides", default="", help="Optional YAML path for proposed overrides.")
    parser.add_argument(
        "--apply-config",
        action="store_true",
        help="Apply generated overrides to --config (guarded by --confirm-apply).",
    )
    parser.add_argument(
        "--confirm-apply",
        action="store_true",
        help="Required with --apply-config to avoid accidental config mutation.",
    )
    parser.add_argument("--max-reject-rate", type=float, default=0.30)
    parser.add_argument("--max-slippage-mape-pct", type=float, default=25.0)
    parser.add_argument("--min-realized-net-alpha-bps", type=float, default=0.0)
    parser.add_argument("--max-critical-alerts", type=int, default=0)
    parser.add_argument("--relax-reject-rate", type=float, default=0.10)
    parser.add_argument("--relax-slippage-mape-pct", type=float, default=10.0)
    parser.add_argument("--relax-realized-net-alpha-bps", type=float, default=6.0)
    parser.add_argument("--output", choices=["table", "json"], default="table")
    return parser


def _print_table(payload: Dict[str, Any]) -> None:
    review = payload.get("review", {}) if isinstance(payload, dict) else {}
    metrics = review.get("metrics", {}) if isinstance(review, dict) else {}
    deltas = review.get("deltas", {}) if isinstance(review, dict) else {}
    print("Nightly review completed")
    print(f"  snapshot: {payload.get('snapshot_path')}")
    print(f"  review:   {payload.get('review_path')}")
    if payload.get("overrides_path"):
        print(f"  overrides:{payload.get('overrides_path')}")
    if payload.get("applied_config_path"):
        print(f"  applied:  {payload.get('applied_config_path')}")
    artifact_paths = payload.get("artifact_paths", {}) if isinstance(payload, dict) else {}
    if artifact_paths:
        print(f"  artifacts:{artifact_paths.get('base_dir')}")
    print(
        "  metrics:  "
        f"reject_rate={float(metrics.get('reject_rate', 0.0)):.3f}, "
        f"slippage_mape_pct={float(metrics.get('slippage_mape_pct', 0.0)):.2f}, "
        f"realized_net_alpha_bps={float(metrics.get('realized_net_alpha_bps', 0.0)):.4f}"
    )
    if not deltas:
        print("  deltas:   none")
        return
    print("  deltas:")
    for key in sorted(deltas.keys()):
        delta = deltas[key]
        print(f"    - {key}: {delta.get('before')} -> {delta.get('after')}")


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = resolve_snapshot_path(args.snapshot, reports_dir=args.reports_dir)
    snapshot = _load_json(snapshot_path)

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    config_payload = _load_yaml(config_path)

    thresholds = NightlyReviewThresholds(
        max_reject_rate=float(args.max_reject_rate),
        max_slippage_mape_pct=float(args.max_slippage_mape_pct),
        min_realized_net_alpha_bps=float(args.min_realized_net_alpha_bps),
        max_critical_alerts=int(args.max_critical_alerts),
        relax_reject_rate=float(args.relax_reject_rate),
        relax_slippage_mape_pct=float(args.relax_slippage_mape_pct),
        relax_realized_net_alpha_bps=float(args.relax_realized_net_alpha_bps),
    )
    review = build_nightly_review(snapshot=snapshot, config=config_payload, thresholds=thresholds)

    stamp = _utc_stamp()
    review_path = out_dir / f"nightly_strategy_review_{stamp}.json"
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run_id = f"nightly_review_{stamp}"
    artifact_paths = write_autonomous_review_artifacts(
        base_dir=args.artifact_dir,
        run_id=run_id,
        review=review,
        snapshot_path=str(snapshot_path),
        review_path=str(review_path),
    )

    overrides = review.get("proposed_overrides", {})
    overrides_path = ""
    write_overrides = str(args.write_overrides).strip()
    if overrides and (write_overrides or args.apply_config):
        target = Path(write_overrides) if write_overrides else (out_dir / f"nightly_overrides_{stamp}.yaml")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(yaml.safe_dump(overrides, sort_keys=True), encoding="utf-8")
        overrides_path = str(target)

    applied_config_path = ""
    backup_config_path = ""
    if args.apply_config:
        if not args.confirm_apply:
            raise ValueError("--apply-config requires --confirm-apply")
        if overrides:
            updated = apply_overrides_to_config(config=config_payload, overrides=overrides)
            backup = config_path.with_suffix(f"{config_path.suffix}.bak.{stamp}")
            backup.write_text(yaml.safe_dump(config_payload, sort_keys=False), encoding="utf-8")
            config_path.write_text(yaml.safe_dump(updated, sort_keys=False), encoding="utf-8")
            applied_config_path = str(config_path)
            backup_config_path = str(backup)

    payload: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "snapshot_path": str(snapshot_path),
        "config_path": str(config_path),
        "review_path": str(review_path),
        "overrides_path": overrides_path,
        "applied_config_path": applied_config_path,
        "backup_config_path": backup_config_path,
        "artifact_paths": artifact_paths,
        "review": review,
    }
    if args.output == "json":
        print(json.dumps(payload, sort_keys=True))
    else:
        _print_table(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
