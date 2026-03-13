# Reference Performance

Last generated (UTC): 2026-03-13T02:03:43.937783+00:00

This file is generated from `results/reference_performance_latest.json`.

## Highlight

- Best bundle by quality: `2026-03-13_reference_crypto_funding_arbitrage`
- Metrics: quality `0.8574`, fill `1.0000`, reject `0.0000`
- Artifacts: [bundle](../results/2026-03-13_reference_crypto_funding_arbitrage/README.md), [csv](../results/2026-03-13_reference_crypto_funding_arbitrage/simulation_leaderboard_20260313T020345468787Z.csv), [report](../results/2026-03-13_reference_crypto_funding_arbitrage/simulation_suite_20260313T020345468787Z.json)

## Bundle Table

| Bundle | Markets | Strategy | Submitted | Filled | Rejected | Quality | Fill | Reject |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `2026-03-13_reference_crypto_funding_arbitrage` | `crypto` | `funding_arbitrage` | 36 | 36 | 0 | 0.8574 | 1.0000 | 0.0000 |
| `2026-03-13_reference_crypto_trend_following` | `crypto` | `trend_following` | 36 | 36 | 0 | 0.8303 | 1.0000 | 0.0000 |
| `2026-03-13_reference_multi_market_making` | `crypto,equities,forex` | `market_making` | 90 | 90 | 0 | 0.8405 | 1.0000 | 0.0000 |

## Regeneration

```bash
python3 scripts/publish_reference_bundles.py --config config/paper.yaml --out-root results
python3 scripts/render_reference_performance.py
```
