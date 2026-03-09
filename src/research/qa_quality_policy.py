"""Grounded standalone QA quality-policy checks."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from research.function_call_schema import QAFunctionCallItem, validate_function_call_item

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
LEAKAGE_PATTERNS = (
    "according to the text",
    "according to the passage",
    "in the passage",
    "the passage says",
    "the source says",
    "as mentioned above",
    "in the context provided",
)
NON_STANDALONE_QUESTION_PATTERNS = (
    "in this passage",
    "from the text above",
    "based on the passage",
    "according to this text",
)


@dataclass(frozen=True)
class QAQualityPolicyResult:
    is_valid: bool
    violations: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _token_set(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(str(text or "").lower()))


def evaluate_qa_quality_policy(payload: QAFunctionCallItem | dict[str, Any]) -> QAQualityPolicyResult:
    item = payload if isinstance(payload, QAFunctionCallItem) else validate_function_call_item(payload)
    violations: list[str] = []

    question = item.question.strip()
    answer = item.answer.strip()
    context_blob = " ".join(item.context).strip()
    q_lower = question.lower()
    a_lower = answer.lower()

    for pattern in NON_STANDALONE_QUESTION_PATTERNS:
        if pattern in q_lower:
            violations.append(f"question_not_standalone:{pattern}")
            break

    for pattern in LEAKAGE_PATTERNS:
        if pattern in a_lower:
            violations.append(f"source_referential_leakage:{pattern}")
            break

    answer_tokens = _token_set(answer)
    context_tokens = _token_set(context_blob)
    overlap = answer_tokens.intersection(context_tokens)
    grounding_ratio = len(overlap) / max(len(answer_tokens), 1)
    if grounding_ratio < 0.20:
        violations.append("insufficient_grounding_overlap")

    if len(answer_tokens) < 3:
        violations.append("answer_too_short")

    return QAQualityPolicyResult(
        is_valid=not violations,
        violations=violations,
        metrics={
            "answer_token_count": float(len(answer_tokens)),
            "context_token_count": float(len(context_tokens)),
            "grounding_overlap_ratio": float(grounding_ratio),
        },
    )
