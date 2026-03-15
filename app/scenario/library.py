from __future__ import annotations

from typing import Any

from app.scenario.launch_builder import default_launch_capabilities
from app.scenario.official_runner import list_official_openscenario_catalog
from app.scenario.platform_catalog import list_platform_scenario_catalog
from app.scenario.template_registry import (
    build_template_parameter_schema,
    get_template_category,
)


def list_scenario_catalog() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    source_items = [
        *list_platform_scenario_catalog(),
        *list_official_openscenario_catalog(),
    ]
    for item in source_items:
        enriched = dict(item)
        existing_capabilities = enriched.get("launch_capabilities")
        if not isinstance(existing_capabilities, dict):
            existing_capabilities = default_launch_capabilities(map_editable=False)
        enriched["launch_capabilities"] = existing_capabilities
        enriched["category"] = get_template_category(enriched["scenario_id"])
        enriched["parameter_schema"] = build_template_parameter_schema(
            enriched["scenario_id"],
            enriched.get("parameter_declarations", []),
        )
        items.append(enriched)
    return items


def get_scenario_catalog_item(scenario_id: str) -> dict[str, Any] | None:
    normalized = scenario_id.strip()
    for item in list_scenario_catalog():
        if item["scenario_id"] == normalized:
            return item
    return None
