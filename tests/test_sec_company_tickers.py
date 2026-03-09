"""Tests for SEC company_tickers ingestion and normalization."""

from __future__ import annotations

from adapters.sec.issuer_registry import ingest_company_tickers, parse_company_tickers


def test_parse_company_tickers_handles_indexed_payload() -> None:
    payload = {
        "0": {"ticker": "AAPL", "title": "Apple Inc.", "cik_str": 320193},
        "1": {"ticker": "MSFT", "title": "Microsoft Corp.", "cik_str": 789019},
    }
    rows = parse_company_tickers(payload)
    assert [row.ticker for row in rows] == ["AAPL", "MSFT"]
    assert rows[0].cik == 320193
    assert rows[0].cik_str == "0000320193"


def test_parse_company_tickers_skips_invalid_rows() -> None:
    payload = {
        "0": {"ticker": "", "title": "Missing ticker", "cik_str": 1},
        "1": {"ticker": "OK", "title": "Good row", "cik_str": 42},
        "2": {"ticker": "MISS", "title": "Missing cik"},
    }
    rows = parse_company_tickers(payload)
    assert len(rows) == 1
    assert rows[0].ticker == "OK"


def test_ingest_company_tickers_uses_client_endpoint() -> None:
    class _StubClient:
        def get_json(self, path: str):  # noqa: ANN202
            assert path == "/files/company_tickers.json"
            return {"0": {"ticker": "TSLA", "title": "Tesla", "cik_str": 1318605}}

    rows = ingest_company_tickers(_StubClient())  # type: ignore[arg-type]
    assert len(rows) == 1
    assert rows[0].ticker == "TSLA"
