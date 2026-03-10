"""Tests for API Server-Sent Event stream channels."""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.config import APISettings
from services.api.state import StreamHub


def _settings() -> APISettings:
    return APISettings(
        service_name="PQTS API Test",
        service_version="9.9.9",
        environment="test",
        auth_tokens="admin-token:admin,operator-token:operator,viewer-token:viewer",
    )


def _viewer() -> dict[str, str]:
    return {"Authorization": "Bearer viewer-token"}


def test_sse_route_is_registered() -> None:
    app = create_app(_settings())
    paths = {route.path for route in app.routes}
    assert "/v1/stream/sse/{channel}" in paths


def test_sse_stream_rejects_invalid_channel() -> None:
    client = TestClient(create_app(_settings()))
    response = client.get("/v1/stream/sse/invalid", headers=_viewer())
    assert response.status_code == 404


def test_sse_stream_requires_authentication() -> None:
    client = TestClient(create_app(_settings()))
    response = client.get("/v1/stream/sse/orders")
    assert response.status_code == 401


def test_stream_hub_sse_subscribers_receive_broadcasts() -> None:
    async def _run() -> dict:
        hub = StreamHub()
        queue = await hub.subscribe_sse("orders")
        await hub.broadcast(
            "orders",
            "order_appended",
            {"account_id": "paper-main", "order": {"order_id": "ord-sse-2"}},
            trace_id="trace-test",
            run_id="run-test",
        )
        message = await asyncio.wait_for(queue.get(), timeout=0.5)
        await hub.unsubscribe_sse("orders", queue)
        return message

    message = asyncio.run(_run())
    assert message["event"] == "order_appended"
    assert message["payload"]["order"]["order_id"] == "ord-sse-2"
