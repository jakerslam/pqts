"""Tests for canonical CIK normalization utility."""

from __future__ import annotations

import pytest

from adapters.sec.utils import normalize_cik


def test_normalize_cik_from_int() -> None:
    assert normalize_cik(320193) == "0000320193"


def test_normalize_cik_from_raw_string() -> None:
    assert normalize_cik("789019") == "0000789019"


def test_normalize_cik_preserves_padded_string() -> None:
    assert normalize_cik("0001318605") == "0001318605"


def test_normalize_cik_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        normalize_cik("")
    with pytest.raises(ValueError):
        normalize_cik("abc123")
    with pytest.raises(ValueError):
        normalize_cik(-5)
