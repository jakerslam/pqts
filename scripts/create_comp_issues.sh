#!/usr/bin/env bash
set -euo pipefail

# Creates COMP-1..COMP-14 GitHub issues from docs/COMP_ISSUES_DRAFT.md sections.
# Requires: gh auth token with issues:write on target repo.
#
# Usage:
#   scripts/create_comp_issues.sh jakerslam/PQTS

repo="${1:-jakerslam/PQTS}"
draft="docs/COMP_ISSUES_DRAFT.md"

if [[ ! -f "${draft}" ]]; then
  echo "Missing ${draft}"
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

awk '
  /^## COMP-[0-9]+/ {
    if (out != "") close(out)
    key=$2
    gsub(":", "", key)
    out=sprintf("%s/%s.md", ENVIRON["TMP_OUT"], key)
    print $0 > out
    next
  }
  out != "" { print $0 >> out }
' TMP_OUT="${tmpdir}" "${draft}"

for file in "${tmpdir}"/COMP-*.md; do
  [[ -f "${file}" ]] || continue
  title="$(head -n 1 "${file}" | sed 's/^## //')"
  body="$(tail -n +2 "${file}")"
  labels="enhancement"
  if [[ "${title}" == *"[P0]"* ]]; then
    labels="enhancement"
  fi
  gh issue create --repo "${repo}" --title "${title}" --label "${labels}" --body "${body}"
done

echo "Created COMP issue set in ${repo}"
