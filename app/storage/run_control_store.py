from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.utils.file_utils import ensure_dir
from app.utils.time_utils import now_utc


class RunControlStore:
    def __init__(self, controls_root: Path) -> None:
        self._controls_root = ensure_dir(controls_root)

    def _path(self, run_id: str) -> Path:
        return self._controls_root / f"{run_id}.json"

    def get(self, run_id: str) -> dict[str, Any]:
        path = self._path(run_id)
        if not path.exists():
            return {}

        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        path = self._path(run_id)
        payload_to_write = {**payload, "updated_at_utc": now_utc().isoformat()}
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload_to_write, handle, indent=2, ensure_ascii=False)
        return payload_to_write
