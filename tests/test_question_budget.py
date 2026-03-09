"""Tests for per-chunk question budget allocation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research.question_budget import allocate_question_budget


def test_allocate_question_budget_respects_global_cap() -> None:
    budgets = allocate_question_budget(
        chunks=[
            {"chunk_id": "c1", "token_count": 100, "relevance": 1.0},
            {"chunk_id": "c2", "token_count": 200, "relevance": 2.0},
            {"chunk_id": "c3", "token_count": 300, "relevance": 1.0},
        ],
        global_question_cap=12,
    )
    assert sum(row.questions_allocated for row in budgets) == 12


def test_allocate_question_budget_applies_floor_when_possible() -> None:
    budgets = allocate_question_budget(
        chunks=[{"chunk_id": "a", "token_count": 10}, {"chunk_id": "b", "token_count": 10}],
        global_question_cap=3,
        minimum_questions_per_chunk=1,
    )
    result = {row.chunk_id: row.questions_allocated for row in budgets}
    assert result["a"] >= 1
    assert result["b"] >= 1
    assert sum(result.values()) == 3


def test_allocate_question_budget_tie_break_is_deterministic() -> None:
    chunks = [
        {"chunk_id": "x", "token_count": 100, "relevance": 1.0},
        {"chunk_id": "y", "token_count": 100, "relevance": 1.0},
        {"chunk_id": "z", "token_count": 100, "relevance": 1.0},
    ]
    first = allocate_question_budget(chunks=chunks, global_question_cap=5)
    second = allocate_question_budget(chunks=chunks, global_question_cap=5)
    assert [row.questions_allocated for row in first] == [row.questions_allocated for row in second]
