"""Per-chunk question budget allocation with strict global cap enforcement."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ChunkBudget:
    chunk_id: str
    token_count: int
    relevance: float
    questions_allocated: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def allocate_question_budget(
    *,
    chunks: Iterable[dict[str, Any]],
    global_question_cap: int,
    minimum_questions_per_chunk: int = 0,
) -> list[ChunkBudget]:
    rows = [dict(row) for row in list(chunks) if isinstance(row, dict)]
    if global_question_cap < 0:
        raise ValueError("global_question_cap must be >= 0")
    if minimum_questions_per_chunk < 0:
        raise ValueError("minimum_questions_per_chunk must be >= 0")
    if not rows:
        return []

    budgets: list[ChunkBudget] = []
    for row in rows:
        chunk_id = str(row.get("chunk_id", "")).strip()
        if not chunk_id:
            continue
        token_count = max(int(float(row.get("token_count", 0) or 0)), 0)
        relevance = max(float(row.get("relevance", 1.0) or 0.0), 0.0)
        budgets.append(
            ChunkBudget(
                chunk_id=chunk_id,
                token_count=token_count,
                relevance=relevance,
                questions_allocated=0,
            )
        )
    if not budgets:
        return []

    ordered = sorted(budgets, key=lambda item: item.chunk_id)
    limit = int(global_question_cap)
    remaining = limit

    # Baseline per-chunk floor (if budget allows).
    floor = int(minimum_questions_per_chunk)
    if floor > 0 and remaining > 0:
        for idx, row in enumerate(ordered):
            assign = min(floor, remaining)
            ordered[idx] = ChunkBudget(
                chunk_id=row.chunk_id,
                token_count=row.token_count,
                relevance=row.relevance,
                questions_allocated=assign,
            )
            remaining -= assign
            if remaining <= 0:
                break

    if remaining <= 0:
        return ordered

    # Proportional allocation based on token_count * relevance.
    weights = [max(float(row.token_count) * float(row.relevance), 1.0) for row in ordered]
    total_weight = sum(weights)
    provisional: list[int] = []
    for weight in weights:
        alloc = int((remaining * weight) / total_weight)
        provisional.append(alloc)

    used = sum(provisional)
    spare = remaining - used
    if spare > 0:
        # Deterministic tie-breaking by highest weight then chunk_id.
        ranking = sorted(
            range(len(ordered)),
            key=lambda idx: (-weights[idx], ordered[idx].chunk_id),
        )
        for idx in ranking:
            if spare <= 0:
                break
            provisional[idx] += 1
            spare -= 1

    allocated: list[ChunkBudget] = []
    for row, extra in zip(ordered, provisional, strict=False):
        allocated.append(
            ChunkBudget(
                chunk_id=row.chunk_id,
                token_count=row.token_count,
                relevance=row.relevance,
                questions_allocated=row.questions_allocated + int(extra),
            )
        )
    return allocated
