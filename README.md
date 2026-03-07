# CARLA 场景仿真控制层 MVP（0.9.16）

本项目是面向 **CARLA 0.9.16** 的“场景仿真控制层 MVP”。

定位：
- 打通仿真控制与任务编排闭环
- 保持 API 层与 executor 层分离
- 保证 synchronous mode 下只有一个 tick 控制方
- 为后续 Web 扩展与 HIL 扩展保留清晰边界

## 当前已实现

- run 生命周期管理（创建/启动/停止/取消/查询）
- run state machine（CREATED/QUEUED/STARTING/RUNNING/PAUSED/STOPPING/COMPLETED/FAILED/CANCELED）
- descriptor 场景配置（YAML/Pydantic 校验）
- executor 控制 CARLA 生命周期（连接、加载地图、同步参数、tick 推进、资源清理）
- 每个 run 的 artifact 输出（`config_snapshot.json`、`status.json`、`metrics.json`、`events.jsonl`、`run.log`）
- 极简中文 Web 控制台（`/` 或 `/ui`）
- Swagger 调试页（`/docs`）
- `debug.viewer_friendly` 调试友好模式（可选）

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

## 时间语义（重点）

- `started_at_utc` / `ended_at_utc`：系统 UTC 时间（控制层时间）
- `sim_time`：CARLA 仿真时间（由 world tick 推进）
- `wall_elapsed_seconds`：墙钟耗时（本机真实运行时间）
- `timeout_seconds`：**按仿真时间**判定，不等于墙钟运行时长

说明：
- 正式模式下 executor 会尽快推进仿真，run 可能在墙钟上很快结束
- 如果你需要人工观察（例如 pygame viewer），建议启用 `debug.viewer_friendly=true` 或提高 timeout

## 项目结构

```text
carla_web_platform/
  app/
    api/
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

## 本地 Miniconda3 环境（macOS / Apple Silicon）

适用目标：
- 本地开发 Web 控制台、API、配置校验与测试
- 远端 CARLA server 联调前的控制面验证

创建环境：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
conda env create -f environment.web.yml
conda activate duckpark-carla-web
```

准备本地配置：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
cp .env.local.example .env.local
```

说明：
- `.env.local` 会在 `scripts/start_platform.sh` 启动时自动加载
- 默认已预填 `CARLA_HOST=192.168.110.151`
- 如只需启动 Web/API 界面，可将 `START_EXECUTOR=false`

平台边界：
- 当前仓库代码目标版本为 `CARLA 0.9.16`
- 官方 `0.9.16` package 安装文档主要面向 `Ubuntu` / `Windows`
- 在 `macOS Apple Silicon` 上，本项目已验证可运行 Web/API 与测试；完整 executor 更建议运行在带匹配 `carla` Python API 的 Ubuntu 节点或容器中

远端联调前检查：

```bash
nc -G 2 -vz 192.168.110.151 2000
nc -G 2 -vz 192.168.110.151 8010
```

若超时，通常表示：
- CARLA server 未启动
- Traffic Manager 未启动
- 主机防火墙或交换网络未放通端口

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
bash scripts/start_platform.sh --carla-host 127.0.0.1 --carla-port 2000 --traffic-manager-port 8010
```

本地 conda 运行示例：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
conda run -n duckpark-carla-web bash scripts/start_platform.sh --carla-host 192.168.110.151 --carla-port 2000 --traffic-manager-port 8010
```

只启动 Web/API：

```bash
bash scripts/start_platform.sh --carla-host 127.0.0.1 --carla-port 2000 --traffic-manager-port 8010 --no-executor
```

## 最小验证流程

1. 打开 `http://127.0.0.1:8000/`，进入中文控制台
2. 在“创建运行”中选择场景，设置 `map_name`、`timeout_seconds`、`fixed_delta_seconds`
3. 如需便于观察勾选 `debug.viewer_friendly`
4. 点击“创建运行”
5. 在“运行列表”点击“启动”
6. 观察状态变化（QUEUED -> STARTING -> RUNNING -> COMPLETED/FAILED）
7. 点击“查看事件”检查事件流
8. 到 artifact 目录查看结果

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

## 无头模式下如何确认场景在执行

`/docs` 和最小 Web 控制台展示的是控制面/状态面，不是实时 3D 画面。可通过以下方式确认场景执行：

1. run 状态流转是否正常（CREATED -> QUEUED -> STARTING -> RUNNING -> COMPLETED/FAILED）
2. `events.jsonl` 是否持续写入（如 `RUN_STARTING`、`WORLD_SYNC_ENABLED`、`SCENARIO_STARTED`）
3. `metrics.json` 是否更新 `sim_time` / `current_tick` / `wall_time`
4. 使用 pygame `ego_viewer.py` 观察 ego 视角

viewer 局限：
- 仅用于本地调试观察，不参与控制
- 不调用 tick，不影响单一 tick 控制权
- 场景切图/重载 world 时需自动重绑（脚本已支持）

## pygame ego viewer（本地观察工具）

脚本路径：`/ros2_ws/src/scripts/ego_viewer.py`

运行示例：

```bash
python3 /ros2_ws/src/scripts/ego_viewer.py --host 127.0.0.1 --port 2000
```

你会在终端看到：
- 当前 map
- 当前 vehicle 总数
- role_name 摘要
- world/map 是否切换
- 命中 ego 后的 id/role_name/位置/速度

## 调试友好模式示例

示例文件：`configs/scenarios/sample_empty_drive_viewer_friendly.yaml`

核心字段：

```yaml
debug:
  viewer_friendly: true
```

开启后 executor 会在每 tick 插入非常小的 sleep（默认逻辑仍是尽快推进仿真）。

## 接口概览

- `POST /runs`：创建 run
- `POST /runs/{run_id}/start`：启动 run
- `POST /runs/{run_id}/stop`：停止 run
- `POST /runs/{run_id}/cancel`：取消 run
- `GET /runs/{run_id}`：查询 run（含 UTC 时间 + sim/wall 指标字段）
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
