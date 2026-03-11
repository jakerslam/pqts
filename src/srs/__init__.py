"""SRS assimilation registry helpers."""

from .assimilation_registry import (
    AssimilatedRequirement,
    ensure_srs_assimilation_coverage,
    load_assimilation_registry,
    summarize_assimilation_registry,
)

__all__ = [
    "AssimilatedRequirement",
    "ensure_srs_assimilation_coverage",
    "load_assimilation_registry",
    "summarize_assimilation_registry",
]
