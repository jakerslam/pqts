# PQTS Priority TODO (ROI + Dependency Ordered)

Last updated: 2026-03-10 (America/Denver)

Execution rule: complete sections top-to-bottom. Items in the same section can run in parallel only if dependencies are satisfied.

Legend:
- `ROI`: `very_high`, `high`, `medium`
- `Type`: `engineering` or `human_only`
- `Ref`: SRS requirement IDs

## 00. Already Completed (Pinned)

- [x] `COMP-1` docs/metadata URL gate in CI + release (`ROI: very_high`, `Type: engineering`)
- [x] `COMP-2` semantic release integrity + changelog/version + artifact checksums/metadata (`ROI: very_high`, `Type: engineering`)
- [x] `COMP-3` benchmark quality classification (`reference` vs `diagnostic_only`) (`ROI: very_high`, `Type: engineering`)
- [x] `COMP-11` first-success CLI path (`pqts init/demo/backtest/paper`) (`ROI: very_high`, `Type: engineering`)
- [x] Monthly report + benchmark provenance pipeline (`ROI: high`, `Type: engineering`)
- [x] Streamlit deprecation milestone doc baseline (`ROI: medium`, `Type: engineering`)

## 01. Immediate Blockers (Do Next)

- [ ] Finalize and sign human decisions in [docs/HUMAN_DECISIONS_LOG.md](/Users/jay/Document%20(Lcl)/Coding/PQTS/docs/HUMAN_DECISIONS_LOG.md):
  - `Decision 001` wedge market
  - `Decision 002` trust label policy
  - `Decision 003` primary UI path
  - `Decision 004` native migration triggers
  - (`ROI: very_high`, `Type: human_only`, `Ref: COMP-10, COMP-13, LANG-6, LANG-3`)
- [ ] Create `COMP-1..COMP-14` GitHub issue set using [scripts/create_comp_issues.sh](/Users/jay/Document%20(Lcl)/Coding/PQTS/scripts/create_comp_issues.sh) once token has `issues:write`.
  - (`ROI: very_high`, `Type: engineering`, `Ref: COMP-*`)

## 02. Credibility Gap Closure (Public Trust)

- [ ] Implement `COMP-4` golden dataset/version governance checks in benchmark pipeline.
  - (`ROI: very_high`, `Type: engineering`, `Ref: COMP-4`)
- [ ] Implement `COMP-5` reference strategy pack standard (3+ packs + diff-against-prior).
  - (`ROI: very_high`, `Type: engineering`, `Ref: COMP-5`, depends on `COMP-4`)
- [ ] Implement `COMP-13` claim evidence policy linting/enforcement for public docs/reports.
  - (`ROI: very_high`, `Type: engineering`, `Ref: COMP-13`, depends on `COMP-3`, `COMP-4`)
- [ ] Lift at least one benchmark suite from `diagnostic_only` to `reference` class by improving fill/reject outcomes.
  - (`ROI: very_high`, `Type: engineering`, `Ref: COMP-3`, depends on execution-quality improvements)

## 03. Product Coherence (One Engine, Clear Surfaces)

- [ ] Implement `COMP-6` one-engine/two-surface architecture contract and guardrails.
  - (`ROI: high`, `Type: engineering`, `Ref: COMP-6`)
- [ ] Implement `COMP-9` Studio↔Core traceability/parity tests for mapped actions.
  - (`ROI: high`, `Type: engineering`, `Ref: COMP-9`, depends on `COMP-6`)
- [ ] Implement `LANG-6` UI surface coherence in runtime/deploy flows (no mixed-framework ambiguity).
  - (`ROI: high`, `Type: engineering`, `Ref: LANG-6`, depends on `Decision 003`)
- [ ] Implement `LANG-7` FastAPI-centered control-plane contract across active UI.
  - (`ROI: high`, `Type: engineering`, `Ref: LANG-7`, depends on `COMP-6`, `LANG-6`)
- [ ] Implement `LANG-11` staged UI migration safety gates and rollback checks.
  - (`ROI: high`, `Type: engineering`, `Ref: LANG-11`, depends on `LANG-6`, `COMP-9`)

## 04. Studio/Core Product Lanes

- [ ] Implement `COMP-7` Studio casual UX contract (paper-first guided path + explanations + one-click paper campaign).
  - (`ROI: high`, `Type: engineering`, `Ref: COMP-7`, depends on `COMP-6`, `COMP-11`, `COMP-12`)
- [ ] Implement `COMP-8` Core pro UX contract (CLI/API/notebook parity + replay/TCA/shortfall/reconciliation path).
  - (`ROI: high`, `Type: engineering`, `Ref: COMP-8`, depends on `COMP-6`, `COMP-9`)
- [ ] Implement `COMP-12` template-first/code-visible workflow with diffable artifacts.
  - (`ROI: high`, `Type: engineering`, `Ref: COMP-12`, depends on `COMP-11`)
- [ ] Implement `COMP-14` entitlement policy baseline with paper-first/live-gate invariants.
  - (`ROI: high`, `Type: engineering`, `Ref: COMP-14`, depends on packaging decisions from humans)

## 05. Language + Runtime Evolution (Python-First / Native-Selective)

- [ ] Implement `LANG-5` Pydantic-first contract hardening for config/payload/manifest boundaries.
  - (`ROI: high`, `Type: engineering`, `Ref: LANG-5`)
- [ ] Implement `LANG-4` research data plane baseline (Arrow-native schema path + local analytical storage integration).
  - (`ROI: high`, `Type: engineering`, `Ref: LANG-4`)
- [ ] Implement `LANG-8` storage-tier policy checks (local analytics vs operational state boundaries).
  - (`ROI: medium`, `Type: engineering`, `Ref: LANG-8`)
- [ ] Implement `LANG-9` mode-specific cycle/refresh SLO telemetry and reporting.
  - (`ROI: high`, `Type: engineering`, `Ref: LANG-9`)
- [ ] Implement `LANG-2` native hot-path boundary skeleton (packaging/build/tests for extension boundary).
  - (`ROI: medium`, `Type: engineering`, `Ref: LANG-2`, depends on `Decision 004`)
- [ ] Implement `LANG-3` migration trigger instrumentation (JIT-first evidence, native promotion thresholds).
  - (`ROI: medium`, `Type: engineering`, `Ref: LANG-3`, depends on `LANG-9`, `Decision 004`)
- [ ] Implement `LANG-10` native artifact distribution matrix in release pipeline.
  - (`ROI: medium`, `Type: engineering`, `Ref: LANG-10`, depends on `LANG-2`)
- [ ] Enforce `LANG-12` stack/performance claim labeling in public outputs.
  - (`ROI: medium`, `Type: engineering`, `Ref: LANG-12`, depends on `COMP-13`)

## 06. Human-Only Commercial and Positioning Work (Parallel Lane)

- [ ] Finalize packaging/pricing narrative and lane definitions (Community/Solo Pro/Team/Enterprise).
  - (`ROI: high`, `Type: human_only`, `Ref: COMP-14`)
- [ ] Maintain dated public competitor comparison narrative with evidence.
  - (`ROI: high`, `Type: human_only`, `Ref: COMP-13`)
- [ ] Sign off benchmark commentary each cycle (reference/diagnostic/unverified correctness).
  - (`ROI: high`, `Type: human_only`, `Ref: COMP-13`, `Decision 002`)
- [ ] Run user interviews (casual + pro cohorts) and feed outcomes into roadmap priorities.
  - (`ROI: high`, `Type: human_only`, `Ref: COMP-7`, `COMP-8`)
