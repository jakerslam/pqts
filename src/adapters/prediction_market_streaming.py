"""Streaming, signer, and builder-mode contracts for prediction-market adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class BuilderScope:
    """Explicit builder/institutional scope configuration."""

    name: str
    can_trade: bool
    can_withdraw: bool
    can_manage_api_keys: bool


@dataclass(frozen=True)
class SignRequest:
    payload: str
    key_id: str


class SignerProtocol:
    """Protocol-like signer base class."""

    def sign(self, request: SignRequest) -> str:  # pragma: no cover - interface
        return f"protocol_sig::{request.key_id}::{len(request.payload)}"


class LocalSigner(SignerProtocol):
    def sign(self, request: SignRequest) -> str:
        return f"local_sig::{request.key_id}::{len(request.payload)}"


class RemoteSigner(SignerProtocol):
    def __init__(self, endpoint: str):
        self.endpoint = str(endpoint).strip()
        if not self.endpoint:
            raise ValueError("remote signer endpoint is required")

    def sign(self, request: SignRequest) -> str:
        return f"remote_sig::{self.endpoint}::{request.key_id}::{len(request.payload)}"


@dataclass
class StreamHealthTracker:
    """Track reconnect/backoff and disconnect safety behavior."""

    disconnect_cancel_enabled: bool = False
    reconnect_attempts: int = 0
    last_disconnect_reason: str = ""
    last_connected_at: str = ""
    last_disconnected_at: str = ""
    gap_recovery_events: int = 0
    protected_cancel_events: int = 0
    event_log: list[dict[str, Any]] = field(default_factory=list)

    def on_connected(self) -> None:
        self.last_connected_at = _utc_now_iso()
        self._log("connected", {})

    def on_disconnect(self, *, reason: str) -> dict[str, Any]:
        self.last_disconnect_reason = str(reason)
        self.last_disconnected_at = _utc_now_iso()
        self.reconnect_attempts += 1
        cancel_triggered = False
        if self.disconnect_cancel_enabled:
            self.protected_cancel_events += 1
            cancel_triggered = True
        self._log("disconnected", {"reason": reason, "cancel_triggered": cancel_triggered})
        return {
            "cancel_triggered": cancel_triggered,
            "reconnect_attempts": self.reconnect_attempts,
        }

    def on_gap_recovery(self, *, sequence_from: int, sequence_to: int) -> None:
        self.gap_recovery_events += 1
        self._log(
            "gap_recovery",
            {"sequence_from": int(sequence_from), "sequence_to": int(sequence_to)},
        )

    def status(self) -> dict[str, Any]:
        return {
            "reconnect_attempts": self.reconnect_attempts,
            "last_disconnect_reason": self.last_disconnect_reason,
            "gap_recovery_events": self.gap_recovery_events,
            "protected_cancel_events": self.protected_cancel_events,
        }

    def _log(self, event: str, payload: dict[str, Any]) -> None:
        self.event_log.append(
            {
                "event": event,
                "payload": dict(payload),
                "timestamp": _utc_now_iso(),
            }
        )
