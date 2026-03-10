# PQTS Incident Response

Use this skill for rapid risk/ops incident triage with evidence capture.

## Steps
1. Generate incident candidates:
   `python3 scripts/run_incident_automation.py --since-minutes 60`
2. Produce SLO health report:
   `python3 scripts/slo_health_report.py --stream-health data/analytics/stream_health.json`
3. Validate reconciliation and disable-list posture:
   `python3 scripts/run_reconciliation_daemon.py --dry-run`
4. Send operator alert if incident severity is high:
   `python3 scripts/send_ops_notification.py --kind incident --title "PQTS incident"`

## Outputs
- Incident payloads in analytics reports.
- SLO status for stream, latency, rejection, and reconciliation.

## Safety
- Never bypass kill-switch or risk guard decisions.
- Use policy-constrained rollback paths only.
