"""Cross-market dependency graph checks and violation alerts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.persistence import EventPersistenceStore


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MarketConstraint:
    constraint_id: str
    kind: str
    markets: tuple[str, ...]
    threshold: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConstraintViolation:
    constraint_id: str
    kind: str
    severity: str
    message: str
    markets: tuple[str, ...]
    observed: dict[str, float]
    threshold: float
    timestamp: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_float(value: Any) -> float:
    return float(value or 0.0)


class CrossMarketDependencyGraph:
    """Evaluate inter-market constraints against probability/state snapshots."""

    def __init__(
        self,
        *,
        constraints: list[MarketConstraint] | None = None,
        persistence_store: EventPersistenceStore | None = None,
    ) -> None:
        self._constraints = list(constraints or [])
        self._store = persistence_store

    def add_constraint(self, constraint: MarketConstraint) -> None:
        self._constraints.append(constraint)

    def evaluate(
        self,
        *,
        market_probabilities: dict[str, float],
        timestamp: str | None = None,
    ) -> list[ConstraintViolation]:
        ts = str(timestamp or _utc_now_iso())
        violations: list[ConstraintViolation] = []
        values = {str(k): _as_float(v) for k, v in dict(market_probabilities).items()}

        for constraint in self._constraints:
            kind = constraint.kind.strip().lower()
            observed = {market: values.get(market, 0.0) for market in constraint.markets}
            violation: ConstraintViolation | None = None

            if kind == "mutual_exclusion":
                total = sum(observed.values())
                if total > (1.0 + constraint.threshold):
                    violation = ConstraintViolation(
                        constraint_id=constraint.constraint_id,
                        kind=constraint.kind,
                        severity="critical",
                        message=(
                            f"Mutual exclusion violated: combined probability {total:.4f} exceeds "
                            f"limit {1.0 + constraint.threshold:.4f}."
                        ),
                        markets=constraint.markets,
                        observed=observed,
                        threshold=1.0 + constraint.threshold,
                        timestamp=ts,
                        metadata=dict(constraint.metadata),
                    )
            elif kind == "ordering":
                if len(constraint.markets) >= 2:
                    left = observed[constraint.markets[0]]
                    right = observed[constraint.markets[1]]
                    if left > (right + constraint.threshold):
                        violation = ConstraintViolation(
                            constraint_id=constraint.constraint_id,
                            kind=constraint.kind,
                            severity="warning",
                            message=(
                                f"Ordering violated: `{constraint.markets[0]}` ({left:.4f}) is greater than "
                                f"`{constraint.markets[1]}` ({right:.4f}) + margin {constraint.threshold:.4f}."
                            ),
                            markets=constraint.markets,
                            observed=observed,
                            threshold=constraint.threshold,
                            timestamp=ts,
                            metadata=dict(constraint.metadata),
                        )
            elif kind == "spread_cap":
                if len(constraint.markets) >= 2:
                    series = list(observed.values())
                    spread = max(series) - min(series)
                    if spread > constraint.threshold:
                        violation = ConstraintViolation(
                            constraint_id=constraint.constraint_id,
                            kind=constraint.kind,
                            severity="warning",
                            message=(
                                f"Spread cap violated: spread {spread:.4f} exceeds cap {constraint.threshold:.4f}."
                            ),
                            markets=constraint.markets,
                            observed=observed,
                            threshold=constraint.threshold,
                            timestamp=ts,
                            metadata=dict(constraint.metadata),
                        )

            if violation is not None:
                violations.append(violation)
                if self._store is not None:
                    self._store.append(
                        category="cross_market_dependency_violations",
                        payload=violation.to_dict(),
                        timestamp=ts,
                    )
        return violations
