"""Contracts for persisted first-success template-run artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class TemplateRunArtifact:
    generated_at: datetime = field(default_factory=_utc_now)
    mode: str = ""
    template: str = ""
    resolved_strategy: str = ""
    config_path: str = ""
    config_sha256: str = ""
    command: tuple[str, ...] = ()
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["generated_at"] = self.generated_at.isoformat()
        payload["command"] = list(self.command)
        payload.pop("extra", None)
        payload.update(dict(self.extra))
        return payload

