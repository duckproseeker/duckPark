# AGENTS.md

## Project Overview

- Scope: this `src/` workspace is a wrapper directory. The active product codebase is `carla_web_platform/`; keep that as the default working directory for implementation tasks.
- Project type: single-repo full-stack control platform for CARLA simulation orchestration, Pi gateway status/capture management, and a browser control console.
- Repo structure:
  - `carla_web_platform/app/`: FastAPI API, executor service, orchestrator, scenario registry, HIL gateway agent, file-backed storage.
  - `carla_web_platform/frontend/`: React 19 + TypeScript + Vite console mounted under `/ui`.
  - `carla_web_platform/configs/`: scenario YAML and sensor profile YAML.
  - `carla_web_platform/docker/`: Dockerfiles and `docker-compose.yml`.
  - `carla_web_platform/deploy/pi/`: Pi systemd units and env example.
  - `carla_web_platform/tests/`: pytest-based API, storage, executor, gateway, UI smoke tests.
- Frontend/backend boundary:
  - Frontend only talks to FastAPI over REST via `frontend/src/api/*`.
  - FastAPI routes live in `app/api/*` and delegate to manager/registry/store layers.
  - CARLA tick ownership stays inside `app/executor/`.
- Shared layer:
  - No shared TS/Python package exists.
  - Shared contract is JSON over REST plus duplicated types: Pydantic schema/route payloads on backend and hand-maintained TS interfaces in `frontend/src/api/types.ts`.
  - Shared runtime config lives in `.env.local`, `app/core/config.py`, `configs/scenarios/`, and `configs/sensors/`.
- Confirmed stack:
  - Backend: Python 3.10, FastAPI, Pydantic v2, Uvicorn, pytest, Ruff, Black, isort.
  - Frontend: React 19, TypeScript, Vite 5, React Router, TanStack Query 5, Tailwind CSS, custom CSS tokens.
  - Infra: Docker multi-stage builds, Docker Compose, Pi systemd services.
  - Storage/queue: file-backed JSON stores under `run_data/` and artifacts under `artifacts/`.
- Data flow:
  - `frontend/src/pages/*` -> `frontend/src/api/*` -> `app/api/routes_*.py` -> `RunManager` / `CaptureManager` / `GatewayRegistry` -> file stores and command queue -> `app.executor.service` or `app.hil.gateway_agent` -> artifacts/run_data -> polled back through REST.
- Collaboration mode fit:
  - `ui-system-builder`: applicable.
  - `api-contract-sync`: applicable.
  - `backend-integration-validator`: applicable.
  - `frontend-feature-scaffold`: applicable.
  - `design-to-implementation-reviewer`: applicable.
  - `full-stack-change-planner`: applicable because changes often span React UI, FastAPI routes, executor/gateway flows, and Docker/runtime config.
- `ASSUMPTION`: the sibling `src/scripts/` directory is not part of the primary app flow because no direct references were identified during this scan. Re-check if a task explicitly mentions it.

## Working Rules for Codex

- Read before changing:
  - UI change: `carla_web_platform/frontend/src/app/`, `carla_web_platform/frontend/src/components/`, `carla_web_platform/frontend/src/pages/`, `carla_web_platform/frontend/src/styles/globals.css`, `carla_web_platform/frontend/tailwind.config.cjs`, `carla_web_platform/frontend/vite.config.ts`.
  - API/contract change: `carla_web_platform/app/api/schemas.py`, target `carla_web_platform/app/api/routes_*.py`, `carla_web_platform/frontend/src/api/*.ts`, `carla_web_platform/frontend/src/api/types.ts`, relevant pytest files under `carla_web_platform/tests/`.
  - Runtime/integration change: `carla_web_platform/app/core/config.py`, `carla_web_platform/app/executor/service.py`, `carla_web_platform/app/orchestrator/queue.py`, `carla_web_platform/scripts/start_platform.sh`, `carla_web_platform/docker/docker-compose.yml`.
- Default working directory: `carla_web_platform/`.
- Do not bypass architectural layers:
  - Do not call `fetch` directly from pages/components. Use `frontend/src/api/client.ts` and domain modules under `frontend/src/api/`.
  - Do not write run/capture/gateway JSON files directly from API routes or frontend code. Go through manager/registry/store abstractions already in `app/orchestrator/` and `app/storage/`.
  - Do not add a second CARLA tick owner outside `app/executor/`.
  - Do not mutate request/response shapes in route payload builders without syncing frontend types and tests.
  - Do not bypass `app/core/config.py` with ad hoc env parsing in Python modules.
  - Do not introduce a second server-state source beyond TanStack Query for REST-backed data.
- Do not add unrelated tech:
  - Do not add Redux/Zustand/global stores unless the task explicitly requires cross-route client state that local state + Query cannot cover.
  - Do not add a new component library or styling system; extend the existing Tailwind theme, CSS variables, and `components/common`.
  - Do not remove `/ui-legacy` fallback or legacy template assets unless the task explicitly includes legacy UI retirement.
- Change scope control:
  - Keep changes inside the touched flow. A run-only change should not refactor capture/gateway domains unless the contract truly overlaps.
  - For changes touching frontend + backend + executor/gateway integration, start from a `full-stack-change-planner` pass before editing multiple layers.
  - Preserve existing snake_case wire format unless a task explicitly approves a full contract rename.
- Required validation before handoff:
  - Backend-only changes: run `make lint` and `pytest -q` inside `carla_web_platform/`.
  - Frontend-only changes: run `npm run check-types` and `npm run build` inside `carla_web_platform/frontend/`.
  - Contract changes: run both backend and frontend validation sets.
  - Integration/runtime changes: add a smoke path using `/healthz`, `/system/status`, `/ui`, and the changed endpoint or screen.
- Uncertainty handling:
  - Use `TODO` when the repo shows a gap that must be filled later.
  - Use `NEEDS_CONFIRMATION` when the requirement may exist externally but is not provable from the repo.
  - Use `ASSUMPTION` only for a local working assumption that lets work continue without fabricating certainty.

## Frontend Architecture Rules

- Current frontend layout is:
  - `frontend/src/api/`: REST client and endpoint wrappers.
  - `frontend/src/app/`: router and providers.
  - `frontend/src/components/common/` and `frontend/src/components/layout/`: reusable UI building blocks.
  - `frontend/src/pages/<domain>/`: route-level containers.
  - `frontend/src/lib/`: shared formatting helpers.
  - `frontend/src/styles/`: Tailwind entry and global CSS tokens.
- Organization rules:
  - Keep route containers in `src/pages/<domain>/`.
  - Keep reusable visual primitives in `src/components/common/` or `src/components/layout/`.
  - Keep data access in `src/api/`.
  - If a domain grows across multiple routes, create a focused `src/features/<domain>/` subtree instead of scattering duplicate helpers across pages.
  - `TODO`: the repo currently has no dedicated `hooks/` or `services/` directory. Add one only when a shared abstraction is used by more than one route or domain.
- Boundary rules:
  - Pages may orchestrate queries/mutations and local form state, but must not embed raw HTTP details.
  - Normalize or derive data either in `src/api/*` or small helper functions, not inline inside JSX-heavy view blocks.
  - Keep server state in TanStack Query; keep filter/sort/modal/form draft state local to the page or feature.
  - Do not duplicate the same server payload in both Query cache and a custom global store.
- Loading/empty/error/form state rules:
  - Every new query-backed page or panel must render explicit loading, empty, and error states.
  - Reuse existing primitives such as `EmptyState`, `Panel`, `PageHeader`, `StatusPill`, `MetricCard`, `JsonBlock` before creating new variants.
  - Forms and mutations must expose pending and failure states; do not hide API errors.
  - Polling-heavy pages should stay aligned with existing cadence patterns: most pages poll at 3s or 5s intervals. Do not add more aggressive polling without a measured reason.
- Styling system rules:
  - Use Tailwind utility classes plus the design tokens in `tailwind.config.cjs` and CSS variables/classes in `src/styles/globals.css`.
  - Prefer the existing visual language: blue/navy token set, glass-card panels, rounded surfaces, and `horizon-*` button/card classes already in use.
  - Do not introduce CSS-in-JS, inline style systems, or a parallel token set.
  - No Storybook or external design-system package is present. Treat `components/common/` plus `globals.css` as the design system source of truth.
- Responsive/accessibility/interaction rules:
  - Preserve the `/ui` basename routing contract from `src/app/router.tsx`.
  - New screens must work inside the existing `AppShell` layout and degrade on smaller widths.
  - Use semantic buttons/links/inputs and preserve keyboard access for forms and navigation.
  - Keep status colors and labels consistent with current status vocabulary: `CREATED`, `QUEUED`, `RUNNING`, `READY`, `ERROR`, `FAILED`, `CANCELED`, `OFFLINE`, and related variants.
- Hard prohibition:
  - Do not scatter API calls, data-shape conversions, or domain-level status logic across view components.

## Backend Integration Rules

- API entrypoint: `carla_web_platform/app/api/main.py`.
- Executor entrypoint: `python3 -m app.executor.service`.
- Gateway agent entrypoint: `python3 -m app.hil.gateway_agent`.
- API calling rules:
  - Frontend REST calls must go through `frontend/src/api/client.ts`.
  - Backend route handlers must keep using `ApiResponse` envelopes and existing `AppError -> HTTPException(detail={code,message})` mapping patterns.
  - New backend endpoints should follow the same response contract shape as neighboring routes in the same domain.
- Environment/base URL management:
  - Backend runtime env is loaded from `carla_web_platform/.env.local` by `scripts/start_platform.sh`.
  - Backend settings source of truth is `app/core/config.py`.
  - Frontend base URL is `VITE_API_BASE_URL`; if unset, Vite proxy in `frontend/vite.config.ts` is the local dev path.
  - Do not hardcode API origins inside components or endpoint modules.
- Auth/header/token rules:
  - No authentication or token injection mechanism was identified in the current repo.
  - `NEEDS_CONFIRMATION`: whether any external deployment requires auth, custom headers, or gateway signing.
  - Until confirmed, do not invent bearer-token injection, cookie assumptions, or auth middleware.
- Error-handling rules:
  - Preserve backend error `detail.code` and `detail.message` structure so `ApiClientError` continues to map correctly.
  - Keep domain errors specific: use `NOT_FOUND`, `CONFLICT`, `VALIDATION_ERROR`, or a similarly explicit code.
  - UI mutations and pages must surface error states instead of silently swallowing them.
- Retry/timeout/cancel rules:
  - Current frontend Query defaults: query retry `1`, mutation retry `0`, stale time `5000`, no refetch on window focus.
  - Current `api/client.ts` has no central timeout, no `AbortController`, and no backoff policy.
  - `TODO`: define a repo-wide timeout/cancellation pattern before adding long-running or user-cancelable HTTP flows.
  - Until then, do not add ad hoc per-page retry or timeout logic; centralize any change in `queryClient.ts` or `api/client.ts`.
- Mock/real integration switch:
  - No MSW/mock server/fixture-backed frontend switch was identified.
  - For UI/API work that does not require CARLA execution, use `bash scripts/start_platform.sh --no-executor`.
  - For real integration, use the live FastAPI service and, when needed, a live CARLA server plus Pi gateway agent.

## API Contract Sync Rules

- Contract source:
  - Primary source is the runtime FastAPI contract generated from `app/api/main.py`, route definitions in `app/api/routes_*.py`, and Pydantic models in `app/api/schemas.py`.
  - Swagger/OpenAPI is available at runtime via `/docs`.
  - `TODO`: there is no checked-in OpenAPI snapshot, export script, or code generation pipeline.
- Type synchronization source:
  - Frontend contract mirror is hand-maintained in `frontend/src/api/types.ts`.
  - Endpoint wrapper behavior is in `frontend/src/api/*.ts`.
- Sync workflow when fields change:
  - Update request/response schema or payload builder on backend.
  - Update route-specific tests under `tests/`.
  - Update matching TS interfaces in `frontend/src/api/types.ts`.
  - Update `frontend/src/api/*.ts` wrappers if list envelopes or endpoint paths change.
  - Update page/query/mutation usage if nullability, enum values, or nested shapes changed.
- Drift prevention rules:
  - Preserve wire-format field names in snake_case. Do not camelCase backend payloads inside the API layer unless a repo-wide mapper is introduced.
  - If a list endpoint returns wrapped data, preserve the exact wrapper shape. Current shapes are not uniform:
    - `/runs` returns a raw array in `data`.
    - `/gateways` returns `{ gateways: [...] }`.
    - `/captures` returns `{ captures: [...] }`.
    - `/maps` returns `{ maps: [...] }`.
  - When enum/status values change, update backend enums, UI status rendering logic, and any filters that hardcode status sets.
  - When nullability changes, update both Pydantic validators/defaults and TS optional/null types; do not let frontend infer certainty from runtime luck.
- Live dependency note:
  - `/maps` depends on a reachable CARLA server and may return `503`. Keep this behavior explicit in UI and tests.

## Validation and Testing Rules

- Preferred execution order:
  - `cd carla_web_platform && make lint`
  - `cd carla_web_platform/frontend && npm run check-types`
  - `cd carla_web_platform && pytest -q`
  - `cd carla_web_platform/frontend && npm run build`
- Backend test priority:
  - Prefer existing pytest coverage first. The repo already has API, storage, gateway, executor failure, descriptor, and UI smoke tests.
  - When changing a route contract, add or update the nearest route test file under `tests/test_api_*.py`.
- Frontend validation baseline:
  - `TODO`: no frontend lint script, unit test runner, integration test runner, Storybook, Playwright, or Cypress config was identified.
  - Minimum frontend acceptance for new work is:
    - `npm run check-types`
    - `npm run build`
    - manual or scripted smoke of the changed route under `/ui`
    - explicit verification of loading, empty, error, and success states
- Full-stack minimal integration path:
  - Start API-only stack with `bash scripts/start_platform.sh --no-executor` for UI/API changes that do not require CARLA.
  - Verify `/healthz`, `/system/status`, `/ui`, and the changed endpoint/page.
  - For run/executor flow changes, verify the queue and heartbeat path: create run -> start run -> check `/system/status` pending commands or executor heartbeat -> inspect `run_data/` and `artifacts/` effects.
  - For gateway/capture changes, verify gateway register/heartbeat and capture create/start/stop/sync flows through existing endpoints and tests.
- External dependency validation:
  - `NEEDS_CONFIRMATION`: any production-grade validation against a real Pi + HDMI/UVC chain.
  - If a change depends on CARLA maps or executor behavior, note whether validation used a live CARLA server or only offline tests.

## Skill-specific Operating Guidance

### ui-system-builder

- Trigger: changes to shared UI primitives, layout, styling tokens, route-level visual systems, or cross-page interaction consistency.
- Input must include: target screens, affected routes, required states, data dependencies, and whether legacy `/ui-legacy` must stay untouched.
- Output must include: updated component structure, token/class usage aligned with `globals.css` and Tailwind theme, and any route or navigation changes.
- Allowed modification areas: `frontend/src/components/`, `frontend/src/pages/`, `frontend/src/app/`, `frontend/src/styles/`, `frontend/tailwind.config.cjs`.
- Required checks: `npm run check-types`, `npm run build`, smoke the changed route under `/ui`.
- Common failure risks:
  - breaking `/ui` basename routing
  - duplicating styles outside current token system
  - introducing inconsistent status colors or button variants
  - regressing empty/error/loading states

### api-contract-sync

- Trigger: any backend route/schema/payload change or any detected drift between FastAPI payloads and `frontend/src/api/types.ts`.
- Input must include: endpoint path, request/response delta, error-code delta, and whether the change touches list wrappers or enum/nullability behavior.
- Output must include: backend schema/route updates, frontend type updates, API wrapper updates, affected test updates, and a short contract-diff summary.
- Allowed modification areas: `app/api/`, `app/core/models.py` when enum/model values change, `frontend/src/api/`, `tests/`, relevant docs.
- Required checks: `make lint`, `pytest -q`, `npm run check-types`, and `npm run build` when frontend types changed.
- Common failure risks:
  - forgetting that TS types are hand-maintained
  - changing one endpoint from wrapped to unwrapped data without updating callers
  - backend/frontend enum drift
  - nullability mismatches that only fail at runtime

### backend-integration-validator

- Trigger: changes touching executor lifecycle, queue behavior, run/capture/gateway persistence, runtime env, Docker startup, or Pi gateway connectivity.
- Input must include: changed flow, required external systems, expected artifacts/state transitions, and whether offline validation is acceptable.
- Output must include: executed validation steps, observed results, gaps caused by missing external systems, and follow-up TODO or NEEDS_CONFIRMATION items.
- Allowed modification areas: `app/`, `scripts/`, `docker/`, `deploy/`, `tests/`, relevant docs.
- Required checks: targeted pytest modules at minimum; add stack smoke using `/healthz`, `/system/status`, and affected endpoints; run broader validation when runtime scripts changed.
- Common failure risks:
  - queue state contamination from old `run_data/`
  - assuming executor is online when only API is running
  - depending on CARLA availability without declaring it
  - forgetting file-backed persistence side effects in tests and local runs

### frontend-feature-scaffold

- Trigger: adding a new screen, route, page-level workflow, or domain UI on top of existing REST endpoints.
- Input must include: route path, target endpoint(s), expected page states, status vocabulary, and whether data is read-only or mutation-heavy.
- Output must include: route registration, page component, API wrapper additions if needed, TS type usage, and consistent empty/error/loading handling.
- Allowed modification areas: `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/api/`, `frontend/src/lib/`, `frontend/src/app/router.tsx`.
- Required checks: `npm run check-types`, `npm run build`, and smoke of the new route under `/ui`.
- Common failure risks:
  - putting request logic directly in JSX files
  - duplicating domain types instead of reusing `src/api/types.ts`
  - adding feature state outside Query/local state without justification
  - missing route-link updates in the existing shell/navigation

### design-to-implementation-reviewer

- Trigger: design review, UI QA, implementation-vs-spec comparison, or a request to audit visual/interaction consistency.
- Input must include: design artifact or description, affected screens, intended states, and any known deviations already accepted by the user.
- Output must include: prioritized findings first, file/route references, and concrete mismatch descriptions covering layout, states, copy, accessibility, and status semantics.
- Allowed modification areas: none by default unless implementation is explicitly requested after review.
- Required checks: compare against `globals.css`, `tailwind.config.cjs`, common component usage, responsive behavior, and `/ui` route behavior.
- Common failure risks:
  - reviewing against a generic design standard instead of this repo’s established visual language
  - missing empty/error/loading state regressions
  - ignoring the dual React/legacy UI setup

### full-stack-change-planner

- Trigger: a task spans React UI, FastAPI routes, contract changes, executor/gateway behavior, Docker/runtime config, or deployment scripts.
- Input must include: user goal, touched domains, contract impact, required external systems, and acceptable validation depth.
- Output must include: impacted files/layers, data-flow changes, contract diff, execution sequence, validation matrix, and explicit blockers or assumptions.
- Allowed modification areas: entire `carla_web_platform/` tree plus repo docs when the task requires multi-layer work.
- Required checks: define the minimal safe validation set before coding; after implementation run all checks implied by touched layers.
- Common failure risks:
  - changing frontend and backend in different directions
  - underestimating live dependencies on CARLA or Pi hardware
  - mixing contract refactors with unrelated UI refactors
  - skipping artifact/queue/heartbeat verification for executor-adjacent changes

## MCP / External Systems

- MCP:
  - No explicit MCP configuration, MCP server definition, or Model Context Protocol integration was identified in this workspace.
  - Rule: write `未识别到明确 MCP 配置` unless future repo changes add concrete config or docs.
- External systems identified from repo evidence:
  - CARLA server and Traffic Manager, configured through `.env.local` and used by `app/executor/` plus `/maps`.
  - Pi gateway agent, started by `scripts/start_pi_gateway_agent.sh` and configured via `deploy/pi/gateway-agent.env.example`.
  - Pi HDMI/UVC bridge services managed by systemd unit files under `deploy/pi/`.
  - Runtime API documentation via FastAPI `/docs`.
- Usage boundary:
  - Do not assume external systems are locally available.
  - When a task depends on CARLA or Pi hardware, state whether validation was offline, simulated, or live.
  - Do not modify Pi service files or gateway env templates unless the task explicitly covers gateway deployment or hardware integration.

## Repo-specific Commands

- Run all commands from `carla_web_platform/` unless noted otherwise.
- `dev`:
  - Full platform: `bash scripts/start_platform.sh --carla-host 127.0.0.1 --carla-port 2000 --traffic-manager-port 8010`
  - API/UI only: `bash scripts/start_platform.sh --carla-host 127.0.0.1 --carla-port 2000 --traffic-manager-port 8010 --no-executor`
  - Frontend only: `cd frontend && npm run dev`
- `build`:
  - Frontend build: `cd frontend && npm run build`
  - Docker stack build/run: `docker compose -f docker/docker-compose.yml up -d --build sim-executor`
- `lint`:
  - Backend lint: `make lint`
  - `TODO`: no frontend lint script detected in `frontend/package.json`
- `typecheck`:
  - Frontend: `cd frontend && npm run check-types`
  - `TODO`: no dedicated backend static typecheck command detected
- `test`:
  - Backend tests: `make test`
- `e2e`:
  - `TODO`: no Playwright/Cypress/e2e command detected
- `codegen`:
  - `TODO`: no code generation command detected
- `contract-related`:
  - Runtime contract inspection: open `/docs` after starting FastAPI
  - `TODO`: no checked-in OpenAPI export or SDK generation command detected
- `format`:
  - Backend format: `make format`

## Known Risks / Needs Confirmation

- Risk: backend contract is duplicated manually into `frontend/src/api/types.ts`; drift is likely if backend payloads change without frontend sync.
- Risk: list endpoint envelope shapes are inconsistent across domains, so “generic list helper” refactors are likely to break callers.
- Risk: no frontend lint/unit/integration/e2e framework is present; current frontend safety net is typecheck + build + manual smoke only.
- Risk: no `.github/workflows/` CI pipeline was identified in this scanned workspace, so validation is not enforced centrally.
- Risk: React console and legacy UI coexist. Changes to `/ui`, asset mounting, or build output can silently regress fallback behavior.
- Risk: file-backed JSON stores and command queue are simple and local-first; concurrent writers or multi-instance deployment would need extra design.
- Risk: `/maps` and true executor validation depend on a reachable CARLA server; offline tests cannot fully prove those flows.
- Risk: no centralized frontend timeout/cancellation policy exists for REST requests.
- Risk: no mock-switch mechanism was identified; UI work may be tempted to fake data ad hoc unless explicitly constrained.
- `NEEDS_CONFIRMATION`: whether any deployment environment requires auth, RBAC, custom headers, or audit logging.
- `NEEDS_CONFIRMATION`: whether future work should retire `app/static/ui.js` + `app/templates/ui.html`, or keep the legacy control panel indefinitely.
- `NEEDS_CONFIRMATION`: whether Pi gateway deployment files under `deploy/pi/` are actively used in production or are only lab references.
- `TODO`: add an explicit, versioned contract export/codegen path if frontend/backend change frequency increases.
- `TODO`: add frontend lint and at least one automated UI smoke/e2e path if the React console becomes the primary operator surface.
