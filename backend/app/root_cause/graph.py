"""Causal Dependency Graph Builder (Sprint 5 - Task 36).

Constructs directed dependency graphs mapping upstream triggers to downstream
symptoms based on deterministic causal weights and timeline order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.root_cause.evidence import CorrelatedEvidenceItem, EvidenceCategory

_CAUSAL_WEIGHTS: dict[EvidenceCategory, int] = {
    EvidenceCategory.NETWORK: 100,
    EvidenceCategory.CONSOLE: 90,
    EvidenceCategory.DOM: 70,
    EvidenceCategory.STORAGE: 60,
    EvidenceCategory.PERFORMANCE: 50,
    EvidenceCategory.GIT: 40,
}


@dataclass
class CausalNode:
    """Node in the causal dependency graph representing an evidence event."""

    node_id: str
    evidence: CorrelatedEvidenceItem
    weight: int
    incoming_edges: list[str] = field(default_factory=list)
    outgoing_edges: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize node to dict."""
        return {
            "node_id": self.node_id,
            "evidence": self.evidence.to_dict(),
            "weight": self.weight,
            "incoming_edges": self.incoming_edges,
            "outgoing_edges": self.outgoing_edges,
        }


@dataclass
class CausalEdge:
    """Directed edge representing causal dependency (source caused target)."""

    source_id: str
    target_id: str
    relation: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize edge to dict."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
        }


@dataclass
class CausalGraph:
    """Directed acyclic graph of evidence events with causal ordering."""

    nodes: dict[str, CausalNode] = field(default_factory=dict)
    edges: list[CausalEdge] = field(default_factory=list)

    @property
    def root_nodes(self) -> list[CausalNode]:
        """Nodes that have no incoming edges, sorted by highest weight."""
        roots = [n for n in self.nodes.values() if not n.incoming_edges]
        return sorted(
            roots,
            key=lambda n: (-n.weight, n.evidence.divergence_order),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize graph to dictionary."""
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "root_node_ids": [n.node_id for n in self.root_nodes],
        }


def build_causal_graph(items: list[CorrelatedEvidenceItem]) -> CausalGraph:
    """Build directed causal graph from correlated evidence items.

    Args:
        items: List of normalized evidence items sorted by divergence order.

    Returns:
        CausalGraph with nodes and directed causal edges.
    """
    graph = CausalGraph()
    if not items:
        return graph

    # 1. Create nodes with weights
    for idx, item in enumerate(items, start=1):
        node_id = f"node_{idx}_{item.category.value}"
        weight = _CAUSAL_WEIGHTS.get(item.category, 30)
        graph.nodes[node_id] = CausalNode(
            node_id=node_id,
            evidence=item,
            weight=weight,
        )

    # 2. Connect causal edges within same route or global scope
    node_list = list(graph.nodes.values())
    for i, upstream in enumerate(node_list):
        for downstream in node_list[i + 1 :]:
            # Route correlation: same route or either is global/empty
            same_route = (
                upstream.evidence.route == downstream.evidence.route
                or upstream.evidence.route in ("global", "")
                or downstream.evidence.route in ("global", "")
            )

            # Causal relationship: upstream weight > downstream weight
            if same_route and upstream.weight > downstream.weight:
                edge = CausalEdge(
                    source_id=upstream.node_id,
                    target_id=downstream.node_id,
                    relation=f"{upstream.evidence.category.value}_triggers_"
                    f"{downstream.evidence.category.value}",
                )
                graph.edges.append(edge)
                upstream.outgoing_edges.append(downstream.node_id)
                downstream.incoming_edges.append(upstream.node_id)

    return graph
