#!/usr/bin/env python3
"""Validate native hot-path skeleton and release matrix metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cargo", default="native/hotpath/Cargo.toml")
    parser.add_argument("--lib", default="native/hotpath/src/lib.rs")
    parser.add_argument("--matrix", default="data/reports/native/release_matrix.json")
    parser.add_argument("--module", default="pqts_hotpath")
    return parser


def main() -> int:
    from core.native_migration import build_native_release_matrix

    args = build_arg_parser().parse_args()
    cargo = Path(args.cargo)
    lib = Path(args.lib)
    matrix = Path(args.matrix)
    for path in (cargo, lib, matrix):
        if not path.exists():
            raise SystemExit(f"missing required native artifact: {path}")

    payload = json.loads(matrix.read_text(encoding="utf-8"))
    expected = build_native_release_matrix(str(args.module))
    actual_rows = payload.get("artifacts", [])
    if len(actual_rows) != len(expected):
        raise SystemExit(
            f"release matrix mismatch: expected {len(expected)} rows, found {len(actual_rows)}"
        )
    print(json.dumps({"validated": True, "rows": len(actual_rows), "module": args.module}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
