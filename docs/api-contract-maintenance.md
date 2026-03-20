# 前后端接口维护

## 基本原则

- FastAPI 路由和 Pydantic schema 是运行时契约真源。
- 前端不要手写猜测的字段，必须以 OpenAPI 和 `frontend/src/api/generated/openapi.ts` 为准。
- 页面只通过 `frontend/src/api/*` 访问后端，不要在页面组件里直接写 HTTP 细节。

## 契约变更时的最小流程

1. 修改后端路由或 schema
   - `app/api/routes_*.py`
   - `app/api/schemas.py`
   - 必要时更新 `app/core/models.py`
2. 更新后端测试
   - 优先补最近的 `tests/test_api_*.py`
3. 重新导出 OpenAPI 并生成前端类型

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
make contract-sync
```

4. 更新前端 API wrapper
   - `frontend/src/api/*.ts`
5. 更新前端手写补充类型
   - `frontend/src/api/types.ts`
6. 更新页面或组件
   - `frontend/src/pages/*`
   - `frontend/src/components/*`

## 当前接口到前端页面的映射

- `/scenarios/catalog`
  - 后端：`app/api/routes_scenarios.py`
  - 前端 wrapper：`frontend/src/api/scenarios.ts`
  - 主要页面：`frontend/src/pages/scenario-sets/ScenarioSetsPage.tsx`
- `/scenarios/launch`
  - 后端：`app/api/routes_scenarios.py`
  - 前端 wrapper：`frontend/src/api/scenarios.ts`
  - 主要页面：`frontend/src/pages/scenario-sets/ScenarioSetsPage.tsx`
- `/runs`、`/runs/{run_id}`、`/runs/{run_id}/events`
  - 后端：`app/api/routes_runs.py`
  - 前端 wrapper：`frontend/src/api/runs.ts`
  - 主要页面：`frontend/src/pages/executions/ExecutionsPage.tsx`、`frontend/src/pages/executions/ExecutionDetailPage.tsx`
- `/runs/{run_id}/environment`
  - 后端：`app/api/routes_runs.py`
  - 前端 wrapper：`frontend/src/api/runs.ts`
  - 主要页面：`frontend/src/pages/executions/ExecutionDetailPage.tsx`
- `/runs/{run_id}/sensor-capture/start`、`/runs/{run_id}/sensor-capture/stop`
  - 后端：`app/api/routes_runs.py`
  - 前端 wrapper：`frontend/src/api/runs.ts`
  - 主要页面：`frontend/src/pages/executions/ExecutionDetailPage.tsx`

## 必跑校验

后端：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
make lint
pytest -q
```

前端：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform/frontend
npm run check-types
npm run build
```

## 当前接口维护重点

### 1. 场景启动

- `GET /scenarios/catalog`
- `POST /scenarios/launch`

维护要点：

- `descriptor_template`
- `parameter_schema`
- `launch_capabilities`
- `scenario_source`

这些字段一旦变化，前端 `ScenarioSetsPage` 会直接受影响。

### 2. 运行时控制

- `GET /runs/{run_id}/environment`
- `POST /runs/{run_id}/environment`
- `POST /runs/{run_id}/sensor-capture/start`
- `POST /runs/{run_id}/sensor-capture/stop`

当前约定：

- `runtime_control.weather` 和 `runtime_control.debug` 主要给 native run 用
- `runtime_control.sensor_capture` 用来展示真实传感器采集状态
- `runtime_control.recorder` 用来展示 CARLA recorder 的状态

当前限制：

- `POST /runs/{run_id}/sensor-capture/start`
- `POST /runs/{run_id}/sensor-capture/stop`

这两个接口当前仍保留在契约里，但平台默认 native runtime 暂不开放“运行中手动开始 / 停止平台侧采集”。

- native run 会返回 `runtime_control.sensor_capture` 状态字段，便于页面展示
- 但 native run 暂不支持运行中手动开始 / 停止平台侧采集
- native run 目前只支持在 descriptor 里通过 `sensors.auto_start=true` 走自动采集

前端执行详情页依赖这些状态字段：

- `enabled`
- `auto_start`
- `desired_state`
- `active`
- `status`
- `output_root` / `output_path`
- `last_error`

### 3. 运行详情

- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/events`
- `GET /runs/{run_id}/viewer`
- `GET /runs/{run_id}/viewer/frame`

维护要点：

- `RunRecord.sensors.auto_start`
- `RunRecord.recorder.enabled`
- `RunEvent` 中的 `SIMULATION_RECORDER_*` / `SENSOR_RECORDING_*`
- `RunPayload.achieved_tick_rate_hz`

其中 `achieved_tick_rate_hz` 是当前观察 native runtime 实际执行速率的关键字段，远端联调和演示帧率对比时优先看它。

## 生成物位置

- OpenAPI JSON：
  - `contracts/openapi.json`
- 生成的前端 OpenAPI 类型：
  - `frontend/src/api/generated/openapi.ts`
- 前端补充收窄类型：
  - `frontend/src/api/types.ts`

## 契约改动后的发布顺序

1. `make contract-sync`
2. `make lint`
3. `pytest -q`
4. `cd frontend && npm run check-types`
5. `cd frontend && npm run build`
6. `REMOTE_PASSWORD='***' bash scripts/remote_deploy.sh --smoke-mode basic`
7. 如果改动涉及场景启动、运行时控制或采集链路，再跑：
   - `REMOTE_PASSWORD='***' bash scripts/remote_deploy.sh --smoke-mode scenario`
   - 或 `REMOTE_PASSWORD='***' bash scripts/remote_deploy.sh --smoke-mode capture`

## 常见错误

- 只改了 `schemas.py`，没有跑 `make contract-sync`
- 后端新增字段后，忘了更新 `frontend/src/api/types.ts`
- 页面直接依赖临时字段，没有经过 `frontend/src/api/*.ts`
- 路由响应结构变了，但 `tests/test_api_*.py` 没跟着改
- 只验证本地后端，没验证 `/ui` 页面真实状态

## 当前建议

- 任何接口改动都把 `make contract-sync` 当成默认步骤，而不是可选步骤。
- 远端联调前，先在本机把 `make lint`、`pytest -q`、`npm run check-types`、`npm run build` 跑通。
- 执行详情页相关改动，除了看接口 JSON，还要看 `/ui/executions/{run_id}` 页面实际状态有没有同步。
