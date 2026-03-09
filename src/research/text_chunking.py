"""Deterministic text cleanup and token-aware chunking helpers."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def deterministic_cleanup(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(text or ""))
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n")]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def estimate_token_count(text: str) -> int:
    return len(TOKEN_PATTERN.findall(str(text or "")))


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    text: str
    token_count: int
    token_start: int
    token_end: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def chunk_text_by_tokens(
    *,
    text: str,
    chunk_size_tokens: int = 300,
    overlap_tokens: int = 40,
    chunk_prefix: str = "chunk",
) -> list[TextChunk]:
    if chunk_size_tokens <= 0:
        raise ValueError("chunk_size_tokens must be > 0")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens must be >= 0")
    if overlap_tokens >= chunk_size_tokens:
        raise ValueError("overlap_tokens must be smaller than chunk_size_tokens")

    cleaned = deterministic_cleanup(text)
    tokens = TOKEN_PATTERN.findall(cleaned)
    if not tokens:
        return []

    chunks: list[TextChunk] = []
    start = 0
    index = 1
    stride = chunk_size_tokens - overlap_tokens

    while start < len(tokens):
        end = min(start + chunk_size_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = " ".join(chunk_tokens)
        chunks.append(
            TextChunk(
                chunk_id=f"{chunk_prefix}_{index:04d}",
                text=chunk_text,
                token_count=len(chunk_tokens),
                token_start=start,
                token_end=end,
                metadata={
                    "chunk_index": index,
                    "total_tokens": len(tokens),
                    "cleaned_length": len(cleaned),
                },
            )
        )
        if end >= len(tokens):
            break
        start += stride
        index += 1

    return chunks
