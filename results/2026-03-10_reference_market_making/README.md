# Result Bundle: 2026-03-10_reference_market_making

## Run Metadata

- Date (UTC): 2026-03-10T18:00:00+00:00
- Risk profile: balanced
- Scenario count: 1
- Config snapshot: `config_paper_snapshot.yaml`

## Command

```bash
python3 scripts/run_simulation_suite.py --markets crypto --strategies market_making --cycles-per-scenario 10 --readiness-every 4 --out-dir results/2026-03-10_reference_market_making --sleep-seconds 0.0 --symbols-per-market 1 --risk-profile balanced
```

## Included Artifacts

- `simulation_suite_20260310T180000000000Z.json`
- `simulation_leaderboard_20260310T180000000000Z.csv`
- `metrics_chart.svg`
- `config_paper_snapshot.yaml`
- `dataset_manifest.json`

## Key Metrics

- `crypto/market_making`: quality=0.25, fill=0.80, reject=0.20, priority=0.15

## Claim Classification

- Claim class: `reference`
- Evidence source: `simulation_suite_20260310T180000000000Z.json` + `simulation_leaderboard_20260310T180000000000Z.csv`

## Notes

Reference-quality bundle used to validate benchmark publication gates.
