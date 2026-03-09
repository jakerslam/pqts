"""Shared SEC adapter normalization helpers."""

from __future__ import annotations


def normalize_cik(value: int | str) -> str:
    """Return canonical zero-padded 10-digit CIK string."""
    if isinstance(value, int):
        if value < 0:
            raise ValueError("CIK must be non-negative.")
        return f"{value:010d}"

    text = str(value).strip()
    if not text:
        raise ValueError("CIK cannot be empty.")
    if not text.isdigit():
        raise ValueError("CIK must contain only digits.")
    return f"{int(text):010d}"
