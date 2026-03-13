"""Trace-context helpers shared across runtime, API, and UI artifacts."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


def new_trace_id(*parts: Any) -> str:
    """Create a deterministic-ish trace token from current UTC + caller parts."""
    base = "|".join(str(part) for part in parts if part is not None)
    stamp = datetime.now(timezone.utc).isoformat()
    payload = f"{stamp}|{base}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"trc_{digest}"


def ensure_trace_fields(payload: dict[str, Any], *, trace_id: str | None = None) -> str:
    """Attach trace metadata to mutable payload dict and return trace id."""
    resolved = str(trace_id or payload.get("trace_id") or new_trace_id(payload.get("order_id", "")))
    payload["trace_id"] = resolved
    payload.setdefault("trace_timestamp", datetime.now(timezone.utc).isoformat())
    return resolved
