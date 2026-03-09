# Branch Protection Guidance

Recommended protection for `main`:

- Require pull request before merge.
- Require status checks to pass before merge:
  - `Verify CI YAML on GitHub Raw`
  - `Verify Dependency Lock`
  - `Pytest`
  - `Lint`
  - `Coverage`
- Require branches to be up to date before merging.
- Require conversation resolution before merge.
- Restrict force pushes and branch deletion.

Optional hardening:

- Require CODEOWNERS review for protected paths.
- Enable signed commits.
- Restrict who can push to `main`.
