"""Nightly paper-trading review with bounded strategy/risk tuning proposals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class NightlyReviewThresholds:
    max_reject_rate: float = 0.30
    max_slippage_mape_pct: float = 25.0
    min_realized_net_alpha_bps: float = 0.0
    max_critical_alerts: int = 0
    relax_reject_rate: float = 0.10
    relax_slippage_mape_pct: float = 10.0
    relax_realized_net_alpha_bps: float = 6.0


def resolve_snapshot_path(snapshot: str, *, reports_dir: str = "data/reports") -> Path:
    token = str(snapshot or "").strip()
    if token and token.lower() != "auto":
        path = Path(token)
        if not path.exists():
            raise FileNotFoundError(f"Snapshot not found: {path}")
        return path

    base = Path(reports_dir) / "paper"
    candidates = sorted(base.glob("paper_campaign_snapshot_*.json"))
    if not candidates:
        raise FileNotFoundError(f"No paper campaign snapshots found under: {base}")
    return candidates[-1]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def extract_review_metrics(snapshot: Dict[str, Any]) -> Dict[str, float]:
    stats = snapshot.get("stats", {}) if isinstance(snapshot, dict) else {}
    ops_health = snapshot.get("ops_health", {}) if isinstance(snapshot, dict) else {}
    promo = snapshot.get("promotion_gate", {}) if isinstance(snapshot, dict) else {}
    revenue = snapshot.get("revenue", {}) if isinstance(snapshot, dict) else {}

    promo_metrics = promo.get("metrics", {}) if isinstance(promo, dict) else {}
    revenue_summary = revenue.get("summary", {}) if isinstance(revenue, dict) else {}
    ops_summary = ops_health.get("summary", {}) if isinstance(ops_health, dict) else {}

    reject_rate = _safe_float(
        stats.get("reject_rate"),
        _safe_float(promo_metrics.get("reject_rate"), 0.0),
    )
    slippage_mape_pct = _safe_float(
        revenue_summary.get("slippage_mape_pct"),
        _safe_float(promo_metrics.get("slippage_mape_pct"), 0.0),
    )
    realized_net_alpha_bps = _safe_float(
        revenue_summary.get("avg_realized_net_alpha_bps"),
        _safe_float(promo_metrics.get("avg_realized_net_alpha_bps"), 0.0),
    )
    critical_alerts = _safe_int(ops_summary.get("critical"), 0)
    warning_alerts = _safe_int(ops_summary.get("warning"), 0)
    fills = _safe_int(stats.get("filled"), _safe_int(promo_metrics.get("fills"), 0))

    return {
        "reject_rate": reject_rate,
        "slippage_mape_pct": slippage_mape_pct,
        "realized_net_alpha_bps": realized_net_alpha_bps,
        "critical_alerts": float(critical_alerts),
        "warning_alerts": float(warning_alerts),
        "fills": float(fills),
    }


def _get_nested(payload: Dict[str, Any], keys: List[str], default: Any) -> Any:
    cursor: Any = payload
    for key in keys:
        if not isinstance(cursor, dict):
            return default
        cursor = cursor.get(key)
    return cursor if cursor is not None else default


def _set_nested(payload: Dict[str, Any], keys: List[str], value: Any) -> None:
    cursor = payload
    for key in keys[:-1]:
        child = cursor.get(key)
        if not isinstance(child, dict):
            child = {}
            cursor[key] = child
        cursor = child
    cursor[keys[-1]] = value


def _bounded(value: float, *, minimum: float, maximum: float) -> float:
    return float(min(max(value, minimum), maximum))


def _derive_current_values(config: Dict[str, Any]) -> Dict[str, float]:
    return {
        "execution.profitability_gate.min_edge_bps": _safe_float(
            _get_nested(config, ["execution", "profitability_gate", "min_edge_bps"], 0.5),
            0.5,
        ),
        "runtime.autopilot.max_active_strategies": _safe_float(
            _get_nested(config, ["runtime", "autopilot", "max_active_strategies"], 6),
            6,
        ),
        "execution.paper_fill_model.stress_slippage_multiplier": _safe_float(
            _get_nested(config, ["execution", "paper_fill_model", "stress_slippage_multiplier"], 2.5),
            2.5,
        ),
        "risk.daily_loss_limit": _safe_float(_get_nested(config, ["risk", "daily_loss_limit"], 500.0), 500.0),
    }


def build_nightly_review(
    *,
    snapshot: Dict[str, Any],
    config: Dict[str, Any],
    thresholds: NightlyReviewThresholds | None = None,
) -> Dict[str, Any]:
    resolved_thresholds = thresholds or NightlyReviewThresholds()
    metrics = extract_review_metrics(snapshot)
    current = _derive_current_values(config)
    proposed = dict(current)
    actions: List[Dict[str, Any]] = []

    reject_rate = _safe_float(metrics.get("reject_rate"), 0.0)
    slippage_mape_pct = _safe_float(metrics.get("slippage_mape_pct"), 0.0)
    realized_net_alpha_bps = _safe_float(metrics.get("realized_net_alpha_bps"), 0.0)
    critical_alerts = _safe_int(metrics.get("critical_alerts"), 0)

    if critical_alerts > int(resolved_thresholds.max_critical_alerts):
        current_max = _safe_float(proposed["runtime.autopilot.max_active_strategies"], 6.0)
        proposed["runtime.autopilot.max_active_strategies"] = _bounded(
            current_max - 1.0,
            minimum=1.0,
            maximum=12.0,
        )
        proposed["risk.daily_loss_limit"] = _bounded(
            _safe_float(proposed["risk.daily_loss_limit"], 500.0) * 0.90,
            minimum=50.0,
            maximum=1_000_000.0,
        )
        actions.append(
            {
                "rule": "critical_alerts_guard",
                "triggered": True,
                "reason": (
                    f"critical_alerts={critical_alerts} "
                    f"> max_critical_alerts={int(resolved_thresholds.max_critical_alerts)}"
                ),
            }
        )

    if reject_rate > float(resolved_thresholds.max_reject_rate):
        proposed["execution.profitability_gate.min_edge_bps"] = _bounded(
            _safe_float(proposed["execution.profitability_gate.min_edge_bps"], 0.5) + 0.25,
            minimum=0.1,
            maximum=10.0,
        )
        proposed["runtime.autopilot.max_active_strategies"] = _bounded(
            _safe_float(proposed["runtime.autopilot.max_active_strategies"], 6.0) - 1.0,
            minimum=1.0,
            maximum=12.0,
        )
        actions.append(
            {
                "rule": "reject_rate_guard",
                "triggered": True,
                "reason": (
                    f"reject_rate={reject_rate:.3f} "
                    f"> max_reject_rate={float(resolved_thresholds.max_reject_rate):.3f}"
                ),
            }
        )

    if slippage_mape_pct > float(resolved_thresholds.max_slippage_mape_pct):
        proposed["execution.paper_fill_model.stress_slippage_multiplier"] = _bounded(
            _safe_float(proposed["execution.paper_fill_model.stress_slippage_multiplier"], 2.5) + 0.15,
            minimum=1.0,
            maximum=6.0,
        )
        proposed["execution.profitability_gate.min_edge_bps"] = _bounded(
            _safe_float(proposed["execution.profitability_gate.min_edge_bps"], 0.5) + 0.15,
            minimum=0.1,
            maximum=10.0,
        )
        actions.append(
            {
                "rule": "slippage_mape_guard",
                "triggered": True,
                "reason": (
                    f"slippage_mape_pct={slippage_mape_pct:.2f} "
                    f"> max_slippage_mape_pct={float(resolved_thresholds.max_slippage_mape_pct):.2f}"
                ),
            }
        )

    if realized_net_alpha_bps < float(resolved_thresholds.min_realized_net_alpha_bps):
        proposed["execution.profitability_gate.min_edge_bps"] = _bounded(
            _safe_float(proposed["execution.profitability_gate.min_edge_bps"], 0.5) + 0.25,
            minimum=0.1,
            maximum=10.0,
        )
        proposed["risk.daily_loss_limit"] = _bounded(
            _safe_float(proposed["risk.daily_loss_limit"], 500.0) * 0.95,
            minimum=50.0,
            maximum=1_000_000.0,
        )
        actions.append(
            {
                "rule": "negative_alpha_guard",
                "triggered": True,
                "reason": (
                    f"realized_net_alpha_bps={realized_net_alpha_bps:.4f} "
                    f"< min_realized_net_alpha_bps={float(resolved_thresholds.min_realized_net_alpha_bps):.4f}"
                ),
            }
        )

    healthy_relax = (
        not actions
        and reject_rate <= float(resolved_thresholds.relax_reject_rate)
        and slippage_mape_pct <= float(resolved_thresholds.relax_slippage_mape_pct)
        and realized_net_alpha_bps >= float(resolved_thresholds.relax_realized_net_alpha_bps)
    )
    if healthy_relax:
        proposed["execution.profitability_gate.min_edge_bps"] = _bounded(
            _safe_float(proposed["execution.profitability_gate.min_edge_bps"], 0.5) - 0.10,
            minimum=0.1,
            maximum=10.0,
        )
        proposed["runtime.autopilot.max_active_strategies"] = _bounded(
            _safe_float(proposed["runtime.autopilot.max_active_strategies"], 6.0) + 1.0,
            minimum=1.0,
            maximum=12.0,
        )
        actions.append(
            {
                "rule": "healthy_relaxation",
                "triggered": True,
                "reason": "Performance and risk metrics are within healthy relaxation bounds.",
            }
        )

    override_payload: Dict[str, Any] = {}
    deltas: Dict[str, Dict[str, float]] = {}
    for dotted_key, proposed_value in proposed.items():
        before = _safe_float(current[dotted_key], 0.0)
        after = _safe_float(proposed_value, before)
        if abs(after - before) < 1e-12:
            continue
        path = dotted_key.split(".")
        cast_value: float | int = after
        if path[-1] in {"max_active_strategies"}:
            cast_value = int(round(after))
        _set_nested(override_payload, path, cast_value)
        deltas[dotted_key] = {"before": before, "after": _safe_float(cast_value, after)}

    return {
        "generated_at": _utc_now_iso(),
        "metrics": metrics,
        "thresholds": asdict(resolved_thresholds),
        "actions": actions,
        "current_values": current,
        "proposed_values": proposed,
        "deltas": deltas,
        "proposed_overrides": override_payload,
    }


def apply_overrides_to_config(
    *,
    config: Dict[str, Any],
    overrides: Dict[str, Any],
) -> Dict[str, Any]:
    result = dict(config)

    def _merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in src.items():
            if isinstance(value, dict):
                child = dst.get(key)
                if not isinstance(child, dict):
                    child = {}
                dst[key] = _merge(dict(child), value)
            else:
                dst[key] = value
        return dst

    return _merge(result, overrides)
