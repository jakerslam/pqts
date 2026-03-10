"""Tests for API/web SLO instrumentation and summary dashboards."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analytics.api_web_slo import ApiWebSLOMonitor, ApiWebSLOThresholds
from core.persistence import EventPersistenceStore


def test_api_web_slo_summary_reports_metrics() -> None:
    monitor = ApiWebSLOMonitor()
    for _ in range(30):
        monitor.record_request(service="api", route="/v1/account", status_code=200, latency_ms=120.0)
        monitor.record_request(service="web", route="/dashboard", status_code=200, latency_ms=180.0)
    payload = monitor.summarize(lookback_minutes=60)
    assert payload["services"]["api"]["requests"] == 30.0
    assert payload["services"]["web"]["requests"] == 30.0
    assert payload["healthy"] is True


def test_api_web_slo_summary_flags_critical_alerts() -> None:
    monitor = ApiWebSLOMonitor(
        thresholds=ApiWebSLOThresholds(
            api_latency_p95_ms=50.0,
            web_latency_p95_ms=50.0,
            max_error_rate=0.10,
            min_availability=0.9,
        )
    )
    for _ in range(10):
        monitor.record_request(service="api", route="/v1/orders", status_code=500, latency_ms=250.0)
    payload = monitor.summarize(lookback_minutes=60)
    assert payload["healthy"] is False
    assert any(alert["kind"] == "error_rate" for alert in payload["alerts"])
    assert any(alert["kind"] == "availability" for alert in payload["alerts"])


def test_api_web_slo_persists_summaries(tmp_path: Path) -> None:
    store = EventPersistenceStore(dsn=f"sqlite:///{tmp_path}/slo.db")
    monitor = ApiWebSLOMonitor(persistence_store=store)
    monitor.record_request(service="api", route="/v1/risk", status_code=200, latency_ms=100.0)
    monitor.summarize(lookback_minutes=60)
    rows = store.read(category="api_web_slo_summaries", limit=10)
    assert len(rows) == 1
