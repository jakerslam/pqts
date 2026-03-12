"""Compatibility shim for local contracts package.

The repository uses a src-layout package structure, but CI/tool execution can
import the third-party ``contracts`` package if ``src`` is not on ``sys.path``.
This shim makes the local ``src/contracts`` package importable whenever the repo
root is on ``sys.path``.
"""

from __future__ import annotations

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent.parent / "src" / "contracts")]

from .api import (
    AccountSummary,
    ErrorCategory,
    ErrorEnvelope,
    FillSnapshot,
    OrderSide,
    OrderSnapshot,
    OrderStatus,
    OrderType,
    PnLSnapshot,
    PositionDirection,
    PositionSnapshot,
    RiskLevel,
    RiskStateSnapshot,
    TimeInForce,
    ToolPayload,
    ToolStatus,
    batch_to_dict,
)
from .events import EventEnvelope
from .module import ModuleDescriptor, ModuleHealth, RuntimeModule
from .runtime import RuntimeContext

__all__ = [
    "AccountSummary",
    "ErrorCategory",
    "ErrorEnvelope",
    "EventEnvelope",
    "FillSnapshot",
    "ModuleDescriptor",
    "ModuleHealth",
    "OrderSide",
    "OrderSnapshot",
    "OrderStatus",
    "OrderType",
    "PnLSnapshot",
    "PositionDirection",
    "PositionSnapshot",
    "RiskLevel",
    "RiskStateSnapshot",
    "RuntimeContext",
    "RuntimeModule",
    "TimeInForce",
    "ToolPayload",
    "ToolStatus",
    "batch_to_dict",
]
