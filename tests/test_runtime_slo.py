from __future__ import annotations

from analytics.runtime_slo import ModeSLO, ModeSLOTracker


def test_runtime_slo_tracker_reports_pass_and_fail() -> None:
    tracker = ModeSLOTracker()
    tracker.register_mode(ModeSLO(mode="paper", cycle_slo_ms=1000, refresh_slo_ms=5000))
    tracker.record_cycle_ms(mode="paper", value_ms=900)
    tracker.record_refresh_ms(mode="paper", value_ms=4000)
    report = tracker.compliance_report("paper")
    assert report["passed"] is True

    tracker.record_cycle_ms(mode="paper", value_ms=2000)
    report_fail = tracker.compliance_report("paper")
    assert report_fail["cycle_pass"] is False
    assert report_fail["passed"] is False
