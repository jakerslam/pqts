# Repo Simplification Notes

Last updated: 2026-03-10

## Objective

Reduce overlap and make module boundaries easier to reason about for both humans and AI coders, while preserving import compatibility.

## Canonical vs Compatibility Modules

### Funding Arbitrage

- Canonical implementation:
  - `src/strategies/funding_arbitrage.py`
- Compatibility adapter:
  - `src/strategies/arbitrage/funding_arbitrage.py`

The `strategies.arbitrage.funding_arbitrage` module now delegates to the canonical strategy module to avoid dual implementations drifting out of sync.

### Regime Detection

- Canonical implementation:
  - `src/research/regime_detector.py`
- Compatibility facade:
  - `src/strategies/regime_detector.py`

The strategy-layer detector now wraps the research detector and maps regimes into the legacy strategy enum surface.

## Shared Primitives

### Kelly Math

Added shared Kelly sizing primitives in:

- `src/portfolio/kelly_core.py`

Consumers now use this shared base:

- `src/portfolio/uncertainty_kelly.py`
- `src/positioning/sizing.py`
- `src/strategies/underdog_value.py`
- `src/strategies/short_cycle_binary.py`

This removes repeated formula implementations and keeps risk math consistent.

## Hygiene

- `make clean` now removes local cache/build artifacts:
  - `__pycache__`
  - `*.egg-info`
  - pytest/mypy/ruff caches
  - `build/`, `dist/`, `site/`

## Next Safe Consolidation Targets

1. Unify backtesting engine interfaces (`src/backtesting/engine.py`, `src/backtesting/event_engine.py`) behind a shared base protocol.
2. Consolidate readiness/promotion evaluators behind one shared gate DSL (`paper_readiness`, `promotion_gates`, `readiness_gates`).
3. Add `src/README.md` package boundary map and keep it validated in CI.
