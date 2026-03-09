#!/usr/bin/env python3
"""Apply SQL migration files for services/api persistence."""

from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import create_engine


def apply_migrations(database_url: str, migrations_dir: Path) -> int:
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    files = sorted(path for path in migrations_dir.glob("*.sql") if path.is_file())
    if not files:
        return 0

    engine = create_engine(database_url, future=True, pool_pre_ping=True)
    with engine.begin() as conn:
        for path in files:
            sql = path.read_text(encoding="utf-8").strip()
            if not sql:
                continue
            conn.exec_driver_sql(sql)
            print(f"Applied migration: {path.name}")
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        required=True,
        help="Target database URL (Postgres recommended).",
    )
    parser.add_argument(
        "--migrations-dir",
        default="services/api/migrations",
        help="Directory containing ordered .sql migration files.",
    )
    args = parser.parse_args()

    applied = apply_migrations(
        database_url=args.database_url,
        migrations_dir=Path(args.migrations_dir).resolve(),
    )
    print(f"Migration run complete. Files applied: {applied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
