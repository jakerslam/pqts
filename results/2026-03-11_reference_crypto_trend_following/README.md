# Result Bundle: 2026-03-11_reference_crypto_trend_following

## Run Metadata

- Date (UTC): 2026-03-11T05:45:36.306813+00:00
- Risk profile: balanced
- Scenario count: 1
- Config snapshot: `config_paper_snapshot.yaml`

## Command

```bash
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 scripts/run_simulation_suite.py --config config/paper.yaml --markets crypto --strategies trend_following --cycles-per-scenario 36 --symbols-per-market 1 --readiness-every 12 --risk-profile balanced --sleep-seconds 0.0 --out-dir results/2026-03-11_reference_crypto_trend_following --telemetry-log results/2026-03-11_reference_crypto_trend_following/simulation_events.jsonl --tca-dir results/2026-03-11_reference_crypto_trend_following/tca
```

## Included Artifacts

- `simulation_suite_20260311T054536166021Z.json`
- `simulation_leaderboard_20260311T054536166021Z.csv`
- `metrics_chart.svg`
- `config_paper_snapshot.yaml`
- `dataset_manifest.json`

## Key Metrics

- total_submitted=36
- total_filled=36
- total_rejected=0
- avg_quality_score=0.8128
- avg_fill_rate=1.0000
- avg_reject_rate=0.0000

- `crypto/trend_following`: quality=0.81, fill=1.00, reject=0.00, submitted=36

## Claim Classification

- Claim class: `reference`
- Evidence source: `simulation_suite_20260311T054536166021Z.json` + `simulation_leaderboard_20260311T054536166021Z.csv`
- Non-zero fill gate: `passed`

## Notes

Reference-quality bundle intended for public reproducibility and benchmark governance.
