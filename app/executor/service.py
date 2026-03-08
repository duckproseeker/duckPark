from __future__ import annotations

import logging
import time

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.executor.sim_controller import SimController
from app.orchestrator.queue import FileCommandQueue, RunCommandType
from app.storage.artifact_store import ArtifactStore
from app.storage.executor_store import ExecutorStore
from app.storage.run_control_store import RunControlStore
from app.storage.run_store import RunStore
from app.utils.time_utils import now_utc

logger = logging.getLogger(__name__)


class ExecutorService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._run_store = RunStore(self._settings.runs_root)
        self._artifact_store = ArtifactStore(self._settings.artifacts_root)
        self._queue = FileCommandQueue(self._settings.commands_root)
        self._executor_store = ExecutorStore(self._settings.executor_root)
        self._control_store = RunControlStore(self._settings.controls_root)
        self._sim_controller = SimController(
            settings=self._settings,
            run_store=self._run_store,
            artifact_store=self._artifact_store,
            control_store=self._control_store,
        )

    def _write_heartbeat(
        self, status: str, active_run_id: str | None = None, last_command_run_id: str | None = None
    ) -> None:
        self._executor_store.write_heartbeat(
            {
                "status": status,
                "active_run_id": active_run_id,
                "last_command_run_id": last_command_run_id,
                "updated_at_utc": now_utc().isoformat(),
                "pending_commands": self._queue.count_pending(),
            }
        )

    def run_forever(self) -> None:
        logger.info("Executor service started")
        self._write_heartbeat("READY")
        while True:
            self._write_heartbeat("READY")
            command = self._queue.pop_next()
            if command is None:
                time.sleep(self._settings.command_poll_interval_seconds)
                continue

            logger.info(
                "Received command %s for run %s", command.command_type, command.run_id
            )
            if command.command_type == RunCommandType.START:
                self._write_heartbeat(
                    "RUNNING",
                    active_run_id=command.run_id,
                    last_command_run_id=command.run_id,
                )
                try:
                    self._sim_controller.execute_run(command.run_id)
                finally:
                    self._write_heartbeat(
                        "READY", last_command_run_id=command.run_id
                    )


def main() -> None:
    setup_logging()
    service = ExecutorService()
    service.run_forever()


if __name__ == "__main__":
    main()
