"""Tests for root_cause/graph.py (Sprint 5 - Task 36)."""

from __future__ import annotations

from app.root_cause.evidence import (
    CorrelatedEvidenceItem,
    EvidenceCategory,
    EvidenceSeverity,
)
from app.root_cause.graph import build_causal_graph


class TestCausalGraphBuilder:
    def test_empty_graph(self) -> None:
        graph = build_causal_graph([])
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
        assert graph.root_nodes == []

    def test_causal_edges_constructed(self) -> None:
        net_item = CorrelatedEvidenceItem(
            category=EvidenceCategory.NETWORK,
            severity=EvidenceSeverity.CRITICAL,
            route="/login",
            event_type="STATUS_CODE_5XX_INTRODUCED",
            title="HTTP 500 on /login",
            description="",
            divergence_order=1,
        )
        console_item = CorrelatedEvidenceItem(
            category=EvidenceCategory.CONSOLE,
            severity=EvidenceSeverity.HIGH,
            route="/login",
            event_type="RUNTIME_EXCEPTION",
            title="Uncaught error",
            description="",
            divergence_order=2,
        )
        dom_item = CorrelatedEvidenceItem(
            category=EvidenceCategory.DOM,
            severity=EvidenceSeverity.HIGH,
            route="/login",
            event_type="BUTTON_REMOVED",
            title="Submit button removed",
            description="",
            divergence_order=3,
        )

        graph = build_causal_graph([net_item, console_item, dom_item])
        assert len(graph.nodes) == 3
        assert len(graph.edges) >= 2

        # Network is highest weight and has no incoming edges
        assert len(graph.root_nodes) >= 1
        assert graph.root_nodes[0].evidence.category == EvidenceCategory.NETWORK

        g_dict = graph.to_dict()
        assert "nodes" in g_dict
        assert "edges" in g_dict
        assert "root_node_ids" in g_dict

    def test_different_routes_no_causal_edge(self) -> None:
        item_a = CorrelatedEvidenceItem(
            category=EvidenceCategory.NETWORK,
            severity=EvidenceSeverity.CRITICAL,
            route="/route-a",
            event_type="STATUS_CODE_5XX_INTRODUCED",
            title="500 on A",
            description="",
        )
        item_b = CorrelatedEvidenceItem(
            category=EvidenceCategory.DOM,
            severity=EvidenceSeverity.LOW,
            route="/route-b",
            event_type="BUTTON_ADDED",
            title="Button on B",
            description="",
        )

        graph = build_causal_graph([item_a, item_b])
        # Routes are strictly distinct and non-global, so no edge created
        assert len(graph.edges) == 0
