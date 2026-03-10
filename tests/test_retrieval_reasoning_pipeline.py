"""Tests for two-stage retrieval→reasoning pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research.retrieval_reasoning_pipeline import TwoStageRetrievalReasoningPipeline


def _corpus() -> list[dict[str, object]]:
    return [
        {
            "document_id": "doc_text_a",
            "source_type": "text",
            "source_ref": "news:a",
            "text": "Revenue growth accelerated to 12 percent in Q4 and margin expanded.",
        },
        {
            "document_id": "doc_table_b",
            "source_type": "table",
            "source_ref": "table:b",
            "text": "Q4 | revenue 120 | margin 18.2",
            "metadata": {"content_type": "table"},
        },
        {
            "document_id": "doc_text_c",
            "source_type": "text",
            "source_ref": "news:c",
            "text": "Customer growth remained stable and churn declined.",
        },
    ]


def test_retrieval_assigns_stable_evidence_ids() -> None:
    pipeline = TwoStageRetrievalReasoningPipeline()
    evidence = pipeline.retrieve(query="What was Q4 revenue and margin?", corpus=_corpus(), top_k=2)
    ids = [row.evidence_id for row in evidence]
    assert ids == ["text_1", "table_1"]


def test_retrieval_reasoning_run_builds_answer_with_citations() -> None:
    pipeline = TwoStageRetrievalReasoningPipeline()
    result = pipeline.run(query="How did revenue change in Q4?", corpus=_corpus(), top_k=2)
    assert result.metadata["retrieved_count"] >= 1
    assert "text_" in result.answer or "table_" in result.answer


def test_retrieval_returns_empty_when_no_overlap() -> None:
    pipeline = TwoStageRetrievalReasoningPipeline()
    result = pipeline.run(query="volcano eruption velocity", corpus=_corpus(), top_k=2)
    assert result.evidence == []
    assert "No grounded evidence" in result.answer
