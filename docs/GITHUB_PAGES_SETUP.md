# GitHub Pages Setup

Last updated: 2026-03-10 (America/Denver)

## Current Status

Pages publish workflow is wired (`.github/workflows/publish-leaderboard.yml`) and runs successfully through site build, but deployment is blocked until repository Pages is enabled.

Observed workflow error:

- `Get Pages site failed: Not Found`
- `Create Pages site failed: Resource not accessible by integration`

## One-Time Repository Setup (Owner/Admin)

1. Open repository settings: `Settings -> Pages`.
2. Set source to **GitHub Actions**.
3. Save settings and confirm Pages is enabled for the repository.

## After Enablement

1. Re-run workflow: `Publish Docs Site` (workflow dispatch), or push any docs change.
2. Verify deployment URL appears in workflow summary.
3. Confirm URL resolves: `https://jakerslam.github.io/pqts/`.

## Fallback Artifact

Until Pages is enabled, the generated leaderboard remains available in-repo:

- `docs/leaderboard/index.html`
