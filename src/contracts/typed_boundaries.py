"""Typed boundary models for runtime config, strategy manifests, and API payloads."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrategyManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    market: str = Field(min_length=1)
    risk_profile: str = Field(min_length=1)
    notional_usd: float = Field(gt=0.0)


class RuntimeConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: str = Field(min_length=1)
    ui_primary: str = Field(min_length=1)
    control_plane_base_url: str = Field(min_length=1)
    cycle_slo_ms: int = Field(gt=0)
    refresh_slo_ms: int = Field(gt=0)


class APIPayloadModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    strategy: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
