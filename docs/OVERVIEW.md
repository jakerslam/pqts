# PQTS Overview

## Executive Summary

> A governed system for monetizing future predictions.

Prediction markets are the primary trading surface; adjacent tradable forecasting venues use the same control plane when they satisfy the same safety and eligibility contracts.

PQTS turns forecasts, probabilities, and scenario analysis into auditable capital decisions under explicit EV, risk, provenance, and promotion gates. It is not a generic "trade anything" shell and it is not a separate speculative sidecar outside the canonical control plane.

## Core Loop

1. Ingest market, scenario, and model inputs.
2. Estimate fair probabilities or decision ranges.
3. Compare venue-implied probability versus model-estimated probability.
4. Block any candidate that fails net-EV, venue-eligibility, or risk gates.
5. Route allowed orders only through `execution.RiskAwareRouter.submit_order()`.
6. Persist reconciliation, settlement, attribution, and promotion evidence.

## Product Shape

- Prediction-market-first: binary, threshold, range, count, and related forecast contracts are the primary execution surface.
- Governed expansion: adjacent forecast-trading venues are allowed only when they satisfy the same routing, reconciliation, entitlement, and certification contracts.
- Read-only by default: unauthenticated or non-eligible venues remain in research, advisory, or dry-run modes.
- One lifecycle: `backtest -> paper -> shadow -> canary -> live`.

## Operator Guarantees

- One canonical order path through the risk-aware router.
- Hard kill-switches, drawdown limits, and venue/account eligibility controls.
- Order-truth and provenance receipts for explainability and replay.
- Promotion gates that prevent direct jumps from research to live capital.
- Reconciliation and settlement visibility instead of silent position drift.

## Primary Surfaces

- `README.md`: public product framing and proof links.
- `docs/index.md`: landing page for the docs property.
- `docs/SRS.md`: canonical requirements and control contracts.
- `docs/ARCHITECTURE.md`: runtime and boundary model.
- `docs/IMPLEMENTATION_DIRECTION.md`: execution posture and migration direction.

## What PQTS Is Not

- Not a generic multi-asset brokerage front-end.
- Not a copy-trading growth hack.
- Not a direct-exchange shortcut that bypasses router, reconciliation, or promotion controls.
- Not permission to enable trading on venues where legal, entitlement, or account status is unclear.
