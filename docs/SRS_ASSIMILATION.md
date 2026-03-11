# SRS Assimilation Registry

The repository tracks SRS implementation completeness with two layers:

1. Execution TODO coverage in [docs/TODO.md](/Users/jay/Document%20(Lcl)/Coding/PQTS/docs/TODO.md)
2. Machine-readable assimilation registry in [config/srs/assimilation_registry.json](/Users/jay/Document%20(Lcl)/Coding/PQTS/config/srs/assimilation_registry.json)

## Tier Model

- `core_delivery`: requirement already covered by direct implementation work in earlier backlog waves.
- `baseline_contract`: requirement assimilated into policy/contract coverage for traceability, staged implementation, and governance checks.

## Generation

Run:

```bash
python3 tools/generate_srs_assimilation_registry.py
python3 tools/generate_srs_coverage_matrix.py
python3 tools/generate_srs_gap_backlog.py
```

## Validation

Use:

```bash
pytest -q tests/test_srs_assimilation_registry.py
```

This verifies every requirement heading in `docs/SRS.md` has exactly one registry row and no orphan IDs.
