"""Base-rate prior registry and Bayesian decision artifact helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from execution.bayesian_updates import BayesianUpdateRecord

try:
    from core.persistence import EventPersistenceStore
except ModuleNotFoundError:  # pragma: no cover
    EventPersistenceStore = Any  # type: ignore[assignment]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(token: str) -> datetime | None:
    raw = str(token).strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class BaseRatePrior:
    market_class: str
    prior_probability: float
    source: str
    updated_at: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BayesianDecisionArtifact:
    market_id: str
    market_class: str
    prior_probability: float
    posterior_probability: float
    posterior_delta: float
    market_probability: float
    model_probability: float
    expected_value_bps: float
    evidence_source: str
    evidence_ref: str
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseRatePriorRegistry:
    """Registry for mandatory base-rate priors by market class."""

    def __init__(
        self,
        *,
        persistence_store: EventPersistenceStore | None = None,
        default_max_age_seconds: int = 30 * 24 * 3600,
    ) -> None:
        self._store = persistence_store
        self._priors: dict[str, BaseRatePrior] = {}
        self.default_max_age_seconds = max(int(default_max_age_seconds), 1)
        self._hydrate_from_store()

    def _hydrate_from_store(self) -> None:
        if self._store is None:
            return
        rows = self._store.read(category="base_rate_priors", limit=100000)
        for row in reversed(rows):
            payload = dict(row.payload)
            market_class = str(payload.get("market_class", "")).strip().lower()
            if not market_class:
                continue
            try:
                prior_probability = float(payload.get("prior_probability", 0.0))
            except (TypeError, ValueError):
                continue
            if not 0.0 <= prior_probability <= 1.0:
                continue
            prior = BaseRatePrior(
                market_class=market_class,
                prior_probability=prior_probability,
                source=str(payload.get("source", "unknown")),
                updated_at=str(payload.get("updated_at", row.timestamp or _utc_now_iso())),
                metadata=dict(payload.get("metadata", {})),
            )
            self._priors[market_class] = prior

    def upsert_prior(
        self,
        *,
        market_class: str,
        prior_probability: float,
        source: str,
        metadata: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> BaseRatePrior:
        token = str(market_class).strip().lower()
        if not token:
            raise ValueError("market_class is required.")
        prior = float(prior_probability)
        if not 0.0 <= prior <= 1.0:
            raise ValueError("prior_probability must be within [0, 1].")
        row = BaseRatePrior(
            market_class=token,
            prior_probability=prior,
            source=str(source).strip() or "unknown",
            updated_at=str(timestamp or _utc_now_iso()),
            metadata=dict(metadata or {}),
        )
        self._priors[token] = row
        if self._store is not None:
            self._store.append(
                category="base_rate_priors",
                payload=row.to_dict(),
                timestamp=row.updated_at,
            )
        return row

    def get_prior(self, market_class: str) -> BaseRatePrior | None:
        token = str(market_class).strip().lower()
        if not token:
            return None
        return self._priors.get(token)

    def validate_prior(
        self,
        *,
        market_class: str,
        now_ts: str | None = None,
        max_age_seconds: int | None = None,
    ) -> tuple[bool, str, BaseRatePrior | None]:
        prior = self.get_prior(market_class)
        if prior is None:
            return False, "missing_base_rate_prior", None

        now_dt = _parse_iso(str(now_ts or _utc_now_iso()))
        prior_dt = _parse_iso(prior.updated_at)
        if now_dt is None or prior_dt is None:
            return False, "invalid_prior_timestamp", prior

        ttl = (
            self.default_max_age_seconds
            if max_age_seconds is None
            else max(int(max_age_seconds), 1)
        )
        age_seconds = int((now_dt - prior_dt).total_seconds())
        if age_seconds > ttl:
            return False, "stale_base_rate_prior", prior
        return True, "ok", prior


def build_bayesian_decision_artifact(
    *,
    market_class: str,
    update: BayesianUpdateRecord,
    market_probability: float,
    model_probability: float,
    expected_value_bps: float,
    evidence_ref: str = "",
) -> BayesianDecisionArtifact:
    prior = float(update.prior_probability)
    posterior = float(update.posterior_probability)
    return BayesianDecisionArtifact(
        market_id=str(update.market_id),
        market_class=str(market_class).strip().lower() or "unknown",
        prior_probability=prior,
        posterior_probability=posterior,
        posterior_delta=posterior - prior,
        market_probability=float(market_probability),
        model_probability=float(model_probability),
        expected_value_bps=float(expected_value_bps),
        evidence_source=str(update.evidence_source),
        evidence_ref=str(evidence_ref),
        generated_at=str(update.updated_at or _utc_now_iso()),
    )
