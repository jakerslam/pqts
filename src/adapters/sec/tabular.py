"""Tabular normalization helpers for SEC analytics payloads."""

from __future__ import annotations

from typing import Any

from adapters.sec.companyconcept import CompanyConceptPoint
from adapters.sec.companyfacts import CompanyFactPoint
from adapters.sec.submissions import SubmissionRecord


def companyfacts_to_table(rows: list[CompanyFactPoint]) -> list[dict[str, Any]]:
    normalized = [
        {
            "cik_str": row.cik_str,
            "taxonomy": row.taxonomy,
            "concept": row.concept,
            "unit": row.unit,
            "value": row.value,
            "end": row.end,
            "form": row.form,
            "accession_number": row.accession_number,
            "filed": row.filed,
        }
        for row in rows
    ]
    normalized.sort(key=lambda row: (row["end"] or "", row["accession_number"] or ""))
    return normalized


def companyconcept_to_table(rows: list[CompanyConceptPoint]) -> list[dict[str, Any]]:
    normalized = [
        {
            "cik_str": row.cik_str,
            "taxonomy": row.taxonomy,
            "concept": row.concept,
            "unit": row.unit,
            "value": row.value,
            "end": row.end,
            "form": row.form,
            "accession_number": row.accession_number,
            "filed": row.filed,
        }
        for row in rows
    ]
    normalized.sort(key=lambda row: (row["end"] or "", row["accession_number"] or ""))
    return normalized


def submissions_to_table(rows: list[SubmissionRecord]) -> list[dict[str, Any]]:
    normalized = [
        {
            "cik_str": row.cik_str,
            "accession_number": row.accession_number,
            "accession_number_nodash": row.accession_number_nodash,
            "form": row.form,
            "filing_date": row.filing_date,
            "report_date": row.report_date,
            "primary_document": row.primary_document,
        }
        for row in rows
    ]
    normalized.sort(key=lambda row: (row["filing_date"], row["accession_number"]))
    return normalized
