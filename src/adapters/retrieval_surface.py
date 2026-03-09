"""Unified multi-source retrieval surface with provenance metadata."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RetrievalRecord:
    source_type: str
    source_id: str
    title: str
    content: str
    url: str | None
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _build_record(
    *,
    source_type: str,
    payload: dict[str, Any],
    rank: int,
    query: str,
) -> RetrievalRecord:
    source_id = str(
        payload.get("id")
        or payload.get("source_id")
        or payload.get("ticker")
        or payload.get("accession_number")
        or payload.get("url")
        or f"{source_type}-{rank}"
    )
    title = str(payload.get("title") or payload.get("name") or source_id)
    content = str(payload.get("content") or payload.get("summary") or "")
    url = str(payload["url"]) if payload.get("url") else None
    score = float(payload.get("score", 0.0))
    metadata = dict(payload.get("metadata", {}) or {})
    provenance = {
        "source_type": source_type,
        "rank": rank,
        "query": query,
        "retrieved_at": _now_iso(),
        "raw_id": source_id,
    }
    return RetrievalRecord(
        source_type=source_type,
        source_id=source_id,
        title=title,
        content=content,
        url=url,
        score=score,
        metadata=metadata,
        provenance=provenance,
    )


def merge_retrieval_sources(
    *,
    query: str,
    structured_financial: list[dict[str, Any]],
    market_data: list[dict[str, Any]],
    web_news: list[dict[str, Any]],
    limit_per_source: int = 20,
) -> list[RetrievalRecord]:
    limited = max(int(limit_per_source), 1)
    merged: list[RetrievalRecord] = []

    for rank, payload in enumerate(structured_financial[:limited], start=1):
        merged.append(
            _build_record(
                source_type="structured_financial",
                payload=payload,
                rank=rank,
                query=query,
            )
        )
    for rank, payload in enumerate(market_data[:limited], start=1):
        merged.append(
            _build_record(
                source_type="market_data",
                payload=payload,
                rank=rank,
                query=query,
            )
        )
    for rank, payload in enumerate(web_news[:limited], start=1):
        merged.append(
            _build_record(
                source_type="web_news",
                payload=payload,
                rank=rank,
                query=query,
            )
        )

    merged.sort(key=lambda item: item.score, reverse=True)
    return merged


@dataclass
class MultiSourceRetrievalSurface:
    structured_fetcher: Callable[[str], list[dict[str, Any]]]
    market_fetcher: Callable[[str], list[dict[str, Any]]]
    web_fetcher: Callable[[str], list[dict[str, Any]]]

    def retrieve(self, query: str, *, limit_per_source: int = 20) -> list[RetrievalRecord]:
        return merge_retrieval_sources(
            query=query,
            structured_financial=self.structured_fetcher(query),
            market_data=self.market_fetcher(query),
            web_news=self.web_fetcher(query),
            limit_per_source=limit_per_source,
        )
