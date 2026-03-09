# PyPI Trusted Publishing Setup

This project publishes to PyPI via GitHub Actions using OpenID Connect (OIDC),
without storing long-lived API tokens.

## 1) Create PyPI Project

- Create `pqts` project on PyPI (or claim the project name if available).

## 2) Configure Trusted Publisher on PyPI

In PyPI project settings, add a trusted publisher with:

- Owner: `jakerslam`
- Repository: `pqts`
- Workflow: `release.yml`
- Environment: `pypi`

## 3) Configure GitHub Environment

In GitHub repo settings, create environment `pypi` and optionally add:

- required reviewers
- deployment branch/tag restrictions

## 4) Publish Flow

1. Update version/changelog.
2. Tag release: `vX.Y.Z`.
3. Push tag: `git push origin vX.Y.Z`.
4. Workflow `.github/workflows/release.yml` builds distributions, creates GitHub Release, and publishes to PyPI.

## 5) Smoke Test

```bash
pip install pqts==X.Y.Z
pqts --help
```
