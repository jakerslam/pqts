"""Test bootstrap helpers for local source-tree imports."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

if SRC.exists():
    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path[:] = [src_str, *sys.path]

root_str = str(ROOT)
if root_str not in sys.path:
    sys.path[:] = [root_str, *sys.path]
