"""Mode-specific cycle and refresh SLO tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import fmean
from typing import Any


@dataclass(frozen=True)
class ModeSLO:
    mode: str
    cycle_slo_ms: int
    refresh_slo_ms: int


@dataclass
class ModeSLOTracker:
    config: dict[str, ModeSLO] = field(default_factory=dict)
    cycle_samples: dict[str, list[float]] = field(default_factory=dict)
    refresh_samples: dict[str, list[float]] = field(default_factory=dict)

    def register_mode(self, slo: ModeSLO) -> None:
        key = str(slo.mode).strip().lower()
        self.config[key] = slo
        self.cycle_samples.setdefault(key, [])
        self.refresh_samples.setdefault(key, [])

    def record_cycle_ms(self, *, mode: str, value_ms: float) -> None:
        key = str(mode).strip().lower()
        self.cycle_samples.setdefault(key, []).append(float(value_ms))

    def record_refresh_ms(self, *, mode: str, value_ms: float) -> None:
        key = str(mode).strip().lower()
        self.refresh_samples.setdefault(key, []).append(float(value_ms))

    def compliance_report(self, mode: str) -> dict[str, Any]:
        key = str(mode).strip().lower()
        if key not in self.config:
            raise ValueError(f"mode not registered: {mode}")
        cfg = self.config[key]
        cycle = self.cycle_samples.get(key, [])
        refresh = self.refresh_samples.get(key, [])
        cycle_avg = float(fmean(cycle)) if cycle else 0.0
        refresh_avg = float(fmean(refresh)) if refresh else 0.0
        cycle_pass = (not cycle) or cycle_avg <= float(cfg.cycle_slo_ms)
        refresh_pass = (not refresh) or refresh_avg <= float(cfg.refresh_slo_ms)
        return {
            "mode": key,
            "cycle_avg_ms": cycle_avg,
            "refresh_avg_ms": refresh_avg,
            "cycle_slo_ms": int(cfg.cycle_slo_ms),
            "refresh_slo_ms": int(cfg.refresh_slo_ms),
            "cycle_pass": bool(cycle_pass),
            "refresh_pass": bool(refresh_pass),
            "passed": bool(cycle_pass and refresh_pass),
        }
