# SRS 66-71 Execution Map

Last updated: 2026-03-11 (America/Denver)

Scope:
- `GIPP-*`
- `MARIK-*`
- `DUNIK-*`
- `ZERQ-*`
- `ANTP-*`
- `MTM-*`

This map turns assimilation requirements into dependency-ordered execution lanes.

## Lane 0: Governance and Anti-Fake-Work

- DoD + enforcer protocol:
  - [docs/DEFINITION_OF_DONE.md](/Users/jay/Document (Lcl)/Coding/PQTS/docs/DEFINITION_OF_DONE.md)
  - [docs/CODEX_ENFORCER.md](/Users/jay/Document (Lcl)/Coding/PQTS/docs/CODEX_ENFORCER.md)
- Tooling gate:
  - [tools/check_codex_enforcer.py](/Users/jay/Document (Lcl)/Coding/PQTS/tools/check_codex_enforcer.py)

## Lane 1: Probabilistic Edge and Risk Core

Ref:
- `GIPP-1, GIPP-2, GIPP-3, GIPP-4, GIPP-5, GIPP-6`
- `DUNIK-1, DUNIK-2, DUNIK-3, DUNIK-6`
- `MTM-1, MTM-2, MTM-3, MTM-4, MTM-5, MTM-6, MTM-7`

Primary components:
- `src/analytics/*` (probability, EV, range/risk models)
- `src/risk/*` (kelly/VaR budgets and limits)
- `src/execution/*` (pre-submit gating and rebalance hooks)

Acceptance artifacts:
- per-trade EV decomposition
- posterior probability trace
- VaR-bounded sizing audit

## Lane 2: Spread-Capture and High-Turnover Execution

Ref:
- `MARIK-1..MARIK-8`
- `DUNIK-4, DUNIK-5, DUNIK-7, DUNIK-8`
- `MTM-8, MTM-9, MTM-10, MTM-11`

Primary components:
- `src/execution/*` (two-sided quoting, TTL exits, budgets)
- `src/markets/*` (orderbook pattern detectors)
- `src/core/*` (throughput/concurrency controls)

Acceptance artifacts:
- inventory neutrality breach logs
- micro-edge attribution report
- latency-bounded exit metrics

## Lane 3: Self-Reviewing Trade Guard

Ref:
- `ZERQ-1..ZERQ-8`
- `GIPP-8`
- `MTM-12`

Primary components:
- `src/risk/*` and `src/execution/*` pre-trade validators
- agent/challenger orchestration hooks
- prevented-trade ledger and post-mortem taxonomy

Acceptance artifacts:
- blocked-trade diagnostics
- prevented-trade accountability report
- review-latency SLO panel

## Lane 4: Terminal UX and Operator Playbook

Ref:
- `ANTP-1..ANTP-8`
- `GIPP-7`

Primary components:
- `apps/web/*` (prediction terminal and onboarding)
- `services/api/*` (freshness/latency/status APIs)
- docs playbook and evidence-linked claims surfaces

Acceptance artifacts:
- terminal indicator/source explainability
- stepwise beginner-to-operator completion markers
- claims-to-evidence lint pass

## Operational Defaults

The initial policy defaults for all lanes are tracked in:
- [config/strategy/assimilation_66_71_defaults.json](/Users/jay/Document (Lcl)/Coding/PQTS/config/strategy/assimilation_66_71_defaults.json)

