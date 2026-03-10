"""Tests for blind/private evaluation mode and submission validation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research.blind_evaluation import (
    build_blind_evaluation_set,
    score_blind_submission,
    validate_submission_schema,
)


def test_build_blind_evaluation_set_hides_answers() -> None:
    items = build_blind_evaluation_set(
        [
            {"question": "Q1 revenue?", "answer": "120", "context": ["rev=120"]},
            {"question": "Q2 revenue?", "answer": "130", "context": ["rev=130"]},
        ]
    )
    assert len(items) == 2
    assert hasattr(items[0], "item_id")
    assert not hasattr(items[0], "answer")


def test_validate_submission_schema_strict_rejects_extra_keys() -> None:
    with pytest.raises(ValueError, match="unexpected keys"):
        validate_submission_schema(
            [{"item_id": "a", "answer": "b", "extra": "x"}],
            strict=True,
        )


def test_score_blind_submission_exact_match() -> None:
    items = build_blind_evaluation_set(
        [
            {"question": "Q1 revenue?", "answer": "120", "context": ["rev=120"]},
            {"question": "Q2 revenue?", "answer": "130", "context": ["rev=130"]},
        ]
    )
    answer_key = {items[0].item_id: "120", items[1].item_id: "130"}
    score = score_blind_submission(
        submission_rows=[
            {"item_id": items[0].item_id, "answer": "120"},
            {"item_id": items[1].item_id, "answer": "999"},
        ],
        answer_key=answer_key,
    )
    assert score.total_items == 2
    assert score.exact_match_count == 1
    assert score.exact_match_rate == 0.5
