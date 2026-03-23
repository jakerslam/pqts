from __future__ import annotations

from datetime import datetime, timedelta, timezone

from research.last30days import (
    BriefingArchive,
    Last30DaysResearcher,
    MarketRecord,
    RecencyWindow,
    ResearchConfig,
    RetrievalItem,
    WatchlistStore,
    parse_intent,
    rank_polymarket_markets,
    resolve_x_handle,
    score_items,
    validate_credentials,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_recency_window_filters_and_intent_parsing() -> None:
    window = RecencyWindow.last_days(30, now=_now())
    within = window.end - timedelta(days=5)
    assert window.contains(within)
    intent = parse_intent("BTC vs ETH latest news")
    assert intent.query_type == "comparison"
    assert intent.topic.lower().startswith("btc")


def test_handle_resolution_fallbacks() -> None:
    handle, reason = resolve_x_handle("@example")
    assert handle == "example"
    assert reason == "handle_inline"
    handle, reason = resolve_x_handle("ExampleUser", handle_map={"ExampleUser": "mapped"})
    assert handle == "mapped"
    assert reason == "handle_map"
    handle, reason = resolve_x_handle("UnknownUser")
    assert handle is None
    assert reason == "fallback_keyword"


def test_score_items_and_convergence() -> None:
    window = RecencyWindow.last_days(30, now=_now())
    items = [
        RetrievalItem(
            source="news",
            title="BTC inflow surge",
            content="BTC inflow surge signals momentum",
            url="a",
            timestamp=window.end - timedelta(days=2),
            engagement=200,
            comments=10,
        ),
        RetrievalItem(
            source="forum",
            title="BTC inflow surge",
            content="BTC inflow surge signals momentum",
            url="b",
            timestamp=window.end - timedelta(days=1),
            engagement=20,
            comments=5,
        ),
    ]
    scored = score_items(items, query="btc inflow", window=window, authority_weights={"news": 1.4})
    assert scored[0].score >= scored[1].score
    assert scored[0].convergence_score >= 1.0


def test_rank_polymarket_markets() -> None:
    markets = [
        MarketRecord(market_id="1", question="BTC up today?", volume_24h=100, liquidity=200, yes_price=0.6, no_price=0.4),
        MarketRecord(market_id="2", question="ETH up today?", volume_24h=50, liquidity=100, yes_price=0.52, no_price=0.48),
    ]
    ranked = rank_polymarket_markets(markets, query="BTC price", outcome="yes")
    assert ranked[0][0].market_id == "1"


def test_credentials_validation_and_briefing_archive(tmp_path) -> None:
    config = ResearchConfig(
        sources_enabled={"news": True, "markets": False},
        credentials={"news": {"api_key": ""}},
    )
    status = validate_credentials(config)
    assert status[0].ok is False
    researcher = Last30DaysResearcher(config=config)
    window = RecencyWindow.last_days(30, now=_now())

    def news_source(_query: str):
        return [
            RetrievalItem(
                source="news",
                title="Market update",
                content="recent market update",
                url="http://example.com",
                timestamp=window.end - timedelta(days=1),
            )
        ]

    briefing = researcher.build_briefing(query="market update", sources={"news": news_source}, window=window)
    archive = BriefingArchive(root=str(tmp_path))
    path = archive.save(briefing)
    assert path.exists()


def test_watchlist_store(tmp_path) -> None:
    store = WatchlistStore(root=str(tmp_path))
    store.add("BTC")
    topics = store.list_topics()
    assert topics and topics[0]["topic"] == "BTC"
    store.record_run("BTC", summary={"ok": True})
