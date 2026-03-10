"""Realtime Server-Sent Event (SSE) channels for execution and risk streams."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from services.api.auth import APIIdentity, require_identity
from services.api.correlation import read_request_correlation
from services.api.state import APIRuntimeStore, StreamHub, get_store, get_stream_hub

router = APIRouter(prefix="/v1/stream", tags=["stream"])

_VALID_CHANNELS = {"orders", "fills", "positions", "pnl", "risk"}
_IDENTITY_DEP = Depends(require_identity)
_STORE_DEP = Depends(get_store)
_HUB_DEP = Depends(get_stream_hub)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sse_frame(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"


def _snapshot_payload(store: APIRuntimeStore, *, channel: str, account_id: str) -> dict[str, Any]:
    if channel == "orders":
        return {"orders": [row.to_dict() for row in store.orders.get(account_id, [])]}
    if channel == "fills":
        return {"fills": [row.to_dict() for row in store.fills.get(account_id, [])]}
    if channel == "positions":
        return {"positions": [row.to_dict() for row in store.positions.get(account_id, [])]}
    if channel == "pnl":
        return {"snapshots": [row.to_dict() for row in store.pnl_snapshots.get(account_id, [])]}
    if channel == "risk":
        risk = store.risk_states.get(account_id)
        return {
            "risk_state": risk.to_dict() if risk is not None else None,
            "incidents": list(store.risk_incidents.get(account_id, [])),
        }
    return {}


def _account_matches(account_id: str, payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return True
    direct = str(payload.get("account_id", "")).strip()
    if direct:
        return direct == account_id
    for key in ("order", "fill", "position", "snapshot", "risk_state", "incident"):
        candidate = payload.get(key)
        if not isinstance(candidate, dict):
            continue
        nested = str(candidate.get("account_id", "")).strip()
        if nested:
            return nested == account_id
    return True


@router.get("/sse/{channel}")
async def stream_channel_sse(
    channel: str,
    request: Request,
    identity: APIIdentity = _IDENTITY_DEP,
    store: APIRuntimeStore = _STORE_DEP,
    hub: StreamHub = _HUB_DEP,
    account_id: str = Query(default="paper-main", min_length=1),
    heartbeat_seconds: float = Query(default=15.0, ge=1.0, le=120.0),
) -> StreamingResponse:
    _ = identity
    normalized_channel = str(channel).strip().lower()
    if normalized_channel not in _VALID_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown stream channel: {channel}",
        )

    trace_id, run_id = read_request_correlation(request)
    queue = await hub.subscribe_sse(normalized_channel)
    snapshot_message = {
        "channel": normalized_channel,
        "event": "snapshot",
        "payload": _snapshot_payload(store, channel=normalized_channel, account_id=account_id),
        "timestamp": _utc_now_iso(),
        "trace_id": trace_id,
        "run_id": run_id,
    }

    async def _iter_events() -> AsyncIterator[str]:
        try:
            yield _sse_frame("snapshot", snapshot_message)
            timeout = float(heartbeat_seconds)
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=timeout)
                except asyncio.TimeoutError:
                    heartbeat = {
                        "channel": normalized_channel,
                        "event": "heartbeat",
                        "payload": {"account_id": account_id},
                        "timestamp": _utc_now_iso(),
                        "trace_id": trace_id,
                        "run_id": run_id,
                    }
                    yield _sse_frame("heartbeat", heartbeat)
                    continue
                if not isinstance(message, dict):
                    continue
                payload = message.get("payload", {})
                if isinstance(payload, dict) and not _account_matches(account_id, payload):
                    continue
                event_name = str(message.get("event", "update")).strip() or "update"
                yield _sse_frame(event_name, message)
        finally:
            await hub.unsubscribe_sse(normalized_channel, queue)

    return StreamingResponse(
        _iter_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
