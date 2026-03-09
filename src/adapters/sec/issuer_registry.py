"""Ticker-to-CIK registry ingestion for SEC `company_tickers.json`."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from adapters.sec.client import SECClient


@dataclass(frozen=True)
class IssuerRecord:
    ticker: str
    title: str
    cik: int
    cik_str: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _extract_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "data" in payload and isinstance(payload["data"], list):
        return [row for row in payload["data"] if isinstance(row, dict)]
    entries: list[dict[str, Any]] = []
    for value in payload.values():
        if isinstance(value, dict):
            entries.append(value)
    return entries


def parse_company_tickers(payload: dict[str, Any]) -> list[IssuerRecord]:
    rows: list[IssuerRecord] = []
    for item in _extract_entries(payload):
        ticker = str(item.get("ticker", "")).strip().upper()
        title = str(item.get("title", "")).strip()
        cik_raw = item.get("cik_str")
        if not ticker or cik_raw is None:
            continue
        cik = int(cik_raw)
        rows.append(
            IssuerRecord(
                ticker=ticker,
                title=title,
                cik=cik,
                cik_str=f"{cik:010d}",
            )
        )
    rows.sort(key=lambda row: (row.ticker, row.cik))
    return rows


def ingest_company_tickers(client: SECClient) -> list[IssuerRecord]:
    payload = client.get_json("/files/company_tickers.json")
    return parse_company_tickers(payload)
