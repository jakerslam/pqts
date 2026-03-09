"""Tests for SEC submissions ingestion and normalization."""

from __future__ import annotations

from adapters.sec.submissions import ingest_submissions, parse_submissions_recent


def test_parse_submissions_recent_normalizes_accession_and_dates() -> None:
    payload = {
        "cik": 320193,
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-24-000010"],
                "form": ["10-K"],
                "filingDate": ["2024-11-01"],
                "reportDate": ["2024-09-30"],
                "primaryDocument": ["a10-k.htm"],
            }
        },
    }
    rows = parse_submissions_recent(payload)
    assert len(rows) == 1
    row = rows[0]
    assert row.cik_str == "0000320193"
    assert row.form == "10-K"
    assert row.accession_number_nodash == "000032019324000010"
    assert row.report_date == "2024-09-30"


def test_ingest_submissions_builds_endpoint_path() -> None:
    class _StubClient:
        def get_json(self, path: str):  # noqa: ANN202
            assert path == "/submissions/CIK0001318605.json"
            return {
                "cik": 1318605,
                "filings": {
                    "recent": {
                        "accessionNumber": ["0001318605-24-000011"],
                        "form": ["10-Q"],
                        "filingDate": ["2024-08-01"],
                    }
                },
            }

    rows = ingest_submissions(_StubClient(), 1318605)  # type: ignore[arg-type]
    assert len(rows) == 1
    assert rows[0].form == "10-Q"
