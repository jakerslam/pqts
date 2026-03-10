"""Blind/private evaluation mode and strict submission schema validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Iterable


@dataclass(frozen=True)
class BlindEvaluationItem:
    item_id: str
    question: str
    context: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SubmissionRecord:
    item_id: str
    answer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SubmissionScore:
    total_items: int
    exact_match_count: int
    exact_match_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


REQUIRED_SUBMISSION_KEYS = {"item_id", "answer"}


def _item_id(question: str, context: list[str]) -> str:
    token = f"{question}|{'|'.join(context)}"
    return f"blind_{sha256(token.encode('utf-8')).hexdigest()[:16]}"


def build_blind_evaluation_set(rows: Iterable[dict[str, Any]]) -> list[BlindEvaluationItem]:
    items: list[BlindEvaluationItem] = []
    for row in list(rows):
        if not isinstance(row, dict):
            continue
        question = str(row.get("question", "")).strip()
        answer = str(row.get("answer", "")).strip()
        context_raw = row.get("context", [])
        if not question or not answer:
            continue
        if isinstance(context_raw, str):
            context = [context_raw.strip()] if context_raw.strip() else []
        elif isinstance(context_raw, list):
            context = [str(item).strip() for item in context_raw if str(item).strip()]
        else:
            context = []
        items.append(
            BlindEvaluationItem(
                item_id=_item_id(question, context),
                question=question,
                context=context,
            )
        )
    return items


def validate_submission_schema(rows: Iterable[dict[str, Any]], *, strict: bool = True) -> list[SubmissionRecord]:
    records: list[SubmissionRecord] = []
    for idx, row in enumerate(list(rows), start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Submission row {idx} must be an object.")
        keys = set(row.keys())
        missing = REQUIRED_SUBMISSION_KEYS - keys
        if missing:
            raise ValueError(f"Submission row {idx} missing required keys: {sorted(missing)}")
        if strict:
            extra = keys - REQUIRED_SUBMISSION_KEYS
            if extra:
                raise ValueError(f"Submission row {idx} has unexpected keys: {sorted(extra)}")

        item_id = str(row.get("item_id", "")).strip()
        answer = str(row.get("answer", "")).strip()
        if not item_id or not answer:
            raise ValueError(f"Submission row {idx} has empty item_id/answer.")
        records.append(SubmissionRecord(item_id=item_id, answer=answer))
    return records


def score_blind_submission(
    *,
    submission_rows: Iterable[dict[str, Any]],
    answer_key: dict[str, str],
) -> SubmissionScore:
    submission = validate_submission_schema(submission_rows, strict=True)
    total = len(submission)
    if total == 0:
        return SubmissionScore(total_items=0, exact_match_count=0, exact_match_rate=0.0)

    exact = 0
    for row in submission:
        expected = str(answer_key.get(row.item_id, "")).strip().lower()
        observed = row.answer.strip().lower()
        if expected and observed == expected:
            exact += 1
    return SubmissionScore(
        total_items=total,
        exact_match_count=exact,
        exact_match_rate=exact / total,
    )
