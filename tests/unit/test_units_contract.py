"""Unit-level contracts for typed execution units and side-aware depth."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from execution.realistic_costs import OrderBook, Side


def test_order_book_depth_is_side_aware_and_notional_based():
    book = OrderBook.from_snapshots(
        bid_snapshots=[(99.0, 10.0), (98.0, 20.0)],
        ask_snapshots=[(101.0, 8.0), (102.0, 5.0)],
    )

    buy_depth = float(book.depth_notional_up_to_pct(0.02, Side.BUY))
    sell_depth = float(book.depth_notional_up_to_pct(0.02, Side.SELL))

    assert buy_depth > 0.0
    assert sell_depth > 0.0
    assert buy_depth != sell_depth
