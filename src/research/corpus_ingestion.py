"""Unified multi-source corpus ingestion and normalization pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Callable, Iterable


def _normalize_text(value: str) -> str:
    # Normalize whitespace while preserving paragraph boundaries.
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    normalized = "\n".join(line for line in lines if line)
    return normalized.strip()


def _doc_id(*parts: str) -> str:
    token = "|".join(str(part) for part in parts)
    return f"doc_{sha256(token.encode('utf-8')).hexdigest()[:16]}"


@dataclass(frozen=True)
class CorpusDocument:
    document_id: str
    source_type: str
    source_ref: str
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class UnifiedCorpusIngestor:
    """Ingest text lists, PDF URLs, and SEC forms into one normalized document envelope."""

    def __init__(
        self,
        *,
        pdf_fetcher: Callable[[str], str | bytes] | None = None,
    ) -> None:
        self._pdf_fetcher = pdf_fetcher or (lambda _url: "")

    def ingest_text_list(
        self,
        *,
        source_ref: str,
        texts: Iterable[str],
    ) -> list[CorpusDocument]:
        docs: list[CorpusDocument] = []
        for idx, raw in enumerate(list(texts), start=1):
            normalized = _normalize_text(raw)
            if not normalized:
                continue
            title = f"{source_ref} text {idx}"
            docs.append(
                CorpusDocument(
                    document_id=_doc_id("text_list", source_ref, str(idx), normalized[:80]),
                    source_type="text_list",
                    source_ref=str(source_ref),
                    title=title,
                    text=normalized,
                    metadata={"index": idx},
                )
            )
        return docs

    def ingest_pdf_url(self, *, pdf_url: str, title: str | None = None) -> CorpusDocument:
        raw = self._pdf_fetcher(str(pdf_url))
        if isinstance(raw, bytes):
            extracted = raw.decode("utf-8", errors="replace")
        else:
            extracted = str(raw)
        normalized = _normalize_text(extracted)
        resolved_title = title or f"PDF {pdf_url}"
        return CorpusDocument(
            document_id=_doc_id("pdf_url", pdf_url, normalized[:80]),
            source_type="pdf_url",
            source_ref=str(pdf_url),
            title=str(resolved_title),
            text=normalized,
            metadata={"url": str(pdf_url)},
        )

    def ingest_sec_forms(
        self,
        *,
        filings: Iterable[dict[str, Any]],
        include_forms: tuple[str, ...] = ("10-K", "10-Q"),
    ) -> list[CorpusDocument]:
        allowed = {token.upper().strip() for token in include_forms}
        docs: list[CorpusDocument] = []
        for row in list(filings):
            if not isinstance(row, dict):
                continue
            form = str(row.get("form", "")).upper().strip()
            if form not in allowed:
                continue
            cik = str(row.get("cik", "")).strip()
            accession = str(row.get("accession", row.get("accession_number", ""))).strip()
            filing_date = str(row.get("filing_date", row.get("report_date", ""))).strip()
            primary_document = str(row.get("primary_document", row.get("document", ""))).strip()
            source_ref = f"sec:{cik}:{accession}"

            body = _normalize_text(str(row.get("text", row.get("body", ""))))
            if not body:
                continue
            title = f"{form} {cik or 'unknown'} {filing_date or accession}"
            docs.append(
                CorpusDocument(
                    document_id=_doc_id("sec_form", form, cik, accession, body[:80]),
                    source_type="sec_form",
                    source_ref=source_ref,
                    title=title,
                    text=body,
                    metadata={
                        "form": form,
                        "cik": cik,
                        "accession": accession,
                        "filing_date": filing_date,
                        "primary_document": primary_document,
                    },
                )
            )
        return docs

    def ingest_all(
        self,
        *,
        text_source_ref: str,
        texts: Iterable[str],
        pdf_urls: Iterable[str],
        sec_filings: Iterable[dict[str, Any]],
    ) -> list[CorpusDocument]:
        docs: list[CorpusDocument] = []
        docs.extend(self.ingest_text_list(source_ref=text_source_ref, texts=texts))
        for pdf_url in list(pdf_urls):
            docs.append(self.ingest_pdf_url(pdf_url=str(pdf_url)))
        docs.extend(self.ingest_sec_forms(filings=sec_filings))
        return docs
