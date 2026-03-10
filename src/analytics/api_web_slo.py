"""API/web SLO instrumentation and dashboard payload helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np

from core.persistence import EventPersistenceStore


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str | None, *, fallback: datetime) -> datetime:
    if not value:
        return fallback
    normalized = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return fallback


@dataclass(frozen=True)
class ApiWebSLOThresholds:
    api_latency_p95_ms: float = 300.0
    web_latency_p95_ms: float = 500.0
    max_error_rate: float = 0.02
    min_availability: float = 0.995


@dataclass(frozen=True)
class RequestSample:
    service: str
    route: str
    status_code: int
    latency_ms: float
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ApiWebSLOMonitor:
    """In-memory API/web request instrumentation with dashboard-friendly SLO summaries."""

    def __init__(
        self,
        *,
        thresholds: ApiWebSLOThresholds | None = None,
        persistence_store: EventPersistenceStore | None = None,
    ) -> None:
        self.thresholds = thresholds or ApiWebSLOThresholds()
        self._store = persistence_store
        self._samples: list[RequestSample] = []

    def record_request(
        self,
        *,
        service: str,
        route: str,
        status_code: int,
        latency_ms: float,
        timestamp: str | None = None,
    ) -> RequestSample:
        now = _utc_now()
        sample = RequestSample(
            service=str(service).strip().lower(),
            route=str(route),
            status_code=int(status_code),
            latency_ms=float(max(latency_ms, 0.0)),
            timestamp=str(timestamp or now.isoformat()),
        )
        self._samples.append(sample)
        if self._store is not None:
            self._store.append(
                category="api_web_slo_request_samples",
                payload=sample.to_dict(),
                timestamp=sample.timestamp,
            )
        return sample

    def _window_samples(self, *, lookback_minutes: int) -> list[RequestSample]:
        now = _utc_now()
        cutoff = now - timedelta(minutes=max(int(lookback_minutes), 1))
        rows = [row for row in self._samples if _parse_ts(row.timestamp, fallback=now) >= cutoff]
        return rows

    @staticmethod
    def _service_metrics(rows: list[RequestSample]) -> dict[str, float]:
        if not rows:
            return {
                "requests": 0.0,
                "latency_p95_ms": 0.0,
                "error_rate": 0.0,
                "availability": 1.0,
            }
        latencies = np.asarray([row.latency_ms for row in rows], dtype=float)
        errors = sum(1 for row in rows if row.status_code >= 500)
        unavailable = sum(1 for row in rows if row.status_code >= 500)
        total = len(rows)
        return {
            "requests": float(total),
            "latency_p95_ms": float(np.percentile(latencies, 95)),
            "error_rate": float(errors / total),
            "availability": float(1.0 - (unavailable / total)),
        }

    def summarize(self, *, lookback_minutes: int = 60) -> dict[str, Any]:
        window = self._window_samples(lookback_minutes=lookback_minutes)
        api_rows = [row for row in window if row.service == "api"]
        web_rows = [row for row in window if row.service == "web"]
        api_metrics = self._service_metrics(api_rows)
        web_metrics = self._service_metrics(web_rows)

        alerts: list[dict[str, Any]] = []
        if api_metrics["latency_p95_ms"] > self.thresholds.api_latency_p95_ms:
            alerts.append(
                {
                    "service": "api",
                    "kind": "latency_p95_ms",
                    "value": api_metrics["latency_p95_ms"],
                    "threshold": self.thresholds.api_latency_p95_ms,
                    "severity": "warning",
                }
            )
        if web_metrics["latency_p95_ms"] > self.thresholds.web_latency_p95_ms:
            alerts.append(
                {
                    "service": "web",
                    "kind": "latency_p95_ms",
                    "value": web_metrics["latency_p95_ms"],
                    "threshold": self.thresholds.web_latency_p95_ms,
                    "severity": "warning",
                }
            )
        for service_name, metrics in (("api", api_metrics), ("web", web_metrics)):
            if metrics["error_rate"] > self.thresholds.max_error_rate:
                alerts.append(
                    {
                        "service": service_name,
                        "kind": "error_rate",
                        "value": metrics["error_rate"],
                        "threshold": self.thresholds.max_error_rate,
                        "severity": "critical",
                    }
                )
            if metrics["availability"] < self.thresholds.min_availability:
                alerts.append(
                    {
                        "service": service_name,
                        "kind": "availability",
                        "value": metrics["availability"],
                        "threshold": self.thresholds.min_availability,
                        "severity": "critical",
                    }
                )

        summary = {
            "generated_at": _utc_now().isoformat(),
            "lookback_minutes": int(lookback_minutes),
            "thresholds": asdict(self.thresholds),
            "services": {"api": api_metrics, "web": web_metrics},
            "alerts": alerts,
            "healthy": len(alerts) == 0,
        }
        if self._store is not None:
            self._store.append(
                category="api_web_slo_summaries",
                payload=summary,
                timestamp=summary["generated_at"],
            )
        return summary
