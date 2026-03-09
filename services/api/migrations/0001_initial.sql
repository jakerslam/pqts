-- PQTS API persistence baseline migration.

CREATE TABLE IF NOT EXISTS api_accounts (
  account_id TEXT PRIMARY KEY,
  payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS api_positions (
  position_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_positions_account_id ON api_positions(account_id);

CREATE TABLE IF NOT EXISTS api_orders (
  order_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_orders_account_id ON api_orders(account_id);

CREATE TABLE IF NOT EXISTS api_fills (
  fill_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_fills_account_id ON api_fills(account_id);

CREATE TABLE IF NOT EXISTS api_pnl_snapshots (
  snapshot_id BIGSERIAL PRIMARY KEY,
  account_id TEXT NOT NULL,
  payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_pnl_snapshots_account_id ON api_pnl_snapshots(account_id);

CREATE TABLE IF NOT EXISTS api_risk_states (
  account_id TEXT PRIMARY KEY,
  payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS api_risk_incidents (
  incident_id BIGSERIAL PRIMARY KEY,
  account_id TEXT NOT NULL,
  payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_risk_incidents_account_id ON api_risk_incidents(account_id);
