# Benchmark Methodology

This page defines how PQTS runtime and backtesting performance are measured.

## Hardware + Environment

- CPU: document model and core count
- RAM: document capacity
- OS: document version
- Python: document exact version

## Dataset Profile

- Universe size
- Time range
- Bar/event resolution
- Data source and checksum/manifests

## Commands

```bash
python scripts/run_simulation_suite.py --markets crypto,equities,forex --strategies market_making,funding_arbitrage,cross_exchange --cycles-per-scenario 60 --readiness-every 20
python scripts/run_strategy_tournament.py --start 2026-01-01T00:00:00Z --end 2026-02-01T00:00:00Z
```

## Metrics Captured

- wall-clock runtime
- throughput (events/orders per second)
- memory utilization
- p95/p99 latencies for key execution paths

## Baseline Table (Template)

| Benchmark | Dataset | Runtime | CPU | Memory | Notes |
|-----------|---------|---------|-----|--------|-------|
| Sim suite | TBD | TBD | TBD | TBD | Populate with reproducible run |
| Tournament | TBD | TBD | TBD | TBD | Populate with reproducible run |
