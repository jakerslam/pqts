# Reference Performance

Last generated (UTC): 2026-03-11T05:45:39.108708+00:00

This file is generated from `results/reference_performance_latest.json`.

## Highlight

- Best bundle by quality: `2026-03-11_reference_multi_market_making`
- Metrics: quality `0.8403`, fill `1.0000`, reject `0.0000`
- Artifacts: [bundle](../results/2026-03-11_reference_multi_market_making/README.md), [csv](../results/2026-03-11_reference_multi_market_making/simulation_leaderboard_20260311T054538975060Z.csv), [report](../results/2026-03-11_reference_multi_market_making/simulation_suite_20260311T054538975060Z.json)

## Bundle Table

| Bundle | Markets | Strategy | Submitted | Filled | Rejected | Quality | Fill | Reject |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `2026-03-11_reference_crypto_funding_arbitrage` | `crypto` | `funding_arbitrage` | 36 | 36 | 0 | 0.8120 | 1.0000 | 0.0000 |
| `2026-03-11_reference_crypto_trend_following` | `crypto` | `trend_following` | 36 | 36 | 0 | 0.8128 | 1.0000 | 0.0000 |
| `2026-03-11_reference_multi_market_making` | `crypto,equities,forex` | `market_making` | 90 | 90 | 0 | 0.8403 | 1.0000 | 0.0000 |

## Regeneration

```bash
python3 scripts/publish_reference_bundles.py --config config/paper.yaml --out-root results
python3 scripts/render_reference_performance.py
```
