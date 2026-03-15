from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


def _read_text_with_fallback(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(
        "utf-8",
        raw,
        0,
        1,
        f"Unable to decode sensor profile {path}",
    )


def load_sensor_profiles(root: Path) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []

    if not root.exists():
        return profiles

    for path in sorted(root.glob("*.yaml")):
        if path.name.startswith("._"):
            continue
        raw_text = _read_text_with_fallback(path)
        payload = yaml.safe_load(raw_text) or {}

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
                "raw_yaml": raw_text,
                "source_path": str(path),
                "metadata": metadata,
            }
        )

    return profiles


def get_sensor_profile(root: Path, profile_name: str) -> dict[str, Any] | None:
    normalized = str(profile_name).strip()
    if not normalized:
        return None

    for item in load_sensor_profiles(root):
        if str(item.get("profile_name") or "").strip() == normalized:
            return copy.deepcopy(item)
    return None


def build_sensor_config_from_profile(
    root: Path, profile_name: str
) -> dict[str, Any] | None:
    profile = get_sensor_profile(root, profile_name)
    if profile is None:
        return None

    return {
        "enabled": True,
        "profile_name": profile["profile_name"],
        "config_yaml_path": profile["source_path"],
        "sensors": copy.deepcopy(profile["sensors"]),
    }
