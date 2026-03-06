# CARLA 0.9.16 Simulation Control Layer MVP

This project implements a minimal, runnable simulation orchestration layer for CARLA 0.9.16.

Scope of this phase:
- Run lifecycle orchestration and state machine
- Descriptor-based scenario execution
- API control plane
- Executor control plane with single tick authority
- Artifact/log output per run

Out of scope of this phase:
- HIL gateway
- Raspberry Pi integration
- USB camera emulation
- Real sensor injection
- Complex frontend/UI
- Distributed scheduler

## Project Layout

```text
carla_web_platform/
  app/
    api/
      main.py
      routes_runs.py
      routes_scenarios.py
      schemas.py
    core/
      config.py
      logging.py
      errors.py
      models.py
    orchestrator/
      run_manager.py
      state_machine.py
      queue.py
    executor/
      service.py
      carla_client.py
      sim_controller.py
      scenario_adapter.py
      recorder.py
      telemetry.py
    scenario/
      descriptor.py
      validators.py
      registry.py
      runtime.py
      builtins/
        empty_drive.py
        follow_lane.py
        npc_crossing.py
    storage/
      run_store.py
      artifact_store.py
    utils/
      time_utils.py
      file_utils.py
  configs/
    scenarios/
      sample_empty_drive.yaml
      sample_follow_lane.yaml
      sample_npc_crossing.yaml
  scripts/
    start_api.sh
    start_executor.sh
    start_platform.sh
  run_platform.sh
  tests/
    test_run_state_machine.py
    test_scenario_descriptor.py
    test_api_runs.py
    test_executor_failure.py
    test_artifacts.py
  docker/
    Dockerfile.api
    Dockerfile.executor
    docker-compose.yml
  artifacts/
  run_data/
  DESIGN.md
  requirements.txt
```

## Run State Machine

Supported states:
- `CREATED`
- `QUEUED`
- `STARTING`
- `RUNNING`
- `PAUSED` (reserved)
- `STOPPING`
- `COMPLETED`
- `FAILED`
- `CANCELED`

State transitions are centrally validated in `app/orchestrator/state_machine.py`.

## API Endpoints

- `POST /runs` create run from descriptor payload or descriptor path
- `POST /runs/{run_id}/start` queue run for execution
- `POST /runs/{run_id}/stop` request stop/cancel
- `POST /runs/{run_id}/cancel` request cancel
- `GET /runs/{run_id}` get run status and metadata
- `GET /runs` list runs (supports `?status=` filter)
- `GET /runs/{run_id}/events` list run events
- `GET /scenarios` list builtins and sample descriptors

## Artifact Output

Each run writes to:

```text
artifacts/<run_id>/
  config_snapshot.json
  run.log
  events.jsonl
  metrics.json
  status.json
  recorder/
  outputs/
```

## Quick Start

### 1) Start CARLA server only

From project root:

```bash
docker compose -f docker/docker-compose.yml up -d carla-server
```

### 2) Start API and executor

```bash
docker compose -f docker/docker-compose.yml up -d --build sim-executor
```

API default address: `http://localhost:8000`

`Dockerfile.api` is kept for optional split deployment, but the default MVP compose runs API + executor in the same `sim-executor` container to keep a 2-container setup (`carla-server` + `sim-executor`).

### 3) Create and run a scenario

Create run:

```bash
curl -s -X POST http://localhost:8000/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "descriptor_path": "/app/configs/scenarios/sample_empty_drive.yaml"
  }'
```

Start run:

```bash
curl -s -X POST http://localhost:8000/runs/<run_id>/start
```

Stop run:

```bash
curl -s -X POST http://localhost:8000/runs/<run_id>/stop
```

Get run:

```bash
curl -s http://localhost:8000/runs/<run_id>
```

Get events:

```bash
curl -s http://localhost:8000/runs/<run_id>/events
```

## Local (without Docker)

```bash
pip install -r requirements.txt
bash run_platform.sh
```

Set env vars as needed:
- `CARLA_HOST`
- `CARLA_PORT`
- `TRAFFIC_MANAGER_PORT`
- `RUNS_ROOT`
- `COMMANDS_ROOT`
- `ARTIFACTS_ROOT`

## Tests

```bash
pytest -q
```

Covered:
- run state transitions
- descriptor validation
- API create/start/stop flow
- executor exception -> `FAILED`
- artifact directory creation

## Current Limitations

- Builtin scenarios are intentionally minimal and not ScenarioRunner-integrated yet.
- No websocket streaming or advanced telemetry backend.
- No HIL data channel.
- No multi-run parallel scheduling.
- `PAUSED` lifecycle is reserved but not fully implemented.

See [DESIGN.md](./DESIGN.md) for design rationale and next-step extension plan.
