"""Two-stage retrieval→reasoning pipeline with stable evidence identifiers."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(str(text or "").lower()))


def _infer_content_type(row: dict[str, Any]) -> str:
    metadata = row.get("metadata", {})
    if isinstance(metadata, dict):
        content_type = str(metadata.get("content_type", "")).strip().lower()
        if content_type == "table":
            return "table"
    source_type = str(row.get("source_type", "")).strip().lower()
    if source_type == "table":
        return "table"
    return "text"


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    content_type: str
    document_id: str
    score: float
    snippet: str
    source_ref: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievalReasoningResult:
    query: str
    answer: str
    evidence: list[EvidenceRecord]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = [row.to_dict() for row in self.evidence]
        return payload


class TwoStageRetrievalReasoningPipeline:
    """Deterministic lexical retrieval followed by evidence-grounded response composition."""

    def retrieve(
        self,
        *,
        query: str,
        corpus: Iterable[dict[str, Any]],
        top_k: int = 5,
    ) -> list[EvidenceRecord]:
        query_tokens = _tokenize(query)
        scored: list[tuple[float, dict[str, Any]]] = []

        for row in list(corpus):
            if not isinstance(row, dict):
                continue
            text = str(row.get("text", "")).strip()
            if not text:
                continue
            doc_tokens = _tokenize(text)
            if not doc_tokens:
                continue
            overlap = query_tokens.intersection(doc_tokens)
            score = len(overlap) / max(len(query_tokens), 1)
            if score <= 0:
                continue
            scored.append((float(score), row))

        scored.sort(
            key=lambda item: (
                -item[0],
                str(item[1].get("document_id", "")),
            )
        )
        selected = scored[: max(int(top_k), 1)]

        text_counter = 0
        table_counter = 0
        evidence: list[EvidenceRecord] = []
        for score, row in selected:
            content_type = _infer_content_type(row)
            if content_type == "table":
                table_counter += 1
                evidence_id = f"table_{table_counter}"
            else:
                text_counter += 1
                evidence_id = f"text_{text_counter}"
            snippet = str(row.get("text", ""))[:220].strip()
            evidence.append(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    content_type=content_type,
                    document_id=str(row.get("document_id", "")),
                    score=float(score),
                    snippet=snippet,
                    source_ref=str(row.get("source_ref", "")),
                )
            )
        return evidence

    def reason(self, *, query: str, evidence: list[EvidenceRecord]) -> str:
        if not evidence:
            return "No grounded evidence found for this query."
        lead = evidence[0]
        citations = ", ".join(item.evidence_id for item in evidence[:3])
        return (
            f"Answer derived from {citations}: "
            f"{lead.snippet}"
        )

    def run(
        self,
        *,
        query: str,
        corpus: Iterable[dict[str, Any]],
        top_k: int = 5,
    ) -> RetrievalReasoningResult:
        evidence = self.retrieve(query=query, corpus=corpus, top_k=top_k)
        answer = self.reason(query=query, evidence=evidence)
        return RetrievalReasoningResult(
            query=str(query),
            answer=answer,
            evidence=evidence,
            metadata={
                "top_k": int(top_k),
                "retrieved_count": len(evidence),
            },
        )
