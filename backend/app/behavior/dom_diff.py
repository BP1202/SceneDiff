"""Task: Structural DOM Diff Engine.

Compares DOM snapshot structures between Base and Head executions.
Enforces rule: Structural comparison only, never pixel screenshot comparison.
"""

from __future__ import annotations

from typing import Any

from app.behavior.severity import BehaviorDivergence, SeverityLevel


def compare_dom_snapshots(
    base_snapshots: list[dict[str, Any]],
    head_snapshots: list[dict[str, Any]],
) -> list[BehaviorDivergence]:
    """Compare DOM snapshots between Base and Head across all visited routes.

    Args:
        base_snapshots: List of serialized DOM snapshot dicts from Base trace.
        head_snapshots: List of serialized DOM snapshot dicts from Head trace.

    Returns:
        List of detected BehaviorDivergence items.
    """
    divergences: list[BehaviorDivergence] = []

    base_map = {s.get("route", "/"): s for s in base_snapshots}
    head_map = {s.get("route", "/"): s for s in head_snapshots}

    # 1. Missing routes in Head
    for route, base_s in base_map.items():
        if route not in head_map:
            divergences.append(
                BehaviorDivergence(
                    category="dom",
                    severity=SeverityLevel.CRITICAL,
                    route=route,
                    event_type="ROUTE_MISSING",
                    title=f"Route '{route}' missing in Head execution",
                    description=(
                        f"Route '{route}' was rendered in Base commit "
                        f"({base_s.get('element_count', 0)} elements) "
                        "but was missing in Head."
                    ),
                    base_value={
                        "route": route,
                        "element_count": base_s.get("element_count", 0),
                    },
                    head_value=None,
                    evidence={"missing_route": route},
                )
            )

    # 2. Newly introduced routes
    for route, head_s in head_map.items():
        if route not in base_map:
            divergences.append(
                BehaviorDivergence(
                    category="dom",
                    severity=SeverityLevel.INFO,
                    route=route,
                    event_type="ROUTE_ADDED",
                    title=f"Route '{route}' added in Head execution",
                    description=f"New route '{route}' visited in Head execution.",
                    base_value=None,
                    head_value={
                        "route": route,
                        "element_count": head_s.get("element_count", 0),
                    },
                    evidence={"new_route": route},
                )
            )

    # 3. Route-by-route structural comparisons
    common_routes = set(base_map.keys()) & set(head_map.keys())
    for route in sorted(common_routes):
        b = base_map[route]
        h = head_map[route]

        # Button comparison
        base_buttons = int(b.get("button_count", 0))
        head_buttons = int(h.get("button_count", 0))
        if head_buttons < base_buttons:
            removed = base_buttons - head_buttons
            divergences.append(
                BehaviorDivergence(
                    category="dom",
                    severity=SeverityLevel.HIGH,
                    route=route,
                    event_type="BUTTON_REMOVED",
                    title=f"{removed} button(s) removed on {route}",
                    description=(
                        f"Button count decreased from {base_buttons} to {head_buttons} "
                        f"on route '{route}'."
                    ),
                    base_value={"button_count": base_buttons},
                    head_value={"button_count": head_buttons},
                    evidence={"difference": -removed},
                )
            )
        elif head_buttons > base_buttons:
            added = head_buttons - base_buttons
            divergences.append(
                BehaviorDivergence(
                    category="dom",
                    severity=SeverityLevel.LOW,
                    route=route,
                    event_type="BUTTON_ADDED",
                    title=f"{added} button(s) added on {route}",
                    description=(
                        f"Button count grew from {base_buttons} to {head_buttons}."
                    ),
                    base_value={"button_count": base_buttons},
                    head_value={"button_count": head_buttons},
                )
            )

        # Form comparison
        base_forms = int(b.get("form_count", 0))
        head_forms = int(h.get("form_count", 0))
        if base_forms > 0 and head_forms == 0:
            divergences.append(
                BehaviorDivergence(
                    category="dom",
                    severity=SeverityLevel.CRITICAL,
                    route=route,
                    event_type="ALL_FORMS_REMOVED",
                    title=f"All interactive forms disappeared on {route}",
                    description=(
                        f"Route '{route}' had {base_forms} form(s) in Base, "
                        "but 0 forms in Head. Critical user workflow failure."
                    ),
                    base_value={"form_count": base_forms},
                    head_value={"form_count": 0},
                )
            )
        elif head_forms < base_forms:
            removed = base_forms - head_forms
            divergences.append(
                BehaviorDivergence(
                    category="dom",
                    severity=SeverityLevel.HIGH,
                    route=route,
                    event_type="FORM_REMOVED",
                    title=f"{removed} form(s) removed on {route}",
                    description=(
                        f"Form count dropped from {base_forms} to {head_forms}."
                    ),
                    base_value={"form_count": base_forms},
                    head_value={"form_count": head_forms},
                )
            )

        # Inputs comparison
        base_inputs = int(b.get("input_count", 0))
        head_inputs = int(h.get("input_count", 0))
        if head_inputs < base_inputs:
            inputs_diff = base_inputs - head_inputs
            divergences.append(
                BehaviorDivergence(
                    category="dom",
                    severity=SeverityLevel.HIGH,
                    route=route,
                    event_type="INPUT_REMOVED",
                    title=f"{inputs_diff} input field(s) removed on {route}",
                    description=(
                        f"Input count dropped from {base_inputs} to {head_inputs}."
                    ),
                    base_value={"input_count": base_inputs},
                    head_value={"input_count": head_inputs},
                )
            )

        # Significant total element drop
        base_elements = int(b.get("element_count", 0))
        head_elements = int(h.get("element_count", 0))
        if base_elements >= 10 and head_elements < base_elements * 0.5:
            divergences.append(
                BehaviorDivergence(
                    category="dom",
                    severity=SeverityLevel.HIGH,
                    route=route,
                    event_type="SIGNIFICANT_ELEMENT_LOSS",
                    title=f"Significant element reduction (>50%) on {route}",
                    description=(
                        f"DOM element count dropped by "
                        f"{round((1 - head_elements / base_elements) * 100, 1)}% "
                        f"({base_elements} -> {head_elements})."
                    ),
                    base_value={"element_count": base_elements},
                    head_value={"element_count": head_elements},
                )
            )

        # Title change
        base_title = b.get("title", "")
        head_title = h.get("title", "")
        if base_title and head_title and base_title != head_title:
            divergences.append(
                BehaviorDivergence(
                    category="dom",
                    severity=SeverityLevel.LOW,
                    route=route,
                    event_type="TITLE_CHANGED",
                    title=f"Page title changed on {route}",
                    description=f"Title changed from '{base_title}' to '{head_title}'.",
                    base_value={"title": base_title},
                    head_value={"title": head_title},
                )
            )

    return divergences
