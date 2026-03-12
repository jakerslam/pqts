"""Stage-aware fractional Kelly policy with explicit full-Kelly override audit."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from portfolio.kelly_core import kelly_fraction_from_probability

DEFAULT_STAGE_CAPS = {
    "backtest": 0.25,
    "paper": 0.10,
    "shadow": 0.05,
    "canary": 0.03,
    "live": 0.02,
}


@dataclass(frozen=True)
class StageKellyPolicy:
    base_fraction: float = 0.25
    hard_per_trade_cap: float = 0.05
    hard_per_event_cap: float = 0.05
    stage_caps: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_STAGE_CAPS))


@dataclass(frozen=True)
class StageKellyDecision:
    stage: str
    full_kelly_fraction: float
    requested_fraction: float
    approved_fraction: float
    blocked: bool
    reason_codes: tuple[str, ...]
    audit: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_stage_kelly(
    *,
    posterior_probability: float,
    payout_multiple: float,
    stage: str,
    policy: StageKellyPolicy | None = None,
    request_full_kelly: bool = False,
    override_actor: str = "",
    override_reason: str = "",
) -> StageKellyDecision:
    cfg = policy or StageKellyPolicy()
    stage_token = str(stage).strip().lower() or "paper"
    reason_codes: list[str] = []
    audit: dict[str, Any] = {
        "stage": stage_token,
        "request_full_kelly": bool(request_full_kelly),
    }

    full_kelly = max(
        0.0,
        float(
            kelly_fraction_from_probability(
                posterior_probability=float(posterior_probability),
                payout_multiple=float(payout_multiple),
            )
        ),
    )
    requested = full_kelly * float(cfg.base_fraction)
    if request_full_kelly:
        if not str(override_actor).strip() or not str(override_reason).strip():
            reason_codes.append("full_kelly_override_missing_audit")
        else:
            requested = full_kelly
            audit["override_actor"] = str(override_actor).strip()
            audit["override_reason"] = str(override_reason).strip()

    if full_kelly <= 0.0:
        reason_codes.append("non_positive_full_kelly")

    stage_cap = float(cfg.stage_caps.get(stage_token, cfg.stage_caps.get("paper", 0.10)))
    hard_trade_cap = float(cfg.hard_per_trade_cap)
    hard_event_cap = float(cfg.hard_per_event_cap)
    approved = min(float(requested), stage_cap, hard_trade_cap, hard_event_cap)
    if requested > approved + 1e-12:
        reason_codes.append("fraction_capped")

    blocked = bool(approved <= 0.0 or "full_kelly_override_missing_audit" in reason_codes)
    if blocked and approved <= 0.0:
        reason_codes.append("approved_fraction_zero")

    audit.update(
        {
            "base_fraction": float(cfg.base_fraction),
            "stage_cap": stage_cap,
            "hard_per_trade_cap": hard_trade_cap,
            "hard_per_event_cap": hard_event_cap,
        }
    )
    return StageKellyDecision(
        stage=stage_token,
        full_kelly_fraction=float(full_kelly),
        requested_fraction=float(requested),
        approved_fraction=max(0.0, float(approved)),
        blocked=blocked,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        audit=audit,
    )
