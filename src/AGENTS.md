# AGENTS.md

## Scope

- The active product codebase is `carla_web_platform/`. Treat it as the default working directory for implementation tasks.
- This laptop is for reading and editing code first. Do not assume local deployment, local containers, or local CARLA runtime are the source of truth.
- The real deployment and debugging environment is the remote server `192.168.110.151`.

## Confirmed Remote Environment

- Verified on `2026-03-14`.
- SSH target confirmed from local SSH config and live login: `du@192.168.110.151`.
- Remote home directory: `/home/du`.
- Main development container currently in use: `ros2-dev`.
- Container working directory: `/ros2_ws`.
- Main source mount for the repo: `/home/du/ros2-humble/src` -> `/ros2_ws/src`.
- Active repo path on the server: `/home/du/ros2-humble/src/carla_web_platform`.
- The CARLA server is not a permanently running service by default.
- `~/startCarla.sh` starts a separate CARLA container from `carlasim/carla:0.9.16` with host networking and `--ros2`.
- Important naming correction: the verified container name is `ros2-dev`, not `ros2_dev`.
- Do not write plaintext passwords or other secrets into repo files, commits, or generated docs. Credentials should stay out-of-band.

## Primary Workflow

- Make code changes locally in this workspace.
- For runtime verification, container debugging, CARLA startup, ROS2 checks, or deployment smoke tests, use the remote server.
- When a task depends on the real environment, prefer remote verification over local guesses.
- Before changing code, read the relevant local files first, then map the verification path to the remote server if needed.

## Remote Execution Rules

- For server work, start from `ssh du@192.168.110.151`.
- For work inside the main dev container, use `docker exec -it ros2-dev bash`.
- For CARLA-dependent work, check whether CARLA is already running before assuming it exists.
- If CARLA is required and not running, start it on the server with `bash ~/startCarla.sh`.
- Any instruction that depends on container names, mounted paths, or runtime services should prefer the verified values above over older guesses.

## Local vs Remote Validation

- Local validation is appropriate for static or code-only checks:
  - `cd carla_web_platform && make lint`
  - `cd carla_web_platform && pytest -q`
  - `cd carla_web_platform/frontend && npm run check-types`
  - `cd carla_web_platform/frontend && npm run build`
- Local Python note:
  - Verified local conda environment for Python 3.10 work: `duckpark-carla-web`.
  - If contract export or backend validation fails under the system interpreter, use that env or let `make export-openapi` fall back to it.
- Remote validation is required for anything involving:
  - Docker or container lifecycle
  - CARLA connectivity or map loading
  - executor behavior
  - ROS2 integration
  - gateway behavior
  - end-to-end `/ui` smoke on the deployed stack
- If validation was only local, say so explicitly.
- If validation used the remote server, state whether CARLA was actually running during the check.

## Code Architecture Rules

- Frontend pages/components must not call raw `fetch` directly. Use `frontend/src/api/client.ts` and domain modules under `frontend/src/api/`.
- Backend API routes must not write run, capture, or gateway files directly. Keep using the existing service, manager, registry, and storage layers.
- Do not bypass `app/core/config.py` with ad hoc environment parsing.
- Keep the existing boundary shape:
  - `frontend/src/pages/*` -> `frontend/src/api/*` -> `app/api/routes_*.py` -> service/manager/store -> executor/gateway/runtime side effects
- Do not add a second source of server state beyond TanStack Query for REST-backed data unless a task explicitly requires it.

## API Contract Maintenance

- Current pain point: backend request/response models and frontend API types are duplicated manually.
- Today the contract is spread across:
  - `app/api/schemas.py`
  - `app/api/routes_*.py`
  - backend payload builder functions
  - `frontend/src/api/types.ts`
  - `frontend/src/api/*.ts`
  - route tests under `tests/`
- The current generated-contract workflow lives in:
  - `carla_web_platform/scripts/export_openapi.py`
  - `carla_web_platform/contracts/openapi.json`
  - `carla_web_platform/frontend/src/api/generated/`
- Contract sync commands:
  - `cd carla_web_platform && make export-openapi`
  - `cd carla_web_platform && make contract-sync`
- Short-term rule:
  - Any API shape change must update backend schema or payload code, frontend wrapper usage, and tests in the same change.
  - Do not change wire fields or wrapper shapes in only one layer.
  - Do not redefine server payload types inside page components.
- Preferred future direction:
  - Treat FastAPI OpenAPI output as the single contract source of truth.
  - Add a repeatable export step for `openapi.json` from `app.api.main:app`.
  - Prefer generated TypeScript types or a generated client from that OpenAPI snapshot instead of continuing to expand hand-maintained duplicates.
  - If introducing code generation, do it incrementally by domain rather than as a full rewrite in one change.
- Until code generation exists, any contract-related task should use an `api-contract-sync` pass.

## Files To Read First

- UI change:
  - `carla_web_platform/frontend/src/app/`
  - `carla_web_platform/frontend/src/pages/`
  - `carla_web_platform/frontend/src/components/`
  - `carla_web_platform/frontend/src/api/`
- API or contract change:
  - `carla_web_platform/app/api/main.py`
  - `carla_web_platform/app/api/schemas.py`
  - relevant `carla_web_platform/app/api/routes_*.py`
  - matching `carla_web_platform/frontend/src/api/*.ts`
  - `carla_web_platform/frontend/src/api/types.ts`
  - matching `carla_web_platform/tests/test_api_*.py`
- Runtime or integration change:
  - `carla_web_platform/app/core/config.py`
  - `carla_web_platform/app/executor/`
  - `carla_web_platform/app/orchestrator/`
  - `carla_web_platform/scripts/start_platform.sh`

## Change Scope

- Keep changes inside the touched flow.
- Do not mix unrelated UI refactors into API or executor work.
- For changes spanning frontend, backend, and runtime behavior, use a `full-stack-change-planner` pass first.
- For remote-runtime changes, use a `backend-integration-validator` pass before handoff.

## Uncertainty Tags

- Use `TODO` for a known repo gap that should be handled later.
- Use `NEEDS_CONFIRMATION` when a fact depends on the remote environment, deployment policy, or hardware setup and has not been verified.
- Use `ASSUMPTION` only when a local working assumption is needed to continue without inventing certainty.

## Repo Notes

- No checked-in OpenAPI snapshot or TS client generation pipeline was found in this workspace during the `2026-03-14` scan.
- `未识别到明确 MCP 配置`.
