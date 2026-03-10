# COMP Issue Drafts

Use with:

```bash
scripts/create_comp_issues.sh jakerslam/PQTS
```

## COMP-1 [P0]: Documentation Availability and Metadata Integrity Gate

### Summary
Implement docs and package metadata URL checks as gating CI/release controls.

### SRS Reference
- COMP-1

### Dependencies
- None

### Acceptance Criteria
- Required public URLs are checked in CI and release.
- Any 4xx/5xx on required docs links fails the gate.
- Package metadata docs URL resolves successfully.

## COMP-2 [P0]: Semantic Release and Distribution Credibility

### Summary
Enforce semantic release integrity and provenance artifacts in release pipeline.

### SRS Reference
- COMP-2

### Dependencies
- COMP-1

### Acceptance Criteria
- Release tags map to semantic version.
- `CHANGELOG.md` contains matching version section.
- `SHA256SUMS.txt` and `release_metadata.json` are published with release artifacts.

## COMP-3 [P0]: Public Benchmark Quality Gate + Diagnostic Classification

### Summary
Classify benchmark outputs as `reference` or `diagnostic_only` using explicit quality thresholds.

### SRS Reference
- COMP-3

### Dependencies
- COMP-4
- COMP-5

### Acceptance Criteria
- Non-zero fill and reject-rate threshold checks are enforced.
- Result class is machine-readable in monthly artifacts.
- `diagnostic_only` outputs are excluded from reference summaries.

## COMP-4 [P1]: Golden Dataset and Provenance Governance

### Summary
Require versioned dataset manifests and comparability controls for public benchmark reports.

### SRS Reference
- COMP-4

### Dependencies
- COMP-2

### Acceptance Criteria
- Benchmark reports pin dataset/version metadata.
- Cross-dataset comparisons are explicitly marked.
- Dataset changes require version bump + migration note.

## COMP-5 [P1]: Reference Strategy Pack Publication Standard

### Summary
Maintain at least three versioned reference packs with reproducible artifacts.

### SRS Reference
- COMP-5

### Dependencies
- COMP-4

### Acceptance Criteria
- At least three reference packs are maintained.
- Each includes run command, config snapshot, metrics, artifact hashes.
- Pack refresh includes prior-vs-current regression diff.

## COMP-6 [P1]: One Engine / Two Surface Architecture Contract

### Summary
Expose one canonical engine through `Studio` and `Core` surfaces without semantic divergence.

### SRS Reference
- COMP-6

### Dependencies
- COMP-9

### Acceptance Criteria
- Studio/Core adapter boundaries documented and enforced.
- Shared execution/risk/promotion services used by both surfaces.
- Contract tests guard against surface drift.

## COMP-7 [P1]: Studio Casual UX Contract

### Summary
Implement paper-first Studio UX with guided onboarding and plain-language explanations.

### SRS Reference
- COMP-7

### Dependencies
- COMP-6
- COMP-11
- COMP-12

### Acceptance Criteria
- Guided paper-first flow works without manual env editing on first success.
- Trade/risk block explanations are human-readable.
- One-click paper campaign launch exists in Studio.

## COMP-8 [P1]: Core Professional UX Contract

### Summary
Ensure Core provides deterministic replay and advanced execution analytics across CLI/API/notebook surfaces.

### SRS Reference
- COMP-8

### Dependencies
- COMP-6
- COMP-9

### Acceptance Criteria
- Replay/provenance workflows available in Core.
- TCA/shortfall/reconciliation and canary controls are available.
- Local and hosted deployment parity checks cover critical paths.

## COMP-9 [P1]: Surface Parity and Traceability

### Summary
Map Studio actions to Core-equivalent commands/APIs with shared event IDs.

### SRS Reference
- COMP-9

### Dependencies
- COMP-6

### Acceptance Criteria
- Every Studio action has auditable Core mapping.
- UI can reveal underlying config/code representation.
- Cross-surface trace IDs are consistent.

## COMP-10 [P1]: Wedge-First Scope Governance

### Summary
Gate market expansion behind execution/reliability readiness controls.

### SRS Reference
- COMP-10

### Dependencies
- Human decision: wedge market selection

### Acceptance Criteria
- Primary wedge market is explicitly configured.
- Expansion requires readiness-gate pass.
- Simultaneous broad multi-market expansion is blocked by policy.

## COMP-11 [P0]: First-Success CLI Path

### Summary
Provide `pqts init/demo/backtest/paper` onboarding path with safe defaults.

### SRS Reference
- COMP-11

### Dependencies
- COMP-1

### Acceptance Criteria
- `init`, `demo`, `backtest`, `paper start` commands work with safe defaults.
- No manual virtualenv step required for default first-success path.
- Commands emit actionable next-step guidance.
- Quickstart docs are CLI-first.

## COMP-12 [P1]: Template-First / Code-Visible Workflow

### Summary
Support template-first execution while preserving code/config visibility and diffability.

### SRS Reference
- COMP-12

### Dependencies
- COMP-11

### Acceptance Criteria
- Template actions persist explicit config/code artifacts.
- Users can transition from template mode to code mode without loss.
- Behavior-changing template actions produce diffable output.

## COMP-13 [P1]: Public Claim Evidence Policy

### Summary
Enforce evidence linkage for performance claims and mandatory label classes.

### SRS Reference
- COMP-13

### Dependencies
- COMP-3
- COMP-4

### Acceptance Criteria
- Claims require linked reproducible artifacts and provenance.
- Unsupported claims are marked `unverified`.
- Public reporting distinguishes `reference`, `diagnostic_only`, `unverified`.

## COMP-14 [P1]: Tiering Safety Baseline and Entitlement Policy

### Summary
Encode tier capabilities in policy while preserving paper-first and live-gate safety.

### SRS Reference
- COMP-14

### Dependencies
- Human decision: pricing/tier copy

### Acceptance Criteria
- Entitlement policy defines Community/Solo Pro/Team/Enterprise.
- Live enablement requires paper-readiness + explicit acknowledgment in all tiers.
- No tier bypasses core risk/promotion gates.
