# Native Hot-Path (Rust + PyO3)

Last updated: 2026-03-10 (America/Denver)

## Objective

Keep PQTS Python-first while moving compute-critical kernels to Rust when JIT-first migration evidence is insufficient.

## Current Native Kernel

- Crate: `native/hotpath`
- Module: `pqts_hotpath`
- Exported functions:
  - `version()`
  - `sum_notional(levels, max_levels)`
  - `fill_metrics(side, reference_price, executed_price, requested_qty, executed_qty)`
  - `sequence_transition(expected_sequence, received_sequence, allow_auto_recover, snapshot_sequence)`
  - `uniform_from_seed(seed)`
  - `event_id_hash(prefix, payload, hex_len)`
  - `paper_fill_metrics(side, requested_qty, reference_price, queue_qty, ...)`
  - `smart_router_score(spread, volume_24h, fee_bps, slippage_ratio, fill_ratio, latency_ms)`
  - `quote_state(price, age_seconds, stale_after_seconds)`

Integrated call sites via `src/core/hotpath_runtime.py`:

- `sum_notional` -> `src/execution/microstructure_features.py`
- `sequence_transition` -> `src/execution/orderbook_sequence.py`
- `fill_metrics` -> `src/execution/event_replay.py` and `src/execution/risk_aware_router.py`
- `paper_fill_metrics` and `uniform_from_seed` -> `src/execution/paper_fill_model.py`
- `smart_router_score` -> `src/execution/smart_router.py`
- `quote_state` -> `src/execution/market_data_resilience.py`
- `event_id_hash` -> `src/execution/ws_ingestion.py` and `src/execution/shadow_stream_worker.py`

## Runtime Behavior

- Default behavior: attempt native module, safely fall back to Python implementation when unavailable.
- Disable native path explicitly: `PQTS_NATIVE_HOTPATH=0`.

## Build Notes

Native builds use `maturin`.

Example local build (editable):

```bash
pip install maturin
maturin develop --manifest-path native/hotpath/Cargo.toml
```

## Verification

- Contract check: `python3 tools/check_native_hotpath.py`
- Runtime check: `pytest -q tests/test_hotpath_runtime.py tests/test_microstructure_features.py tests/test_orderbook_sequence.py tests/test_event_replay.py tests/test_execution_tuning.py tests/test_market_data_resilience.py tests/test_ws_ingestion.py tests/test_shadow_stream_worker.py tests/test_smart_router_urgency_ladder.py`

## Release Matrix

Target matrix is tracked in `data/reports/native/release_matrix.json` and validated by `tools/check_native_hotpath.py`.
