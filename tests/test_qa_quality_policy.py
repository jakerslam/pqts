"""Tests for standalone and grounded QA quality policy."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research.qa_quality_policy import evaluate_qa_quality_policy


def test_quality_policy_accepts_grounded_standalone_item() -> None:
    result = evaluate_qa_quality_policy(
        {
            "question": "What was operating margin in Q4 2025?",
            "answer": "Operating margin in Q4 2025 was 18.2 percent.",
            "context": [
                "Q4 2025 operating margin reported at 18.2%.",
                "Management guidance remained unchanged.",
            ],
        }
    )
    assert result.is_valid is True
    assert result.violations == []


def test_quality_policy_rejects_source_referential_answer() -> None:
    result = evaluate_qa_quality_policy(
        {
            "question": "What did revenue do year over year?",
            "answer": "According to the text, revenue increased by 12%.",
            "context": ["Revenue increased by 12% year over year."],
        }
    )
    assert result.is_valid is False
    assert any("source_referential_leakage" in item for item in result.violations)


def test_quality_policy_rejects_non_standalone_question() -> None:
    result = evaluate_qa_quality_policy(
        {
            "question": "Based on the passage, what changed in cash flow?",
            "answer": "Operating cash flow increased by 5 million.",
            "context": ["Operating cash flow increased by 5 million in Q4."],
        }
    )
    assert result.is_valid is False
    assert any("question_not_standalone" in item for item in result.violations)
