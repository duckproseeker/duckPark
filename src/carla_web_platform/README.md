# CARLA 芯片测评平台

本项目是一个基于 **CARLA 0.9.16** 的芯片测评平台，用于给算法工程师和测试工程师提供统一的场景仿真、批量执行、设备接入、指标回传和报告导出能力。

当前版本已经不再是“最小控制台 MVP”，而是围绕下面的业务链路组织：

`所属项目 -> 基准任务 -> 场景矩阵 -> 设备绑定 / DUT 登记 -> benchmark task -> 多个 runs -> 指标汇总 -> 报告导出`

## 当前能力

- 后端一等模型：
  - `projects`
  - `benchmark-definitions`
  - `benchmark-tasks`
  - `reports`
  - `runs`
- 前端主导航：
  - `项目`
  - `基准任务`
  - `场景集`
  - `执行中心`
  - `报告中心`
  - `设备中心`
- 批量测评任务创建：
  - 一个 `benchmark task` 可展开为多个 `run`
  - 同时支持多场景、多地图、多天气、多传感器组合
- 地图归一化：
  - UI 把 `TownXX` 与 `TownXX_Opt` 视为同一张地图
  - 后端统一优先使用优化后的 `TownXX_Opt`
- 报告导出：
  - 当前支持 `JSON` 和 `Markdown`
- DUT 录入规则：
  - DUT 型号不在首页和项目页写死
  - 由测试人员在创建任务时录入
  - 任务与报告会显式带出 DUT 型号
- 场景运行时：
  - 默认执行链已经切到平台 `native runtime`
  - 官方 `.xosc` 现在作为输入格式进入平台受控子集解析，而不是直接交给 `scenario_runner.py`
  - 当前受控子集重点覆盖地图、天气、参与者生成、时间/距离触发、`ChangeAutoPilot` 和简单 `KeepVelocity`
  - 不承诺完整覆盖全部 OpenSCENARIO 语义
- 内置演示模板：
  - 当前 Web 默认暴露的内置模板都走平台 `native runtime`
  - `Town01`、`Town02`、`Town03`、`Town04`、`Town05`、`Town10HD_Opt` 是当前实机确认可用的模板地图
  - `town10_autonomous_demo` 与其余内置巡航模板都由平台内置 Traffic Manager 自动驾驶控制 hero
- 设备中心观测链：
  - Jetson 指标回传到 Pi `dut_result_receiver` 之后，还需要 Pi `gateway_agent` 持续 heartbeat 到平台
  - `设备中心 / 单 DUT 运行观测` 页面依赖这条 heartbeat 才会被判定为在线实时观测，而不只是旧快照

## 技术栈

- 前端：`React 19` + `TypeScript` + `Vite` + `React Router` + `TanStack Query` + `TailwindCSS`
- 后端：`FastAPI` + `Pydantic v2`
- 测试：`pytest`
- 代码质量：`ruff` + `black` + `isort`
- 运行方式：Docker 或本地 Python/Conda

## 目录结构

```text
carla_web_platform/
  app/
    api/                  # FastAPI 路由与响应封装
    core/                 # 配置、模型、错误定义
    executor/             # CARLA 执行器
    orchestrator/         # run manager / command queue
    platform/             # project / benchmark / report 业务服务
    scenario/             # 场景目录、地图归一化、天气与传感器模板
    storage/              # 文件型持久化
  frontend/
    src/
      api/                # REST client
      components/         # 公共 UI 组件
      pages/              # 页面级功能
      lib/                # 指标与格式化辅助
  configs/                # 场景、传感器等配置
  scripts/                # 平台本身的启动、契约导出、远端部署脚本
  docker/                 # Docker 构建与 compose
  tests/                  # 后端 API 与行为测试
../hil_runtime/           # sibling: Host / Pi / Jetson 的运行时脚本、systemd 模板、链路文档
```

## HIL 运行资产分层

为避免继续把 Host / Pi / Jetson 的部署脚本都堆在 `carla_web_platform/` 下面，当前约定如下：

- `carla_web_platform/`
  - 只保留平台产品代码、平台自身启动脚本、API 契约导出和远端平台部署脚本
- `../hil_runtime/host/`
  - 主机侧 CARLA headed 启动、前视预览与 HDMI 演示入口
- `../hil_runtime/pi/`
  - 树莓派 HDMI 注入、UVC gadget、gateway agent、systemd 模板和示例环境变量
- `../hil_runtime/jetson/`
  - Jetson detector 启动脚本、metrics 上报、C++ detector 源码
- `../hil_runtime/docs/`
  - Pi -> Jetson 链路、真机排障与演示记录

## 关键数据模型

### Project

项目不等于芯片型号。它表示一个测评业务容器，例如：

- `基线验证项目`
- `矩阵回归项目`
- `热稳压测项目`

### Benchmark Definition

定义“测什么”，包括：

- 关注指标
- 执行节奏
- 报告形态
- 默认评测协议

### Benchmark Task

一次实际创建的测评任务，包含：

- 所属项目
- DUT 型号
- 场景矩阵
- 设备绑定信息
- 评测协议
- 自动启动开关
- 展开的多个 `run_ids`

### Report

由 `benchmark task` 导出的报告资产，当前落地为：

- `report.json`
- `report.md`

## 关键接口

### 项目与模板

- `GET /projects`
- `GET /benchmark-definitions`

### 场景模板与场景启动

- `GET /scenarios/catalog`
- `POST /scenarios/launch`

当前约定：

- 平台模板场景走 `native_descriptor`
- 官方 `.xosc` 场景走 `openscenario`
- 两者最终都由平台 executor 内的 native runtime 执行
- 当前默认可见的内置模板为 9 个：
  - `town10_autonomous_demo`
  - `town01_urban_loop`
  - `town02_suburb_cruise`
  - `town03_intersection_sweep`
  - `town03_rush_hour`
  - `town04_night_cruise`
  - `town05_rainy_commute`
  - `town10_dense_flow`
  - `free_drive_sensor_collection`

设计说明见：

- `docs/scenario-template-design.md`
- `docs/host-bringup.md`
- `docs/api-contract-maintenance.md`
- `../hil_runtime/docs/pi_jetson_rtp_pipeline.md`

### 测评任务

- `GET /benchmark-tasks`
- `GET /benchmark-tasks/{benchmark_task_id}`
- `POST /benchmark-tasks`

请求示例：

```json
{
  "project_id": "baseline-validation",
  "benchmark_definition_id": "perception-baseline",
  "dut_model": "演示开发板",
  "scenario_matrix": [
    {
      "scenario_id": "empty_drive",
      "map_name": "Town01",
      "environment_preset_id": "clear_day",
      "sensor_profile_name": "front_rgb"
    }
  ],
  "hil_config": {
    "mode": "camera_open_loop",
    "gateway_id": "pi-gateway-01",
    "video_source": "hdmi_x1301",
    "dut_input_mode": "uvc_camera",
    "result_ingest_mode": "http_push"
  },
  "evaluation_profile_name": "yolo_open_loop_v1",
  "auto_start": false
}
```

### 运行与报告

- `GET /runs`
- `POST /runs/{run_id}/start`
- `POST /runs/{run_id}/stop`
- `POST /runs/{run_id}/cancel`
- `GET /reports`
- `POST /reports/export`
- `GET /reports/{report_id}/download?format=json`
- `GET /reports/{report_id}/download?format=markdown`

## 本地开发

### Python 环境

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
conda env create -f environment.web.yml
conda activate duckpark-carla-web
```

### 启动后端

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
bash scripts/start_platform.sh --carla-host 127.0.0.1 --carla-port 2000 --traffic-manager-port 8010
```

只启动 Web/API、不启动 executor：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
bash scripts/start_platform.sh --api-host 0.0.0.0 --api-port 8000 --no-executor --carla-host 127.0.0.1
```

### 启动前端开发服务器

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform/frontend
npm install
npm run dev -- --host 0.0.0.0
```

如果仍然采用一体化部署，则后端会直接托管 `frontend/dist` 到 `/ui`。

## Docker 启动

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
docker compose -f docker/docker-compose.yml up -d --build
```

默认入口：

- 平台 UI：`http://127.0.0.1:8000/ui`
- Swagger：`http://127.0.0.1:8000/docs`

## 远端部署

当前协作约束：

- 本机只负责改代码和跑本地验证
- 正式环境在 `192.168.110.151`
- 主开发容器是 `ros2-dev`
- CARLA server 在另一个容器里，通常通过 `~/startCarla.sh` 启动
- 远端 smoke 现在默认验证平台 native runtime，而不是 ScenarioRunner 主链

远端运维说明见：

- `docs/remote-ops.md`
- `docs/host-bringup.md`

注意：

- 这里统一使用 `remote_git_sync.sh`
- `src/hil_runtime/` 下的 host / Pi / Jetson 运行资产需要按目标机器单独同步
- 如果要把主机上的 Web、headed CARLA、native follow 显示链一起拉起来，直接看 `docs/host-bringup.md`

常用命令：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
REMOTE_PASSWORD='***' bash scripts/remote_git_sync.sh deploy
REMOTE_PASSWORD='***' bash scripts/remote_git_sync.sh rollback
```

Makefile 包装：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
make remote-sync
make remote-rollback
```

## 常用命令

### 后端

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
make test
make lint
make format
```

### 前端

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform/frontend
npm run check-types
npm run build
```

### 契约同步

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
make contract-sync
```

接口维护说明见：

- `docs/api-contract-maintenance.md`
- `docs/remote-ops.md`

## 最小联调流程

1. 启动平台后端和 executor。
2. 打开 `/ui/executions`。
3. 选择所属项目、基准任务模板。
4. 通过下拉多选选择场景、地图、天气和传感器模板。
5. 绑定设备并录入 DUT 型号。
6. 创建 benchmark task。
7. 在执行列表观察 `CREATED -> QUEUED -> RUNNING -> COMPLETED/FAILED`。
8. 在 `/ui/reports` 导出最新任务报告。

## 已知约束

- 前端开发态若与后端跨域分离运行，当前需要通过 Vite 代理或后端补充 CORS。
- 功耗、温度、mAP、延迟等指标依赖网关或评测侧真实回传；未接入时前端会显示“待接入”。
- 报告导出当前仅提供 `JSON` / `Markdown`，尚未提供 PDF。
- `make lint` 可能受仓库内既有 Ruff 存量问题影响，提交前应先区分新增问题与历史问题。
- CARLA recorder 当前状态链路已接通，但 recorder 文件落盘仍依赖 CARLA server 容器和 executor 容器之间的共享路径设计，不能只以“状态为 RUNNING”判断产物已经可用。
