# API Migrations

Baseline SQL migrations for the FastAPI service persistence layer live in this directory.

## Current baseline

- `0001_initial.sql`: creates canonical persistence tables for:
  - `api_accounts`
  - `api_positions`
  - `api_orders`
  - `api_fills`
  - `api_pnl_snapshots`
  - `api_risk_states`
  - `api_risk_incidents`

## Apply manually (Postgres)

```bash
psql "$PQTS_DATABASE_URL" -f services/api/migrations/0001_initial.sql
```

For local development, the API also performs `create_all()` schema initialization at startup.
