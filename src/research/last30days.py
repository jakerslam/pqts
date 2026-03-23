"""Recency-bounded multi-source research utilities (Last30Days assimilation)."""

from __future__ import annotations

import hashlib
import json
import math
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_HANDLE_RE = re.compile(r"@([A-Za-z0-9_]{1,32})")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(str(text or "").lower()))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class RecencyWindow:
    start: datetime
    end: datetime
    days: int = 30

    @classmethod
    def last_days(cls, days: int = 30, *, now: datetime | None = None) -> "RecencyWindow":
        safe_days = max(1, int(days))
        now_ts = now or _utc_now()
        end = now_ts
        start = now_ts - timedelta(days=safe_days)
        return cls(start=start, end=end, days=safe_days)

    def contains(self, ts: datetime | None) -> bool:
        if ts is None:
            return False
        return self.start <= ts <= self.end


@dataclass(frozen=True)
class ResearchIntent:
    topic: str
    target: str
    query_type: str


@dataclass(frozen=True)
class CredentialStatus:
    source: str
    ok: bool
    missing: list[str] = field(default_factory=list)
    message: str = ""


@dataclass(frozen=True)
class ResearchConfig:
    sources_enabled: Mapping[str, bool] = field(default_factory=dict)
    credentials: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    authority_weights: Mapping[str, float] = field(default_factory=dict)
    comment_weight: float = 0.05
    max_workers: int = 6
    timeout_seconds: float = 15.0


@dataclass(frozen=True)
class RetrievalItem:
    source: str
    title: str
    content: str
    url: str
    timestamp: datetime | None
    engagement: float = 0.0
    comments: float = 0.0

    def tokens(self) -> set[str]:
        return _tokenize(f"{self.title} {self.content}")


@dataclass(frozen=True)
class ScoredItem:
    item: RetrievalItem
    score: float
    recency_score: float
    overlap_score: float
    authority_score: float
    engagement_score: float
    convergence_score: float


@dataclass(frozen=True)
class Briefing:
    query: str
    intent: ResearchIntent
    window: RecencyWindow
    sources: list[str]
    coverage: Mapping[str, int]
    citations: list[str]
    ranked: list[ScoredItem]
    notes: list[str] = field(default_factory=list)


def parse_intent(query: str) -> ResearchIntent:
    query_text = str(query or "").strip()
    lowered = query_text.lower()
    query_type = "general"
    if " vs " in lowered or " versus " in lowered:
        query_type = "comparison"
    elif "recommend" in lowered or "best" in lowered:
        query_type = "recommendations"
    elif "prompt" in lowered:
        query_type = "prompts"
    elif "news" in lowered or "latest" in lowered or "recent" in lowered:
        query_type = "news"

    target = query_text
    topic = query_text.split(" vs ")[0] if " vs " in lowered else query_text
    return ResearchIntent(topic=topic.strip(), target=target.strip(), query_type=query_type)


def resolve_x_handle(entity: str, *, handle_map: Mapping[str, str] | None = None) -> tuple[str | None, str]:
    handle_map = handle_map or {}
    entity_clean = str(entity or "").strip()
    match = _HANDLE_RE.search(entity_clean)
    if match:
        return match.group(1), "handle_inline"
    mapped = handle_map.get(entity_clean)
    if mapped:
        return str(mapped).lstrip("@"), "handle_map"
    return None, "fallback_keyword"


def validate_credentials(config: ResearchConfig) -> list[CredentialStatus]:
    results: list[CredentialStatus] = []
    for source, enabled in config.sources_enabled.items():
        if not enabled:
            results.append(CredentialStatus(source=source, ok=True, missing=[], message="disabled"))
            continue
        required = config.credentials.get(source, {})
        missing = [key for key, value in required.items() if not str(value).strip()]
        ok = len(missing) == 0
        msg = "ok" if ok else "missing_credentials"
        results.append(CredentialStatus(source=source, ok=ok, missing=missing, message=msg))
    return results


def _recency_decay(ts: datetime | None, window: RecencyWindow) -> float:
    if ts is None:
        return 0.0
    if ts < window.start:
        return 0.0
    age_days = max(0.0, (window.end - ts).total_seconds() / 86400.0)
    if window.days <= 0:
        return 0.0
    # Exponential decay with half-life at window midpoint
    half_life = max(1.0, window.days / 2.0)
    return float(math.exp(-math.log(2.0) * age_days / half_life))


def _engagement_score(engagement: float, comments: float, comment_weight: float) -> float:
    base = math.log1p(max(0.0, engagement))
    comment = math.log1p(max(0.0, comments)) * max(0.0, min(0.2, comment_weight))
    return float(base + comment)


def score_items(
    items: Iterable[RetrievalItem],
    *,
    query: str,
    window: RecencyWindow,
    authority_weights: Mapping[str, float] | None = None,
    comment_weight: float = 0.05,
) -> list[ScoredItem]:
    authority_weights = authority_weights or {}
    query_tokens = _tokenize(query)
    scored: list[ScoredItem] = []
    items_list = list(items)
    convergence = detect_convergence(items_list)

    for item in items_list:
        tokens = item.tokens()
        overlap = len(tokens.intersection(query_tokens)) / max(1.0, len(query_tokens))
        recency = _recency_decay(item.timestamp, window)
        authority = float(authority_weights.get(item.source, 1.0))
        engagement = _engagement_score(item.engagement, item.comments, comment_weight)
        convergence_score = float(convergence.get(item.url, 0.0))
        score = (overlap * 0.45) + (recency * 0.35) + (authority * 0.1) + (engagement * 0.1)
        score += convergence_score * 0.05
        scored.append(
            ScoredItem(
                item=item,
                score=float(score),
                recency_score=float(recency),
                overlap_score=float(overlap),
                authority_score=float(authority),
                engagement_score=float(engagement),
                convergence_score=float(convergence_score),
            )
        )

    return sorted(scored, key=lambda row: row.score, reverse=True)


def detect_convergence(items: Iterable[RetrievalItem]) -> dict[str, float]:
    items_list = list(items)
    tokens_list = [item.tokens() for item in items_list]
    convergence: dict[str, float] = {item.url: 0.0 for item in items_list}
    for idx, base_tokens in enumerate(tokens_list):
        if not base_tokens:
            continue
        match_count = 0
        for jdx, other_tokens in enumerate(tokens_list):
            if idx == jdx or not other_tokens:
                continue
            overlap = len(base_tokens.intersection(other_tokens)) / max(1.0, len(base_tokens))
            if overlap >= 0.6:
                match_count += 1
        convergence[items_list[idx].url] = float(match_count)
    return convergence


@dataclass(frozen=True)
class MarketRecord:
    market_id: str
    question: str
    volume_24h: float = 0.0
    volume_7d: float = 0.0
    volume_30d: float = 0.0
    liquidity: float = 0.0
    price_change_24h: float = 0.0
    yes_price: float = 0.0
    no_price: float = 0.0
    end_time: datetime | None = None
    tags: tuple[str, ...] = ()


def rank_polymarket_markets(
    markets: Iterable[MarketRecord],
    *,
    query: str,
    outcome: str | None = None,
) -> list[tuple[MarketRecord, float]]:
    query_tokens = _tokenize(query)
    ranked: list[tuple[MarketRecord, float]] = []
    for market in markets:
        q_tokens = _tokenize(market.question)
        relevance = len(query_tokens.intersection(q_tokens)) / max(1.0, len(query_tokens))
        volume = math.log1p(market.volume_24h + market.volume_7d + market.volume_30d)
        liquidity = math.log1p(max(0.0, market.liquidity))
        velocity = abs(market.price_change_24h)
        competitiveness = 1.0 - abs(market.yes_price - market.no_price)
        outcome_bias = 0.0
        if outcome:
            if outcome.lower() == "yes":
                outcome_bias = market.yes_price
            elif outcome.lower() == "no":
                outcome_bias = market.no_price
        score = (
            relevance * 0.4
            + volume * 0.2
            + liquidity * 0.15
            + velocity * 0.15
            + competitiveness * 0.1
            + outcome_bias * 0.05
        )
        ranked.append((market, float(score)))
    return sorted(ranked, key=lambda row: row[1], reverse=True)


class BriefingArchive:
    def __init__(self, root: str = "data/research/briefings") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def save(self, briefing: Briefing) -> Path:
        identity = f"{briefing.query}|{briefing.intent.query_type}|{briefing.window.start.isoformat()}"
        name = f"briefing_{_short_hash(identity)}.json"
        path = self.root / name
        payload = {
            "query": briefing.query,
            "intent": briefing.intent.__dict__,
            "window": {
                "start": briefing.window.start.isoformat(),
                "end": briefing.window.end.isoformat(),
                "days": briefing.window.days,
            },
            "sources": briefing.sources,
            "coverage": dict(briefing.coverage),
            "citations": list(briefing.citations),
            "ranked": [
                {
                    "source": row.item.source,
                    "title": row.item.title,
                    "url": row.item.url,
                    "score": row.score,
                }
                for row in briefing.ranked
            ],
            "notes": list(briefing.notes),
        }
        with self._lock:
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path


class WatchlistStore:
    def __init__(self, root: str = "data/research/watchlist") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.watchlist_path = self.root / "watchlist.jsonl"
        self.history_path = self.root / "history.jsonl"
        self._lock = threading.Lock()

    def add(self, topic: str, *, metadata: Mapping[str, Any] | None = None) -> None:
        record = {"topic": str(topic), "metadata": dict(metadata or {}), "added_at": _utc_now().isoformat()}
        with self._lock:
            self.watchlist_path.write_text(
                (self.watchlist_path.read_text(encoding="utf-8") if self.watchlist_path.exists() else "")
                + json.dumps(record)
                + "\n",
                encoding="utf-8",
            )

    def list_topics(self) -> list[Mapping[str, Any]]:
        if not self.watchlist_path.exists():
            return []
        rows = []
        for line in self.watchlist_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def record_run(self, topic: str, *, summary: Mapping[str, Any] | None = None) -> None:
        record = {
            "topic": str(topic),
            "summary": dict(summary or {}),
            "run_at": _utc_now().isoformat(),
        }
        with self._lock:
            self.history_path.write_text(
                (self.history_path.read_text(encoding="utf-8") if self.history_path.exists() else "")
                + json.dumps(record)
                + "\n",
                encoding="utf-8",
            )


class Last30DaysResearcher:
    def __init__(self, *, config: ResearchConfig | None = None) -> None:
        self.config = config or ResearchConfig()

    def retrieve_parallel(
        self,
        query: str,
        *,
        sources: Mapping[str, Callable[[str], Iterable[RetrievalItem]]],
        window: RecencyWindow,
    ) -> tuple[list[RetrievalItem], dict[str, int]]:
        enabled_sources = {
            name: func for name, func in sources.items() if self.config.sources_enabled.get(name, True)
        }
        coverage: dict[str, int] = {name: 0 for name in enabled_sources}
        items: list[RetrievalItem] = []
        with ThreadPoolExecutor(max_workers=int(self.config.max_workers)) as executor:
            future_map = {
                executor.submit(func, query): name for name, func in enabled_sources.items()
            }
            for future in as_completed(future_map, timeout=self.config.timeout_seconds):
                name = future_map[future]
                try:
                    for item in list(future.result()):
                        if window.contains(item.timestamp):
                            items.append(item)
                            coverage[name] += 1
                except Exception:
                    coverage[name] = 0
        return items, coverage

    def build_briefing(
        self,
        *,
        query: str,
        sources: Mapping[str, Callable[[str], Iterable[RetrievalItem]]],
        window: RecencyWindow | None = None,
    ) -> Briefing:
        intent = parse_intent(query)
        active_window = window or RecencyWindow.last_days(30)
        items, coverage = self.retrieve_parallel(query, sources=sources, window=active_window)
        scored = score_items(
            items,
            query=query,
            window=active_window,
            authority_weights=self.config.authority_weights,
            comment_weight=self.config.comment_weight,
        )
        citations = [row.item.url for row in scored]
        return Briefing(
            query=str(query),
            intent=intent,
            window=active_window,
            sources=list(coverage.keys()),
            coverage=coverage,
            citations=citations,
            ranked=scored,
            notes=[],
        )
