# Implementation Direction

Last updated: 2026-03-09 (America/Denver)

## North-Star Objectives

1. Fast to run
2. Maintainable
3. Easy to understand
4. Easy to add new modules
5. Easy for AI coders to traverse and modify safely

## Architecture Direction

- Primary architecture: modular monolith.
- Canonical layers:
  - `src/app/` composition and runtime entrypoints
  - `src/contracts/` typed interfaces and event/context contracts
  - `src/modules/` domain module lifecycle units
  - `src/adapters/` external I/O integrations
- Existing domain packages remain in place during migration and are composed through `src/app/`.

## Language Direction

- Python remains the system default for runtime, execution logic, risk gating, and orchestration.
- The product target is Python-first (not Python-only): user-facing surface remains mostly Python, while hot-path kernels migrate to Rust when profiling triggers are met.
- FastAPI is the canonical control plane; all active surfaces consume API contracts.
- Next.js (`apps/web`) is the primary external Studio surface.
- Dash (`src/dashboard/start.py`) remains operator/internal fallback during cutover windows.
- DuckDB/Polars/PyArrow remain the preferred analytical data-plane stack for heavy scan/aggregation paths.
- R remains supported as an optional research validator bridge for experiment gate metrics.

## R Integration Position

- Implemented and available:
  - `src/research/r_analytics_bridge.py`
  - `scripts/r/validate_experiment.R`
- Intended role:
  - optional validation layer for research promotion gates
  - not a required dependency for core trading runtime
- Default posture:
  - enabled selectively where research rigor benefits from R-side stats workflows

## Delivery Rules

- Incremental migration only; no destabilizing rewrites.
- Preserve CLI/script compatibility while moving logic into canonical layers.
- Keep one primary runtime path per release phase (no mixed Streamlit/Dash runtime ambiguity).
- Enforce typed boundaries (Pydantic models) for runtime config, API payloads, and strategy manifests.
- Every structural change should include:
  - boundary validation (`tools/check_architecture_boundaries.py`)
  - architecture map check (`tools/print_architecture_map.py`)
  - stack-direction validation (`tools/check_stack_direction.py`)
  - focused tests for new contracts/tooling.

## Compliance References

- `docs/CODEX_COMPLIANCE.md`
- `docs/ARCHITECTURE.md`
