"""Tests for SEC tabular normalization helpers."""

from __future__ import annotations

from adapters.sec.companyconcept import CompanyConceptPoint
from adapters.sec.companyfacts import CompanyFactPoint
from adapters.sec.submissions import SubmissionRecord
from adapters.sec.tabular import (
    companyconcept_to_table,
    companyfacts_to_table,
    submissions_to_table,
)


def test_companyfacts_to_table_preserves_traceability_fields() -> None:
    rows = [
        CompanyFactPoint(
            cik_str="0000320193",
            taxonomy="us-gaap",
            concept="Assets",
            unit="USD",
            value=10.0,
            end="2024-12-31",
            form="10-K",
            accession_number="0001",
            filed="2025-01-01",
        )
    ]
    table = companyfacts_to_table(rows)
    assert table[0]["accession_number"] == "0001"
    assert table[0]["end"] == "2024-12-31"


def test_companyconcept_to_table_preserves_fields() -> None:
    rows = [
        CompanyConceptPoint(
            cik_str="0000789019",
            taxonomy="us-gaap",
            concept="Assets",
            unit="USD",
            value=1.0,
            end="2024-12-31",
            form="10-K",
            filed="2025-01-01",
            accession_number="0002",
        )
    ]
    table = companyconcept_to_table(rows)
    assert table[0]["taxonomy"] == "us-gaap"
    assert table[0]["accession_number"] == "0002"


def test_submissions_to_table_keeps_report_date_and_accession() -> None:
    rows = [
        SubmissionRecord(
            cik_str="0001318605",
            accession_number="0001318605-24-000011",
            accession_number_nodash="000131860524000011",
            form="10-Q",
            filing_date="2024-08-01",
            report_date="2024-06-30",
            primary_document="q2.htm",
        )
    ]
    table = submissions_to_table(rows)
    assert table[0]["report_date"] == "2024-06-30"
    assert table[0]["accession_number"] == "0001318605-24-000011"
