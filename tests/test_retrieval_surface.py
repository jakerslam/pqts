"""Tests for multi-source retrieval surface with provenance."""

from __future__ import annotations

from adapters.retrieval_surface import MultiSourceRetrievalSurface, merge_retrieval_sources


def test_merge_retrieval_sources_includes_all_source_types() -> None:
    merged = merge_retrieval_sources(
        query="apple outlook",
        structured_financial=[{"id": "sec-1", "title": "10-K", "content": "filing", "score": 0.9}],
        market_data=[{"id": "mkt-1", "title": "Quote", "content": "price", "score": 0.7}],
        web_news=[{"id": "news-1", "title": "News", "content": "headline", "score": 0.8}],
    )
    assert len(merged) == 3
    source_types = {row.source_type for row in merged}
    assert source_types == {"structured_financial", "market_data", "web_news"}
    assert all("retrieved_at" in row.provenance for row in merged)
    assert all(row.provenance["query"] == "apple outlook" for row in merged)


def test_retrieval_surface_calls_each_fetcher() -> None:
    calls: list[str] = []

    def _structured(query: str) -> list[dict[str, object]]:
        calls.append(f"structured:{query}")
        return [{"id": "a", "content": "A", "score": 0.1}]

    def _market(query: str) -> list[dict[str, object]]:
        calls.append(f"market:{query}")
        return [{"id": "b", "content": "B", "score": 0.2}]

    def _web(query: str) -> list[dict[str, object]]:
        calls.append(f"web:{query}")
        return [{"id": "c", "content": "C", "score": 0.3}]

    surface = MultiSourceRetrievalSurface(
        structured_fetcher=_structured,
        market_fetcher=_market,
        web_fetcher=_web,
    )
    rows = surface.retrieve("fomc", limit_per_source=1)
    assert len(rows) == 3
    assert calls == ["structured:fomc", "market:fomc", "web:fomc"]
