"""Leakage regression tests for preprocessing + schema integrity pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research.function_call_schema import validate_function_call_item
from research.qa_quality_policy import evaluate_qa_quality_policy
from research.text_chunking import deterministic_cleanup


def test_preprocessing_does_not_mutate_semantic_content() -> None:
    raw = "  Revenue grew 12%  \n\n margin improved  "
    cleaned = deterministic_cleanup(raw)
    assert "Revenue grew 12%" in cleaned
    assert "margin improved" in cleaned


def test_schema_integrity_rejects_prompt_leakage_fields() -> None:
    with pytest.raises(ValueError, match="Unexpected keys"):
        validate_function_call_item(
            {
                "question": "What changed in revenue?",
                "answer": "Revenue increased.",
                "context": "Q4 notes",
                "prompt": "hidden chain-of-thought",
            },
            strict=True,
        )


def test_quality_policy_catches_source_referential_phrase_regression() -> None:
    result = evaluate_qa_quality_policy(
        {
            "question": "What was gross margin in Q4?",
            "answer": "In the passage, gross margin was 54%.",
            "context": ["Gross margin was 54% in Q4."],
        }
    )
    assert result.is_valid is False
    assert any("source_referential_leakage" in violation for violation in result.violations)
