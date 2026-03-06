from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class EventLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class RunEvent(BaseModel):
    timestamp: datetime
    run_id: str
    level: EventLevel = EventLevel.INFO
    event_type: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)


class RunMetrics(BaseModel):
    run_id: str
    scenario_name: str
    map_name: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    final_status: RunStatus | None = None
    failure_reason: str | None = None
    current_tick: int | None = None
    sim_time: float | None = None
    wall_time: float | None = None
    spawned_actors_count: int = 0


class RunRecord(BaseModel):
    run_id: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None
    error_reason: str | None = None
    stop_requested: bool = False
    cancel_requested: bool = False
    scenario_name: str
    map_name: str
    descriptor: dict[str, Any]
    artifact_dir: str
