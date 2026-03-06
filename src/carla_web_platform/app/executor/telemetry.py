from __future__ import annotations

import time

from app.core.models import RunMetrics, RunStatus
from app.utils.time_utils import now_utc


class TelemetryCollector:
    def __init__(self, run_id: str, scenario_name: str, map_name: str) -> None:
        self._wall_start = time.monotonic()
        self._metrics = RunMetrics(
            run_id=run_id,
            scenario_name=scenario_name,
            map_name=map_name,
            start_time=now_utc(),
        )

    def on_tick(self, frame: int, sim_time: float) -> None:
        self._metrics.current_tick = frame
        self._metrics.sim_time = sim_time

    def finalize(
        self,
        final_status: RunStatus,
        failure_reason: str | None,
        spawned_actors_count: int,
    ) -> RunMetrics:
        self._metrics.end_time = now_utc()
        self._metrics.final_status = final_status
        self._metrics.failure_reason = failure_reason
        self._metrics.wall_time = time.monotonic() - self._wall_start
        self._metrics.spawned_actors_count = spawned_actors_count
        return self._metrics
