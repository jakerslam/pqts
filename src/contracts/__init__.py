"""Canonical architecture contracts package."""

from contracts.api import (
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
from contracts.events import EventEnvelope
from contracts.module import ModuleDescriptor, ModuleHealth, RuntimeModule
from contracts.runtime import RuntimeContext

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
