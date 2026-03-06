# CARLA 场景仿真控制层 MVP（0.9.16）

本项目是面向 **CARLA 0.9.16** 的“场景仿真控制层 MVP”。

定位：
- 先打通仿真控制与任务编排闭环
- 保持 API 层与 executor 层分离
- 保证 synchronous mode 下只有一个 tick 控制方
- 为后续 Web 扩展与 HIL 扩展保留清晰边界

## 当前已实现

- run 生命周期管理（创建/启动/停止/取消/查询）
- run state machine（CREATED/QUEUED/STARTING/RUNNING/PAUSED/STOPPING/COMPLETED/FAILED/CANCELED）
- descriptor 驱动场景配置（YAML/Pydantic 校验）
- executor 统一控制 CARLA 生命周期：连接、加载地图、设置同步、推进 tick、清理资源
- 每个 run 的 artifact 输出（`config_snapshot.json`、`status.json`、`metrics.json`、`events.jsonl`、`run.log`）
- 极简中文 Web 控制台（`/` 或 `/ui`）
- Swagger 调试页（`/docs`）

## 当前未实现

- 树莓派网关与外设联动
- USB 摄像头模拟
- HIL 时间同步
- DUT 数据注入
- 在线实时大屏/复杂前端
- 分布式调度
- 完整 ScenarioRunner / Leaderboard 深度集成

## 关于 ScenarioRunner/Leaderboard 的真实状态

当前版本是**自定义最小 CARLA executor MVP**：
- 已实现基础场景编排与执行闭环
- **尚未**实现完整 ScenarioRunner 编排链路
- **尚未**实现 Leaderboard 评测流
- 相关目录仅作为后续适配扩展基础，不代表已深度接入

## 页面入口说明

- `/docs`：开发调试接口页（Swagger/OpenAPI），用于接口联调，不是正式控制台
- `/` 或 `/ui`：正式最小中文控制台（浏览器操作入口）

## 项目结构

```text
carla_web_platform/
  app/
    api/
      main.py
      routes_runs.py
      routes_scenarios.py
      routes_ui.py
      schemas.py
    core/
    orchestrator/
    executor/
    scenario/
    storage/
    templates/
      ui.html
    static/
      ui.js
      ui.css
  configs/scenarios/
  scripts/
  docker/
  tests/
  artifacts/
  run_data/
```

## 启动方式

### 1) 启动 carla-server

```bash
docker compose -f docker/docker-compose.yml up -d carla-server
```

### 2) 启动 sim-executor（内含 API + executor）

```bash
docker compose -f docker/docker-compose.yml up -d --build sim-executor
```

默认访问：
- 控制台：`http://127.0.0.1:8000/`
- Swagger：`http://127.0.0.1:8000/docs`

### 3) 本地直接运行（不走 Docker）

```bash
cd /ros2_ws/src/carla_web_platform
pip install -r requirements.txt
CARLA_HOST=127.0.0.1 CARLA_PORT=2000 TRAFFIC_MANAGER_PORT=8010 bash run_platform.sh
```

## 最小验证流程

1. 打开 `http://127.0.0.1:8000/`，进入中文控制台
2. 在“创建运行”中选择场景，设置 `map_name`、`timeout_seconds`、`fixed_delta_seconds`
3. 点击“创建运行”
4. 在“运行列表”点击“启动”
5. 观察状态变化（QUEUED -> STARTING -> RUNNING -> COMPLETED/FAILED）
6. 点击“查看事件”检查事件流
7. 到 artifact 目录查看结果

artifact 默认目录：

```text
artifacts/<run_id>/
  config_snapshot.json
  status.json
  metrics.json
  events.jsonl
  run.log
  recorder/
  outputs/
```

## 接口概览

- `POST /runs`：创建 run
- `POST /runs/{run_id}/start`：启动 run
- `POST /runs/{run_id}/stop`：停止 run
- `POST /runs/{run_id}/cancel`：取消 run
- `GET /runs/{run_id}`：查询 run
- `GET /runs`：查询列表
- `GET /runs/{run_id}/events`：查询事件
- `GET /scenarios`：查询内置场景与模板

## 测试

```bash
pytest -q
```

当前包含：
- run 状态机转移测试
- descriptor 校验测试
- API 创建/启动/停止流程测试
- executor 异常转 FAILED 测试
- artifact 目录生成测试
- UI 页面路由冒烟测试
