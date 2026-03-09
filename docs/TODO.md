# PQTS Engineering TODO

Last updated: 2026-03-09 (America/Denver)

This file tracks engineering chores/fix items (not net-new product capabilities and not human-only outreach work).

## P0

- [ ] Add `LICENSE` file with MIT text and ensure repository metadata reflects license choice.
- [ ] Add GitHub Actions CI pipeline covering:
  - `pytest`
  - `ruff`
  - `mypy`
  - architecture boundary validation (`tools/check_architecture_boundaries.py`)
  - security scan
- [ ] Add README badges for CI status and package/release status.
- [ ] Finalize PyPI distribution workflow (`pip install pqts`) including release automation and publish credentials documentation.

## P1

- [ ] Add release checklist doc for version bump, changelog, package build, smoke install, and publish.
- [ ] Add CI branch protection guidance and required-check policy in docs.
