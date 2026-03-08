# Codex Project Profile

Scan scope: `/Users/kavin/Documents/GitHub/duckPark/src` on 2026-03-08.

## Confirmed Structure

- Workspace root contains:
  - `carla_web_platform/`
  - `scripts/`
- Active application is `carla_web_platform/`.
- Backend lives in `carla_web_platform/app/`.
- Frontend lives in `carla_web_platform/frontend/`.
- Tests live in `carla_web_platform/tests/`.
- Infra/runtime files live in `carla_web_platform/docker/`, `carla_web_platform/deploy/`, `carla_web_platform/scripts/`.

## Confirmed Stack

- Backend: FastAPI, Pydantic v2, Uvicorn, pytest, Ruff, Black, isort.
- Frontend: React 19, TypeScript, Vite 5, React Router, TanStack Query 5, Tailwind CSS.
- Runtime: Docker multi-stage build, Docker Compose, `.env.local` loaded by `scripts/start_platform.sh`.
- Persistence: file-backed JSON stores in `run_data/` and `artifacts/`.

## Confirmed Data Flow

- React pages call `frontend/src/api/*`.
- API calls go to FastAPI routes in `app/api/`.
- Routes delegate to managers/registries and file stores.
- Run start requests enqueue file commands consumed by `app/executor/service.py`.
- Gateway state comes from `app/hil/gateway_agent.py`.
- UI is served at `/ui`; legacy fallback exists at `/ui-legacy`.

## Confirmed Contract/Validation Facts

- Contract source is FastAPI routes + Pydantic schemas.
- Swagger/OpenAPI is available at runtime through `/docs`.
- Frontend API types are hand-maintained in `frontend/src/api/types.ts`.
- Backend commands found:
  - `make format`
  - `make lint`
  - `make test`
  - `bash scripts/start_platform.sh`
- Frontend commands found:
  - `npm run dev`
  - `npm run build`
  - `npm run preview`
  - `npm run check-types`
- No frontend lint/test/e2e script detected.
- No `.github/workflows/` CI config detected.
- No codegen/OpenAPI export command detected.

## Design/System Facts

- Reusable UI components exist under `frontend/src/components/common/` and `frontend/src/components/layout/`.
- Visual tokens come from `frontend/tailwind.config.cjs` and `frontend/src/styles/globals.css`.
- No Storybook or external design-system package detected.

## External Systems Identified

- CARLA server and Traffic Manager.
- Pi gateway agent and Pi systemd unit files.
- Docker Compose stack with `carla-server` and `sim-executor`.
- No explicit MCP configuration detected.

## Risks

- Manual TS/Python contract duplication can drift.
- Endpoint list envelopes are inconsistent by domain.
- React console and legacy UI coexist.
- Live map/executor validation depends on reachable CARLA runtime.
- File-backed queue/store model is local-first and not multi-instance hardened.
- Frontend lacks automated tests and lint coverage.

## Unconfirmed Items

- `ASSUMPTION`: primary future Codex work should target `carla_web_platform/`; root-level `scripts/` is secondary until a task proves otherwise.
- `NEEDS_CONFIRMATION`: whether auth, token injection, or protected deployments exist outside the repo.
- `NEEDS_CONFIRMATION`: whether legacy UI retirement is planned.
- `NEEDS_CONFIRMATION`: whether Pi deployment files represent current production practice.
- `TODO`: establish contract export/codegen if frontend/backend iteration becomes frequent.
- `TODO`: add frontend lint and automated UI smoke/e2e coverage.
