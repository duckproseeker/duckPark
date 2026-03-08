from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_sensor_profiles(root: Path) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []

    if not root.exists():
        return profiles

    for path in sorted(root.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        if not isinstance(payload, dict):
            raise ValueError(f"Invalid sensor profile YAML: {path}")

        profile_name = str(payload.get("profile_name", path.stem)).strip()
        display_name = str(payload.get("display_name", profile_name)).strip()
        description = str(payload.get("description", "")).strip()
        sensors = payload.get("sensors", [])
        metadata = payload.get("metadata", {})

        if not isinstance(sensors, list):
            raise ValueError(f"Sensor profile sensors must be a list: {path}")
        if not isinstance(metadata, dict):
            raise ValueError(f"Sensor profile metadata must be a mapping: {path}")

        profiles.append(
            {
                "profile_name": profile_name,
                "display_name": display_name,
                "description": description,
                "sensors": sensors,
                "raw_yaml": path.read_text(encoding="utf-8"),
                "source_path": str(path),
                "metadata": metadata,
            }
        )

    return profiles
