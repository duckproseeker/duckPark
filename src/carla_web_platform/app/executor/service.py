from __future__ import annotations

import logging
import time

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.executor.sim_controller import SimController
from app.orchestrator.queue import FileCommandQueue, RunCommandType
from app.storage.artifact_store import ArtifactStore
from app.storage.run_store import RunStore

logger = logging.getLogger(__name__)


class ExecutorService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._run_store = RunStore(self._settings.runs_root)
        self._artifact_store = ArtifactStore(self._settings.artifacts_root)
        self._queue = FileCommandQueue(self._settings.commands_root)
        self._sim_controller = SimController(
            settings=self._settings,
            run_store=self._run_store,
            artifact_store=self._artifact_store,
        )

    def run_forever(self) -> None:
        logger.info("Executor service started")
        while True:
            command = self._queue.pop_next()
            if command is None:
                time.sleep(self._settings.command_poll_interval_seconds)
                continue

            logger.info("Received command %s for run %s", command.command_type, command.run_id)
            if command.command_type == RunCommandType.START:
                self._sim_controller.execute_run(command.run_id)


def main() -> None:
    setup_logging()
    service = ExecutorService()
    service.run_forever()


if __name__ == "__main__":
    main()
