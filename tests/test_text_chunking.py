"""Tests for deterministic cleanup and token-aware chunking."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research.text_chunking import chunk_text_by_tokens, deterministic_cleanup, estimate_token_count


def test_deterministic_cleanup_normalizes_whitespace() -> None:
    raw = "Line 1  \r\n\r\nLine\t\t2  \n  Line 3"
    cleaned = deterministic_cleanup(raw)
    assert cleaned == "Line 1\nLine 2\nLine 3"


def test_estimate_token_count_stable() -> None:
    text = "AAPL rose 2.5% today."
    assert estimate_token_count(text) == 8
    assert estimate_token_count(text) == 8


def test_chunk_text_by_tokens_applies_overlap() -> None:
    text = " ".join(f"token{i}" for i in range(1, 31))
    chunks = chunk_text_by_tokens(text=text, chunk_size_tokens=10, overlap_tokens=2, chunk_prefix="t")
    assert len(chunks) == 4
    assert chunks[0].token_start == 0
    assert chunks[0].token_end == 10
    assert chunks[1].token_start == 8
    assert chunks[1].token_end == 18
    assert chunks[-1].token_end == 30


def test_chunk_text_validates_overlap() -> None:
    try:
        chunk_text_by_tokens(text="hello", chunk_size_tokens=5, overlap_tokens=5)
    except ValueError as exc:
        assert "smaller than chunk_size_tokens" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
