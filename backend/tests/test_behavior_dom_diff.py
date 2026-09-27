"""Tests for behavior/dom_diff.py — Structural DOM Diff Engine (Sprint 4)."""

from __future__ import annotations

from app.behavior.dom_diff import compare_dom_snapshots
from app.behavior.severity import SeverityLevel


class TestDomDiff:
    def test_missing_route_triggers_critical(self) -> None:
        base = [
            {
                "route": "/checkout",
                "element_count": 50,
                "button_count": 2,
                "form_count": 1,
            }
        ]
        head = [{"route": "/", "element_count": 20, "button_count": 1, "form_count": 0}]

        diffs = compare_dom_snapshots(base, head)
        missing = [d for d in diffs if d.event_type == "ROUTE_MISSING"]
        assert len(missing) == 1
        assert missing[0].severity == SeverityLevel.CRITICAL
        assert missing[0].route == "/checkout"

    def test_added_route_triggers_info(self) -> None:
        base = [{"route": "/", "element_count": 10}]
        head = [
            {"route": "/", "element_count": 10},
            {"route": "/new", "element_count": 15},
        ]

        diffs = compare_dom_snapshots(base, head)
        added = [d for d in diffs if d.event_type == "ROUTE_ADDED"]
        assert len(added) == 1
        assert added[0].severity == SeverityLevel.INFO

    def test_button_removed_triggers_high(self) -> None:
        base = [
            {"route": "/login", "button_count": 3, "form_count": 1, "element_count": 20}
        ]
        head = [
            {"route": "/login", "button_count": 1, "form_count": 1, "element_count": 18}
        ]

        diffs = compare_dom_snapshots(base, head)
        btn_diffs = [d for d in diffs if d.event_type == "BUTTON_REMOVED"]
        assert len(btn_diffs) == 1
        assert btn_diffs[0].severity == SeverityLevel.HIGH
        assert "2 button(s) removed" in btn_diffs[0].title

    def test_all_forms_removed_triggers_critical(self) -> None:
        base = [
            {"route": "/login", "button_count": 2, "form_count": 1, "element_count": 20}
        ]
        head = [
            {"route": "/login", "button_count": 2, "form_count": 0, "element_count": 10}
        ]

        diffs = compare_dom_snapshots(base, head)
        form_diffs = [d for d in diffs if d.event_type == "ALL_FORMS_REMOVED"]
        assert len(form_diffs) == 1
        assert form_diffs[0].severity == SeverityLevel.CRITICAL

    def test_form_decreased_triggers_high(self) -> None:
        base = [
            {
                "route": "/settings",
                "button_count": 1,
                "form_count": 3,
                "element_count": 30,
            }
        ]
        head = [
            {
                "route": "/settings",
                "button_count": 1,
                "form_count": 1,
                "element_count": 25,
            }
        ]

        diffs = compare_dom_snapshots(base, head)
        form_diffs = [d for d in diffs if d.event_type == "FORM_REMOVED"]
        assert len(form_diffs) == 1
        assert form_diffs[0].severity == SeverityLevel.HIGH

    def test_significant_element_loss_triggers_high(self) -> None:
        base = [
            {
                "route": "/dashboard",
                "element_count": 100,
                "button_count": 5,
                "form_count": 1,
            }
        ]
        head = [
            {
                "route": "/dashboard",
                "element_count": 30,
                "button_count": 5,
                "form_count": 1,
            }
        ]

        diffs = compare_dom_snapshots(base, head)
        loss = [d for d in diffs if d.event_type == "SIGNIFICANT_ELEMENT_LOSS"]
        assert len(loss) == 1
        assert loss[0].severity == SeverityLevel.HIGH

    def test_title_changed_triggers_low(self) -> None:
        base = [
            {
                "route": "/",
                "title": "Old App",
                "button_count": 1,
                "form_count": 0,
                "element_count": 5,
            }
        ]
        head = [
            {
                "route": "/",
                "title": "New App",
                "button_count": 1,
                "form_count": 0,
                "element_count": 5,
            }
        ]

        diffs = compare_dom_snapshots(base, head)
        title_diffs = [d for d in diffs if d.event_type == "TITLE_CHANGED"]
        assert len(title_diffs) == 1
        assert title_diffs[0].severity == SeverityLevel.LOW
