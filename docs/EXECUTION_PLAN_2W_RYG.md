# Two-Week RYG Execution Plan

Last updated: 2026-03-10 (America/Denver)

Goal: close trust-surface contradictions and enforce one canonical web/control-plane contract before adding net-new feature breadth.

## Red (Immediate, blocker-level)

1. Web/API contract coherence
- Status: `done`
- Scope: force web client to consume canonical FastAPI `/v1` contract for account/portfolio/execution/risk paths with auth headers and typed mapping.
- Exit criteria: no `/api/v1/*` pseudo-contract usage in core dashboard data fetches.

2. Version truth consistency
- Status: `done`
- Scope: keep API service version in lockstep with package version (`pyproject.toml`) instead of hardcoded service defaults.
- Exit criteria: API `/health` and `/ready` report active package version.

3. Docs/runtime truth consistency
- Status: `done`
- Scope: maintain one preferred onboarding path in README and keep source/dev path explicitly secondary.
- Exit criteria: no conflicting “first command” narratives across README/quickstart.

## Yellow (High ROI, next)

1. Thin-client completion for web routes
- Status: `done`
- Scope: replace in-memory/file-backed web API shims (`promotion`, `operator/actions`, `order-truth`, `execution-quality`, `replay`, `template-gallery`) with FastAPI-backed endpoints.
- Exit criteria: Next routes become proxy-only or are removed where direct backend access is used.

2. Public proof plumbing
- Status: `in_progress`
- Scope: scheduled benchmark workflow and monthly artifact pipeline kept green; publish fallback docs artifact while Pages permission gap remains.
- Exit criteria: weekly artifact pipeline consistently passes and is externally reachable (Pages or fallback artifact).

3. Backlog/documentation drift control
- Status: `in_progress`
- Scope: mark historical issue templates as non-canonical; keep `docs/TODO.md` as single active backlog.
- Exit criteria: no stale “future” claims for already-shipped surfaces.

## Green (Scale and validation)

1. External cohort validation
- Status: `pending`
- Scope: recruit external beginner/pro cohorts, run scripted flows, and publish measured friction outcomes.
- Exit criteria: non-zero external cohort counts and release-window evidence in user-research artifacts.

2. Market-claim calibration
- Status: `pending`
- Scope: keep messaging aligned with `crypto_first` and integration-certification maturity.
- Exit criteria: public copy reflects staged expansion and experimental status where applicable.

3. Operational hardening continuity
- Status: `in_progress`
- Scope: keep certified-paper gate, native latency regression gate, and chaos/recovery suite in CI/nightly.
- Exit criteria: no silent regressions on these gates across two release cycles.
