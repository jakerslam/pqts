# PQTS Documentation

> A governed system for monetizing future predictions.

Prediction markets are the primary trading surface; adjacent tradable forecasting venues use the same control plane when they satisfy the same safety and eligibility contracts.

PQTS is a governed forecast-to-capital system focused on:

- deterministic simulation and promotion gates
- strict EV, risk, and venue-eligibility controls
- operational telemetry, reconciliation, and settlement reliability

## 5-Minute Path

1. `pqts init`
2. `pqts demo`
3. `pqts backtest momentum`
4. `pqts paper start`

See [5-Minute Quickstart](QUICKSTART_5_MIN.md).

## Live Artifacts

- Simulation telemetry: [SIMULATION_TELEMETRY.md](SIMULATION_TELEMETRY.md)
- Requirements baseline: [SRS.md](SRS.md)
- Benchmark methodology: [BENCHMARKS.md](BENCHMARKS.md)
- Latest reference metrics: [REFERENCE_PERFORMANCE.md](REFERENCE_PERFORMANCE.md)
- Repository layout: [REPO_STRUCTURE.md](REPO_STRUCTURE.md)

## Public Leaderboard

The static leaderboard page is generated from the latest simulation leaderboard CSV
at build time and published with this docs site.
