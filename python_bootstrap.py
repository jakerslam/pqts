"""Shared Python import-path bootstrap for repository tooling.

Execution entry points that are launched directly from the repository root need
the project root and `src` directory to be importable.
"""

from __future__ import annotations

from pathlib import Path
import sys


def ensure_repo_python_path() -> None:
    repo_root = Path(__file__).resolve().parent
    src_root = repo_root / "src"
    additions = [str(repo_root)]
    if src_root.exists():
        additions.append(str(src_root))
    additions = [entry for entry in additions if entry not in sys.path]
    if additions:
        sys.path = [*additions, *sys.path]
