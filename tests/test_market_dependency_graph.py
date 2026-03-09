"""Tests for cross-market dependency graph constraints."""

from __future__ import annotations

from core.persistence import EventPersistenceStore
from execution.market_dependency_graph import CrossMarketDependencyGraph, MarketConstraint


def test_mutual_exclusion_constraint_emits_violation(tmp_path) -> None:
    store = EventPersistenceStore(dsn=f"sqlite:///{tmp_path / 'events.db'}")
    graph = CrossMarketDependencyGraph(
        constraints=[
            MarketConstraint(
                constraint_id="winner_exclusion",
                kind="mutual_exclusion",
                markets=("candidate_a_win", "candidate_b_win"),
                threshold=0.02,
            )
        ],
        persistence_store=store,
    )

    violations = graph.evaluate(
        market_probabilities={"candidate_a_win": 0.61, "candidate_b_win": 0.51},
        timestamp="2026-03-09T01:00:00+00:00",
    )
    assert len(violations) == 1
    assert violations[0].kind == "mutual_exclusion"
    persisted = store.read(category="cross_market_dependency_violations", limit=10)
    assert len(persisted) == 1
    assert persisted[0].payload["constraint_id"] == "winner_exclusion"


def test_ordering_constraint_and_spread_cap() -> None:
    graph = CrossMarketDependencyGraph(
        constraints=[
            MarketConstraint(
                constraint_id="ordering_1",
                kind="ordering",
                markets=("future_price_up", "spot_price_up"),
                threshold=0.01,
            ),
            MarketConstraint(
                constraint_id="spread_1",
                kind="spread_cap",
                markets=("venue_a_up", "venue_b_up", "venue_c_up"),
                threshold=0.05,
            ),
        ]
    )

    violations = graph.evaluate(
        market_probabilities={
            "future_price_up": 0.80,
            "spot_price_up": 0.60,
            "venue_a_up": 0.52,
            "venue_b_up": 0.60,
            "venue_c_up": 0.71,
        }
    )
    ids = {row.constraint_id for row in violations}
    assert ids == {"ordering_1", "spread_1"}
