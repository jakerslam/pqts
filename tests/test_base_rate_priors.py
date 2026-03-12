from __future__ import annotations

from core.persistence import EventPersistenceStore
from execution.base_rate_priors import BaseRatePriorRegistry, build_bayesian_decision_artifact
from execution.bayesian_updates import BayesianProbabilityEngine


def test_base_rate_prior_registry_requires_and_validates_fresh_priors(tmp_path) -> None:
    store = EventPersistenceStore(dsn=f"sqlite:///{tmp_path / 'priors.db'}")
    registry = BaseRatePriorRegistry(persistence_store=store, default_max_age_seconds=3600)

    ok, reason, prior = registry.validate_prior(market_class="crypto_binary")
    assert ok is False
    assert reason == "missing_base_rate_prior"
    assert prior is None

    inserted = registry.upsert_prior(
        market_class="crypto_binary",
        prior_probability=0.41,
        source="historical_base_rate",
        timestamp="2026-03-12T00:00:00+00:00",
    )
    assert inserted.market_class == "crypto_binary"

    ok, reason, prior = registry.validate_prior(
        market_class="crypto_binary",
        now_ts="2026-03-12T00:30:00+00:00",
    )
    assert ok is True
    assert reason == "ok"
    assert prior is not None
    assert prior.prior_probability == 0.41


def test_build_bayesian_decision_artifact_includes_prior_posterior_delta() -> None:
    engine = BayesianProbabilityEngine(default_alpha=2.0, default_beta=2.0)
    update = engine.update(
        market_id="btc_breakout",
        evidence_successes=3.0,
        evidence_failures=1.0,
        evidence_source="signal_ensemble",
    )
    artifact = build_bayesian_decision_artifact(
        market_class="crypto_binary",
        update=update,
        market_probability=0.51,
        model_probability=0.57,
        expected_value_bps=14.2,
        evidence_ref="bundle_2026_03_12",
    )
    payload = artifact.to_dict()
    assert payload["prior_probability"] == 0.5
    assert payload["posterior_probability"] == 5.0 / 8.0
    assert payload["posterior_delta"] > 0.0
    assert payload["market_class"] == "crypto_binary"
