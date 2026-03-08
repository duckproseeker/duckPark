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
  scripts/                # 启动与运维脚本
  docker/                 # Docker 构建与 compose
  tests/                  # 后端 API 与行为测试
```

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
