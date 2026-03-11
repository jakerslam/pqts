"""RCG requirement primitives for short-cycle prediction-market execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable, Iterable, Mapping, Sequence


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MarketDiscoveryInput:
    market_id: str
    asset_candidates: tuple[str, ...]
    interval_candidates: tuple[str, ...]
    yes_token: str
    no_token: str


@dataclass(frozen=True)
class ResolvedMarket:
    market_id: str
    asset: str
    interval: str
    yes_token: str
    no_token: str
    resolution_reason: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def discover_markets(
    *,
    rows: Iterable[MarketDiscoveryInput],
    allowed_assets: Sequence[str],
    allowed_intervals: Sequence[str],
) -> tuple[list[ResolvedMarket], list[str]]:
    """Resolve deterministic (asset, interval) buckets and fail closed on ambiguity."""
    allowed_assets_set = {token.upper() for token in allowed_assets}
    allowed_intervals_set = {token.strip() for token in allowed_intervals}
    resolved: list[ResolvedMarket] = []
    errors: list[str] = []
    for row in rows:
        valid_assets = sorted(
            {
                token.upper()
                for token in row.asset_candidates
                if token.upper() in allowed_assets_set
            }
        )
        valid_intervals = sorted(
            {
                token.strip()
                for token in row.interval_candidates
                if token.strip() in allowed_intervals_set
            }
        )
        if len(valid_assets) != 1:
            errors.append(f"{row.market_id}:asset_resolution_failed")
            continue
        if len(valid_intervals) != 1:
            errors.append(f"{row.market_id}:interval_resolution_failed")
            continue
        yes_token = str(row.yes_token).strip()
        no_token = str(row.no_token).strip()
        if not yes_token or not no_token:
            errors.append(f"{row.market_id}:token_resolution_failed")
            continue
        resolved.append(
            ResolvedMarket(
                market_id=row.market_id,
                asset=valid_assets[0],
                interval=valid_intervals[0],
                yes_token=yes_token,
                no_token=no_token,
                resolution_reason="resolved_unique_bucket",
            )
        )
    return resolved, errors


@dataclass(frozen=True)
class DryRunParityArtifact:
    market_id: str
    would_submit: bool
    would_fill: bool
    why_blocked: str
    expected_edge_bps: float
    liquidity_score: float
    risk_passed: bool
    generated_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_dry_run_parity_artifact(
    *,
    market_id: str,
    expected_edge_bps: float,
    liquidity_score: float,
    risk_passed: bool,
    min_liquidity_score: float = 0.65,
) -> DryRunParityArtifact:
    edge = float(expected_edge_bps)
    liquidity = max(min(float(liquidity_score), 1.0), 0.0)
    risk_ok = bool(risk_passed)
    if not risk_ok:
        return DryRunParityArtifact(
            market_id=market_id,
            would_submit=False,
            would_fill=False,
            why_blocked="risk_gate_failed",
            expected_edge_bps=edge,
            liquidity_score=liquidity,
            risk_passed=risk_ok,
        )
    if edge <= 0.0:
        return DryRunParityArtifact(
            market_id=market_id,
            would_submit=False,
            would_fill=False,
            why_blocked="expected_edge_non_positive",
            expected_edge_bps=edge,
            liquidity_score=liquidity,
            risk_passed=risk_ok,
        )
    if liquidity < float(min_liquidity_score):
        return DryRunParityArtifact(
            market_id=market_id,
            would_submit=False,
            would_fill=False,
            why_blocked="liquidity_below_threshold",
            expected_edge_bps=edge,
            liquidity_score=liquidity,
            risk_passed=risk_ok,
        )
    would_fill = liquidity >= float(min_liquidity_score + 0.15)
    return DryRunParityArtifact(
        market_id=market_id,
        would_submit=True,
        would_fill=bool(would_fill),
        why_blocked="",
        expected_edge_bps=edge,
        liquidity_score=liquidity,
        risk_passed=risk_ok,
    )


@dataclass(frozen=True)
class BundleEdgeDiagnostics:
    gross_edge_bps: float
    fee_bps: float
    slippage_bps: float
    residual_risk_bps: float
    net_edge_bps: float
    min_required_bps: float
    passed: bool

    def to_dict(self) -> dict[str, float | bool]:
        return asdict(self)


def evaluate_complementary_bundle_edge(
    *,
    ask_yes: float,
    ask_no: float,
    maker_fee_bps: float,
    taker_fee_bps: float,
    use_maker: bool,
    slippage_bps: float,
    residual_risk_bps: float,
    min_required_bps: float,
) -> BundleEdgeDiagnostics:
    gross_edge_bps = (1.0 - (float(ask_yes) + float(ask_no))) * 10000.0
    fee_bps = max(float(maker_fee_bps if use_maker else taker_fee_bps), 0.0)
    slip = max(float(slippage_bps), 0.0)
    residual = max(float(residual_risk_bps), 0.0)
    min_required = max(float(min_required_bps), 0.0)
    net_edge_bps = float(gross_edge_bps - fee_bps - slip - residual)
    return BundleEdgeDiagnostics(
        gross_edge_bps=float(gross_edge_bps),
        fee_bps=float(fee_bps),
        slippage_bps=float(slip),
        residual_risk_bps=float(residual),
        net_edge_bps=float(net_edge_bps),
        min_required_bps=float(min_required),
        passed=bool(net_edge_bps >= min_required),
    )


@dataclass(frozen=True)
class RepricingDecision:
    action: str
    new_limit_price: float
    quote_lifetime_ms: int
    replace_count: int
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def decide_dynamic_repricing(
    *,
    side: str,
    current_limit_price: float,
    best_bid: float,
    best_ask: float,
    now_ms: int,
    last_quote_ms: int,
    max_quote_lifetime_ms: int,
    min_tick: float,
    replace_count: int,
    max_replace_count: int,
) -> RepricingDecision:
    side_token = str(side).strip().lower()
    current_limit = max(float(current_limit_price), 0.0)
    tick = max(float(min_tick), 1e-9)
    lifetime = max(int(now_ms) - int(last_quote_ms), 0)
    replacements = max(int(replace_count), 0)
    max_replaces = max(int(max_replace_count), 0)
    if replacements >= max_replaces:
        return RepricingDecision(
            action="cancel",
            new_limit_price=current_limit,
            quote_lifetime_ms=lifetime,
            replace_count=replacements,
            reason="replace_cap_reached",
        )
    target = float(best_bid if side_token == "buy" else best_ask)
    if target <= 0.0:
        return RepricingDecision(
            action="hold",
            new_limit_price=current_limit,
            quote_lifetime_ms=lifetime,
            replace_count=replacements,
            reason="invalid_book_reference",
        )
    moved = abs(target - current_limit) >= tick
    stale = lifetime >= max(int(max_quote_lifetime_ms), 0)
    if moved or stale:
        return RepricingDecision(
            action="reprice",
            new_limit_price=target,
            quote_lifetime_ms=lifetime,
            replace_count=replacements + 1,
            reason="stale_quote" if stale else "book_moved",
        )
    return RepricingDecision(
        action="hold",
        new_limit_price=current_limit,
        quote_lifetime_ms=lifetime,
        replace_count=replacements,
        reason="within_tolerance",
    )


@dataclass(frozen=True)
class MakerFirstDecision:
    order_style: str
    fallback_used: bool
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def choose_maker_first_style(
    *,
    maker_first_enabled: bool,
    taker_fallback_enabled: bool,
    urgency_score: float,
    elapsed_wait_ms: int,
    max_maker_wait_ms: int,
) -> MakerFirstDecision:
    urgency = max(min(float(urgency_score), 1.0), 0.0)
    elapsed = max(int(elapsed_wait_ms), 0)
    maker_window = max(int(max_maker_wait_ms), 0)
    if maker_first_enabled and urgency < 0.85 and elapsed <= maker_window:
        return MakerFirstDecision(
            order_style="post_only",
            fallback_used=False,
            rationale="maker_first_window_active",
        )
    if taker_fallback_enabled:
        return MakerFirstDecision(
            order_style="ioc",
            fallback_used=True,
            rationale="urgency_or_timeout_fallback",
        )
    return MakerFirstDecision(
        order_style="post_only",
        fallback_used=False,
        rationale="fallback_disabled",
    )


@dataclass(frozen=True)
class ReferencePriceSample:
    source: str
    price: float
    timestamp_ms: int
    priority: int = 100


@dataclass(frozen=True)
class ReferencePriceContext:
    selected_source: str
    selected_price: float
    divergence_bps: float
    stale_sources: tuple[str, ...]
    passed: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_reference_price_context(
    *,
    samples: Iterable[ReferencePriceSample],
    now_ms: int,
    max_age_ms: int,
    max_divergence_bps: float,
) -> ReferencePriceContext:
    fresh: list[ReferencePriceSample] = []
    stale_sources: list[str] = []
    for row in samples:
        if max(int(now_ms) - int(row.timestamp_ms), 0) > max(int(max_age_ms), 0):
            stale_sources.append(str(row.source))
            continue
        if float(row.price) <= 0:
            stale_sources.append(str(row.source))
            continue
        fresh.append(row)

    if not fresh:
        return ReferencePriceContext(
            selected_source="",
            selected_price=0.0,
            divergence_bps=0.0,
            stale_sources=tuple(sorted(stale_sources)),
            passed=False,
            reason="no_fresh_sources",
        )
    fresh.sort(key=lambda row: (int(row.priority), str(row.source)))
    selected = fresh[0]
    divergence = 0.0
    for row in fresh[1:]:
        divergence = max(
            divergence,
            abs(float(row.price) - float(selected.price)) / max(float(selected.price), 1e-9) * 10000.0,
        )
    passed = divergence <= max(float(max_divergence_bps), 0.0)
    return ReferencePriceContext(
        selected_source=str(selected.source),
        selected_price=float(selected.price),
        divergence_bps=float(divergence),
        stale_sources=tuple(sorted(stale_sources)),
        passed=bool(passed),
        reason="ok" if passed else "divergence_exceeded",
    )


@dataclass(frozen=True)
class ValidationStep:
    step: str
    passed: bool
    remediation: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_beginner_validation_ladder(checks: Mapping[str, bool]) -> dict[str, object]:
    ordered = [
        ("market_discovery", "Run `pqts quickstart` and verify market resolution."),
        ("dry_run_parity", "Run dry-run parity and inspect `would_submit` / `why_blocked`."),
        ("edge_gate", "Adjust edge threshold, fee model, or slippage assumptions."),
        ("risk_guardrails", "Apply conservative risk profile and retry paper mode."),
        ("settlement_ready", "Verify settlement worker configuration and claim permissions."),
    ]
    steps: list[ValidationStep] = []
    first_failed = ""
    for name, remediation in ordered:
        passed = bool(checks.get(name, False))
        steps.append(ValidationStep(step=name, passed=passed, remediation="" if passed else remediation))
        if not passed and not first_failed:
            first_failed = name
    return {
        "passed": first_failed == "",
        "first_failed_step": first_failed,
        "steps": [row.to_dict() for row in steps],
        "next_action": "" if first_failed == "" else next(
            row.remediation for row in steps if row.step == first_failed
        ),
    }


@dataclass(frozen=True)
class ClaimablePosition:
    position_id: str
    market_id: str
    claimable: bool
    notional_usd: float


@dataclass(frozen=True)
class SettlementAttempt:
    position_id: str
    market_id: str
    attempt: int
    ok: bool
    reason: str
    redeemed_notional_usd: float
    timestamp: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class SettlementWorker:
    """Idempotent resolution-to-redeem worker with bounded retries."""

    def __init__(self, *, max_retries: int = 3, backoff_seconds: float = 2.0) -> None:
        self.max_retries = max(int(max_retries), 1)
        self.backoff_seconds = max(float(backoff_seconds), 0.0)
        self._redeemed: set[str] = set()

    def process_claimable_positions(
        self,
        *,
        positions: Iterable[ClaimablePosition],
        redeem_fn: Callable[[ClaimablePosition], tuple[bool, str]],
    ) -> list[SettlementAttempt]:
        attempts: list[SettlementAttempt] = []
        for position in positions:
            if not bool(position.claimable):
                continue
            if position.position_id in self._redeemed:
                attempts.append(
                    SettlementAttempt(
                        position_id=position.position_id,
                        market_id=position.market_id,
                        attempt=0,
                        ok=True,
                        reason="already_redeemed",
                        redeemed_notional_usd=0.0,
                    )
                )
                continue
            for attempt in range(1, self.max_retries + 1):
                ok, reason = redeem_fn(position)
                attempts.append(
                    SettlementAttempt(
                        position_id=position.position_id,
                        market_id=position.market_id,
                        attempt=attempt,
                        ok=bool(ok),
                        reason=str(reason),
                        redeemed_notional_usd=float(position.notional_usd if ok else 0.0),
                    )
                )
                if ok:
                    self._redeemed.add(position.position_id)
                    break
        return attempts

