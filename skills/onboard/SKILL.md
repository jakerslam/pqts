# PQTS Onboard

Use this skill to move from zero to first successful paper run with safe defaults.

## Steps
1. Initialize workspace: `pqts init`.
2. Run a deterministic demo: `pqts demo`.
3. Run one template backtest: `pqts backtest momentum`.
4. Start bounded paper campaign: `pqts paper start`.

## Verification
- Confirm artifacts exist under `data/reports/demo`, `data/reports/backtest`, and `data/reports/paper`.
- Confirm no critical alerts in latest paper snapshot (`ops_health.summary.critical == 0`).

## Safety
- Keep mode in paper unless promotion gates pass.
- Do not route live credentials into local demo runs.
