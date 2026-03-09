"""SEC submissions metadata ingestion (`CIK{cik}.json`)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from adapters.sec.client import SECClient
from adapters.sec.utils import normalize_cik


@dataclass(frozen=True)
class SubmissionRecord:
    cik_str: str
    accession_number: str
    accession_number_nodash: str
    form: str
    filing_date: str
    report_date: str | None
    primary_document: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _array(source: dict[str, Any], key: str) -> list[Any]:
    value = source.get(key, [])
    return value if isinstance(value, list) else []


def parse_submissions_recent(payload: dict[str, Any], *, cik: int | str | None = None) -> list[SubmissionRecord]:
    cik_value = cik if cik is not None else payload.get("cik")
    cik_str = normalize_cik(cik_value if cik_value is not None else payload.get("cik", "0"))

    filings = payload.get("filings", {})
    recent = filings.get("recent", {}) if isinstance(filings, dict) else {}
    if not isinstance(recent, dict):
        return []

    accession_numbers = _array(recent, "accessionNumber")
    forms = _array(recent, "form")
    filing_dates = _array(recent, "filingDate")
    report_dates = _array(recent, "reportDate")
    primary_documents = _array(recent, "primaryDocument")

    total = min(len(accession_numbers), len(forms), len(filing_dates))
    rows: list[SubmissionRecord] = []
    for idx in range(total):
        accession = str(accession_numbers[idx]).strip()
        if not accession:
            continue
        rows.append(
            SubmissionRecord(
                cik_str=cik_str,
                accession_number=accession,
                accession_number_nodash=accession.replace("-", ""),
                form=str(forms[idx]).strip(),
                filing_date=str(filing_dates[idx]).strip(),
                report_date=(
                    str(report_dates[idx]).strip() if idx < len(report_dates) and report_dates[idx] else None
                ),
                primary_document=(
                    str(primary_documents[idx]).strip()
                    if idx < len(primary_documents) and primary_documents[idx]
                    else None
                ),
            )
        )
    return rows


def ingest_submissions(client: SECClient, cik: int | str) -> list[SubmissionRecord]:
    cik_str = normalize_cik(cik)
    payload = client.get_json(f"/submissions/CIK{cik_str}.json")
    return parse_submissions_recent(payload, cik=cik_str)
