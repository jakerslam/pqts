"""Core REST endpoints for account, portfolio, execution, PnL, and risk resources."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from contracts.api import (
    AccountSummary,
    FillSnapshot,
    OrderSnapshot,
    PnLSnapshot,
    PositionSnapshot,
    RiskStateSnapshot,
)
from services.api.auth import APIIdentity, require_identity, require_operator
from services.api.state import APIRuntimeStore, get_store

router = APIRouter(prefix="/v1", tags=["core"])


def _invalid_payload(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid payload: {exc}",
    )


@router.get("/accounts/{account_id}")
def get_account_summary(
    account_id: str,
    _: Annotated[APIIdentity, Depends(require_identity)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    account = store.accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    return {"account": account.to_dict()}


@router.put("/accounts/{account_id}")
def upsert_account_summary(
    account_id: str,
    payload: dict[str, Any],
    _: Annotated[APIIdentity, Depends(require_operator)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    payload["account_id"] = account_id
    try:
        snapshot = AccountSummary.from_dict(payload)
    except Exception as exc:
        raise _invalid_payload(exc) from exc
    store.accounts[account_id] = snapshot
    return {"account": snapshot.to_dict()}


@router.get("/portfolio/positions")
def list_positions(
    account_id: Annotated[str, Query(min_length=1)],
    _: Annotated[APIIdentity, Depends(require_identity)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    rows = store.positions.get(account_id, [])
    return {"positions": [item.to_dict() for item in rows]}


@router.post("/portfolio/positions")
def append_position(
    payload: dict[str, Any],
    _: Annotated[APIIdentity, Depends(require_operator)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    try:
        snapshot = PositionSnapshot.from_dict(payload)
    except Exception as exc:
        raise _invalid_payload(exc) from exc
    store.positions.setdefault(snapshot.account_id, []).append(snapshot)
    return {"position": snapshot.to_dict()}


@router.get("/execution/orders")
def list_orders(
    account_id: Annotated[str, Query(min_length=1)],
    _: Annotated[APIIdentity, Depends(require_identity)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    rows = store.orders.get(account_id, [])
    return {"orders": [item.to_dict() for item in rows]}


@router.post("/execution/orders")
def append_order(
    payload: dict[str, Any],
    _: Annotated[APIIdentity, Depends(require_operator)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    try:
        snapshot = OrderSnapshot.from_dict(payload)
    except Exception as exc:
        raise _invalid_payload(exc) from exc
    store.orders.setdefault(snapshot.account_id, []).append(snapshot)
    return {"order": snapshot.to_dict()}


@router.get("/execution/fills")
def list_fills(
    account_id: Annotated[str, Query(min_length=1)],
    _: Annotated[APIIdentity, Depends(require_identity)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    rows = store.fills.get(account_id, [])
    return {"fills": [item.to_dict() for item in rows]}


@router.post("/execution/fills")
def append_fill(
    payload: dict[str, Any],
    _: Annotated[APIIdentity, Depends(require_operator)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    try:
        snapshot = FillSnapshot.from_dict(payload)
    except Exception as exc:
        raise _invalid_payload(exc) from exc
    store.fills.setdefault(snapshot.account_id, []).append(snapshot)
    return {"fill": snapshot.to_dict()}


@router.get("/pnl/snapshots")
def list_pnl_snapshots(
    account_id: Annotated[str, Query(min_length=1)],
    _: Annotated[APIIdentity, Depends(require_identity)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    rows = store.pnl_snapshots.get(account_id, [])
    return {"snapshots": [item.to_dict() for item in rows]}


@router.post("/pnl/snapshots")
def append_pnl_snapshot(
    payload: dict[str, Any],
    _: Annotated[APIIdentity, Depends(require_operator)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    try:
        snapshot = PnLSnapshot.from_dict(payload)
    except Exception as exc:
        raise _invalid_payload(exc) from exc
    store.pnl_snapshots.setdefault(snapshot.account_id, []).append(snapshot)
    return {"snapshot": snapshot.to_dict()}


@router.get("/risk/state/{account_id}")
def get_risk_state(
    account_id: str,
    _: Annotated[APIIdentity, Depends(require_identity)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    snapshot = store.risk_states.get(account_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk state not found.")
    return {"risk_state": snapshot.to_dict()}


@router.put("/risk/state/{account_id}")
def upsert_risk_state(
    account_id: str,
    payload: dict[str, Any],
    _: Annotated[APIIdentity, Depends(require_operator)],
    store: Annotated[APIRuntimeStore, Depends(get_store)],
) -> dict[str, Any]:
    payload["account_id"] = account_id
    try:
        snapshot = RiskStateSnapshot.from_dict(payload)
    except Exception as exc:
        raise _invalid_payload(exc) from exc
    store.risk_states[account_id] = snapshot
    return {"risk_state": snapshot.to_dict()}
