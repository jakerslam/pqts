# SRS Unmapped P2 Execution Map

Last updated: 2026-03-11 (America/Denver)

This document closes the remaining P2 SRS families by mapping each family to
concrete baseline controls, evidence artifacts, and validation hooks.

Source defaults:
- [config/strategy/assimilation_unmapped_p2_defaults.json](/Users/jay/Document (Lcl)/Coding/PQTS/config/strategy/assimilation_unmapped_p2_defaults.json)

Validation hook:
- [tools/check_unmapped_srs_closure.py](/Users/jay/Document (Lcl)/Coding/PQTS/tools/check_unmapped_srs_closure.py)

## COH (COH-1..COH-8)

- Scope: web/api coherence, thin-client boundary, version truth, backlog freshness.
- Evidence: web contract checks, onboarding canonical path checks, docs reachability checks.

## LEAN (LEAN-1..LEAN-6)

- Scope: framework-layer contracts, research-to-prod templates, optimizer reproducibility, adapter readiness matrix.
- Evidence: layer schema exports, optimization run manifests, readiness index artifacts.

## FTR (FTR-1..FTR-9)

- Scope: pairlist pipeline, strategy protections, lookahead/recursive guards, operator API/stream contracts, ML feature namespaces.
- Evidence: bundle artifacts, API schema checks, model namespace validations.

## NAUT (NAUT-1..NAUT-8)

- Scope: shared runtime core, deterministic replay, precision timestamp policy, adapter triad, lifecycle state machine, message bus externalization.
- Evidence: replay determinism hashes, lifecycle transition tests, triad contract checks.

## HBOT (HBOT-1..HBOT-6)

- Scope: controller/executor architecture, reusable executor library, collateral-aware budget checks, in-flight/lost-order tracking, connector metrics, gateway boundaries.
- Evidence: executor lifecycle tests, budget precheck logs, connector/gateway capability artifacts.

## VBT (VBT-1..VBT-5)

- Scope: vectorized research grids, indicator/signal factory, optimized records, composable stats/plots, research object persistence.
- Evidence: grid manifests, factory contracts, persistence version tags.

## BTR (BTR-1..BTR-5)

- Scope: analyzer/observer/sizer plugin contracts, replay/resample sync invariants, rich broker order semantics, multi-data orchestration, store pattern abstractions.
- Evidence: plugin lifecycle checks, synchronization tests, order semantics matrix reports.

## XCOMP (XCOMP-1..XCOMP-3)

- Scope: integration maturity transparency, template density, claim-discipline parity gates.
- Evidence: integration registry checks, template coverage artifacts, claim-evidence CI passes.

