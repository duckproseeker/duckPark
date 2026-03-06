from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

from app.core.config import Settings
from app.core.models import EventLevel, RunEvent, RunStatus
from app.executor.carla_client import CarlaClient
from app.executor.recorder import RecorderManager
from app.executor.scenario_adapter import ScenarioAdapter
from app.executor.telemetry import TelemetryCollector
from app.scenario.runtime import ScenarioRuntimeContext
from app.scenario.validators import validate_descriptor
from app.storage.artifact_store import ArtifactStore
from app.storage.run_store import RunStore
from app.utils.time_utils import now_utc

logger = logging.getLogger(__name__)


class SimController:
    def __init__(
        self,
        settings: Settings,
        run_store: RunStore,
        artifact_store: ArtifactStore,
        client_factory: Callable[[str, int, float, int], CarlaClient] = CarlaClient,
    ) -> None:
        self._settings = settings
        self._run_store = run_store
        self._artifact_store = artifact_store
        self._client_factory = client_factory
        self._scenario_adapter = ScenarioAdapter()
        self._recorder = RecorderManager()

    def _emit_event(
        self,
        run_id: str,
        event_type: str,
        message: str,
        payload: dict[str, Any] | None = None,
        level: EventLevel = EventLevel.INFO,
        ) -> None:
        event = RunEvent(
            timestamp=now_utc(),
            run_id=run_id,
            level=level,
            event_type=event_type,
            message=message,
            payload=payload or {},
        )
        self._artifact_store.append_event(event)
        self._artifact_store.append_run_log(
            run_id,
            f"[{event.timestamp.isoformat()}] {event.level.value} {event.event_type} {event.message}",
        )

    def _persist_status(self, run_id: str) -> None:
        run = self._run_store.get(run_id)
        self._artifact_store.write_status(run)

    def _transition(
        self,
        run_id: str,
        target: RunStatus,
        error_reason: str | None = None,
        set_started_at: bool = False,
        set_ended_at: bool = False,
    ) -> None:
        run = self._run_store.transition(
            run_id,
            target,
            error_reason=error_reason,
            set_started_at=set_started_at,
            set_ended_at=set_ended_at,
        )
        self._artifact_store.write_status(run)

    def execute_run(self, run_id: str) -> None:
        run = self._run_store.get(run_id)
        descriptor = validate_descriptor(run.descriptor)

        if run.status != RunStatus.QUEUED:
            logger.warning("Skipping run %s because status=%s", run_id, run.status)
            return

        if run.cancel_requested:
            self._transition(run_id, RunStatus.CANCELED, set_ended_at=True)
            self._emit_event(run_id, "SCENARIO_COMPLETED", "Run canceled before start")
            return

        telemetry = TelemetryCollector(run_id, descriptor.scenario_name, descriptor.map_name)
        carla_client: CarlaClient | None = None
        context: ScenarioRuntimeContext | None = None
        failure_reason: str | None = None
        final_status: RunStatus = RunStatus.COMPLETED

        try:
            self._transition(run_id, RunStatus.STARTING)
            self._emit_event(run_id, "RUN_STARTING", "Executor started run")

            if not descriptor.sync.enabled:
                raise RuntimeError("sync.enabled must be true. Executor owns single tick authority")

            carla_client = self._client_factory(
                self._settings.carla_host,
                self._settings.carla_port,
                self._settings.carla_timeout_seconds,
                self._settings.traffic_manager_port,
            )
            carla_client.connect()
            self._emit_event(run_id, "CARLA_CONNECTED", "Connected to CARLA server")

            carla_client.load_map(descriptor.map_name)
            self._emit_event(run_id, "MAP_LOADED", "Loaded CARLA map", payload={"map_name": descriptor.map_name})

            carla_client.set_weather(descriptor.weather.preset)
            carla_client.configure_world_sync(True, descriptor.sync.fixed_delta_seconds)
            self._emit_event(
                run_id,
                "WORLD_SYNC_ENABLED",
                "World synchronous mode enabled",
                payload={"fixed_delta_seconds": descriptor.sync.fixed_delta_seconds},
            )

            if descriptor.traffic.enabled:
                carla_client.configure_tm_sync(True)
                self._emit_event(run_id, "TM_SYNC_ENABLED", "Traffic Manager synchronous mode enabled")

            ego_vehicle = carla_client.spawn_ego_vehicle(
                descriptor.ego_vehicle.blueprint,
                descriptor.ego_vehicle.spawn_point.model_dump(mode="python"),
            )
            self._emit_event(
                run_id,
                "EGO_SPAWNED",
                "Ego vehicle spawned",
                payload={"blueprint": descriptor.ego_vehicle.blueprint},
            )

            context = ScenarioRuntimeContext(
                run_id=run_id,
                descriptor=descriptor,
                carla_client=carla_client,
                ego_vehicle=ego_vehicle,
            )
            self._scenario_adapter.setup(context)

            self._recorder.start(run_id, descriptor, carla_client, self._artifact_store.run_dir(run_id))

            self._transition(run_id, RunStatus.RUNNING, set_started_at=True)
            self._emit_event(run_id, "SCENARIO_STARTED", "Scenario execution started")

            timeout_seconds = descriptor.termination.timeout_seconds
            max_ticks = int(timeout_seconds / descriptor.sync.fixed_delta_seconds)

            for tick_count in range(max_ticks):
                latest = self._run_store.get(run_id)
                if latest.stop_requested or latest.cancel_requested:
                    self._transition(run_id, RunStatus.STOPPING)
                    self._emit_event(run_id, "RUN_STOPPING", "Run entered STOPPING state")
                    break

                tick_result = carla_client.tick()
                telemetry.on_tick(tick_result.frame, tick_result.sim_time)
                self._scenario_adapter.on_tick(context, tick_count=tick_count, sim_time=tick_result.sim_time)

            latest = self._run_store.get(run_id)
            if latest.cancel_requested:
                final_status = RunStatus.CANCELED
            elif latest.stop_requested and latest.status == RunStatus.STOPPING:
                final_status = RunStatus.COMPLETED
            else:
                final_status = RunStatus.COMPLETED

            self._emit_event(
                run_id,
                "SCENARIO_COMPLETED",
                "Scenario loop finished",
                payload={"final_status": final_status.value},
            )
        except Exception as exc:  # noqa: BLE001
            failure_reason = str(exc)
            final_status = RunStatus.FAILED
            logger.error("Run %s failed: %s", run_id, traceback.format_exc())
            self._emit_event(
                run_id,
                "RUN_FAILED",
                "Run failed due to exception",
                payload={"error": failure_reason},
                level=EventLevel.ERROR,
            )
        finally:
            self._emit_event(run_id, "CLEANUP_STARTED", "Run cleanup started")

            if context is not None:
                try:
                    self._scenario_adapter.teardown(context)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Scenario teardown failed for run %s: %s", run_id, exc)

            spawned_count = 0
            if carla_client is not None:
                try:
                    self._recorder.stop(carla_client)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Recorder stop failed for run %s: %s", run_id, exc)

                try:
                    spawned_count = carla_client.spawned_actor_count()
                    carla_client.cleanup()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("CARLA cleanup failed for run %s: %s", run_id, exc)

            self._emit_event(run_id, "CLEANUP_FINISHED", "Run cleanup finished")

            metrics = telemetry.finalize(
                final_status=final_status,
                failure_reason=failure_reason,
                spawned_actors_count=spawned_count,
            )
            self._artifact_store.write_metrics(metrics)

            run_after = self._run_store.get(run_id)
            if run_after.status in {RunStatus.COMPLETED, RunStatus.CANCELED, RunStatus.FAILED}:
                self._artifact_store.write_status(run_after)
                return

            if final_status == RunStatus.FAILED:
                self._transition(
                    run_id,
                    RunStatus.FAILED,
                    error_reason=failure_reason,
                    set_ended_at=True,
                )
            else:
                if run_after.status == RunStatus.STOPPING and final_status == RunStatus.CANCELED:
                    self._transition(run_id, RunStatus.CANCELED, set_ended_at=True)
                elif run_after.status == RunStatus.STOPPING:
                    self._transition(run_id, RunStatus.COMPLETED, set_ended_at=True)
                else:
                    self._transition(run_id, RunStatus.COMPLETED, set_ended_at=True)
