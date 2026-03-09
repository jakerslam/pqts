"""Tests for unified corpus ingestion pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research.corpus_ingestion import UnifiedCorpusIngestor


def test_ingest_text_list_normalizes_and_filters_empty_rows() -> None:
    ingestor = UnifiedCorpusIngestor()
    docs = ingestor.ingest_text_list(
        source_ref="notes",
        texts=["  Hello  world  ", "", "Line 1\n\nLine 2"],
    )
    assert len(docs) == 2
    assert docs[0].source_type == "text_list"
    assert docs[0].text == "Hello  world"
    assert docs[1].text == "Line 1\nLine 2"


def test_ingest_pdf_url_uses_fetcher_and_normalizes() -> None:
    ingestor = UnifiedCorpusIngestor(pdf_fetcher=lambda _url: b"PDF\n\ncontent  ")
    doc = ingestor.ingest_pdf_url(pdf_url="https://example.com/sample.pdf", title="Sample PDF")
    assert doc.source_type == "pdf_url"
    assert doc.title == "Sample PDF"
    assert doc.text == "PDF\ncontent"


def test_ingest_sec_forms_includes_10k_10q_only() -> None:
    ingestor = UnifiedCorpusIngestor()
    docs = ingestor.ingest_sec_forms(
        filings=[
            {
                "form": "10-K",
                "cik": "789019",
                "accession": "0000789019-26-000001",
                "filing_date": "2026-02-01",
                "text": "Annual report body",
            },
            {"form": "8-K", "cik": "789019", "text": "current report body"},
            {
                "form": "10-Q",
                "cik": "789019",
                "accession": "0000789019-26-000002",
                "filing_date": "2026-03-01",
                "text": "Quarterly report body",
            },
        ]
    )
    assert len(docs) == 2
    assert {doc.metadata["form"] for doc in docs} == {"10-K", "10-Q"}


def test_ingest_all_merges_all_sources() -> None:
    ingestor = UnifiedCorpusIngestor(pdf_fetcher=lambda _url: "pdf text")
    docs = ingestor.ingest_all(
        text_source_ref="research_notes",
        texts=["alpha note"],
        pdf_urls=["https://example.com/a.pdf"],
        sec_filings=[{"form": "10-Q", "cik": "1", "accession": "x", "text": "sec body"}],
    )
    assert [doc.source_type for doc in docs] == ["text_list", "pdf_url", "sec_form"]
