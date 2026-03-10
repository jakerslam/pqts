# PQTS Paper Review

Use this skill for a deterministic daily paper-ops review and readiness check.

## Steps
1. Run campaign + readiness pipeline:
   `python3 scripts/daily_paper_ops.py --config config/paper.yaml --require-no-critical-alerts`
2. Run monthly attribution report if needed:
   `python3 scripts/monthly_attribution_report.py --db-path data/research.db --stage paper --lookback-days 90`
3. Generate review summary and bounded tuning proposals:
   `python3 scripts/run_nightly_strategy_review.py --snapshot auto`

## Outputs
- Daily ops summary JSON in `data/reports/`.
- Nightly review JSON in `data/reports/nightly_review/`.
- Optional override patch YAML when `--write-overrides` is provided.

## Safety
- Review proposals before applying config changes.
- Keep adjustments bounded and reversible.
