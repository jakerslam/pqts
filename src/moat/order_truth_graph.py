"""Per-order truth graph for signal-to-fill lineage and auditing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class TruthNode:
    node_id: str
    order_id: str
    node_type: str
    strategy: str
    venue: str
    run_id: str
    incident_id: str | None
    payload: dict[str, Any]
    timestamp: str


@dataclass
class OrderTruthGraph:
    nodes: list[TruthNode] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)

    def add_node(
        self,
        *,
        node_id: str,
        order_id: str,
        node_type: str,
        strategy: str,
        venue: str,
        run_id: str,
        incident_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> TruthNode:
        node = TruthNode(
            node_id=str(node_id),
            order_id=str(order_id),
            node_type=str(node_type),
            strategy=str(strategy),
            venue=str(venue),
            run_id=str(run_id),
            incident_id=str(incident_id) if incident_id else None,
            payload=dict(payload or {}),
            timestamp=_utc_now_iso(),
        )
        self.nodes.append(node)
        return node

    def add_edge(self, source_node_id: str, target_node_id: str) -> None:
        self.edges.append((str(source_node_id), str(target_node_id)))

    def query(
        self,
        *,
        strategy: str | None = None,
        venue: str | None = None,
        run_id: str | None = None,
        incident_id: str | None = None,
    ) -> list[TruthNode]:
        rows = self.nodes
        if strategy is not None:
            rows = [row for row in rows if row.strategy == strategy]
        if venue is not None:
            rows = [row for row in rows if row.venue == venue]
        if run_id is not None:
            rows = [row for row in rows if row.run_id == run_id]
        if incident_id is not None:
            rows = [row for row in rows if row.incident_id == incident_id]
        return rows
