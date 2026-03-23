# 场景模板与运行请求设计

## 当前状态

这份文档最初写于“官方 ScenarioRunner 仍是唯一执行主链”的阶段，下面不少段落保留了当时的设计背景。

截至当前版本，active path 已经调整为：

- 官方 `.xosc` 继续作为输入格式保留
- 平台模板场景走 `native_descriptor`
- 官方 `.xosc` 场景走 `openscenario`
- 两类请求最终都由平台自己的 native runtime 执行
- OpenSCENARIO 当前只保证平台受控子集，不承诺完整覆盖所有标准语义

阅读下面内容时，如果看到“ScenarioRunner 唯一主链”之类的表述，应把它理解为历史设计背景，而不是现行实现。

## 当前落地口径

截至当前仓库版本，Web 默认暴露的内置模板有这些约束：

- 只暴露平台内置 `native_descriptor` 模板和少量保留的输入格式模板
- 默认可见的巡航类模板都由平台 native runtime + Traffic Manager 自动驾驶控制 hero
- 当前实机确认可用并已收口到目录里的模板地图为：
  - `Town01`
  - `Town02`
  - `Town03`
  - `Town04`
  - `Town05`
  - `Town10HD_Opt`
- `Town06`、`Town07` 这类当前远端环境不存在的模板地图不应继续暴露到演示目录里

如果文档后续还出现“模板目录可以随意换到任意 Town 地图”的描述，应按上面的实机可用地图约束理解当前行为。

## 背景

当前平台已经支持通过 `GET /scenarios/catalog` 展示可运行场景，并通过 `POST /scenarios/launch` 生成 per-run 的 `scenario_launch_spec.json` 与 `generated_scenario.xosc`。

现阶段的主要限制有两类：

1. 前端虽然已经只暴露“场景、地图、天气、背景车/人、超时”这些业务维度，但场景能力边界还不够明确。
2. 后端当前主要围绕官方 OpenSCENARIO 样例工作，后续如果引入 Python Scenario，自定义模板还缺少稳定的抽象层。

这份文档把下一阶段的目标定成“统一场景模板层”。前端永远只选择“跑什么场景”，底层到底通过 native descriptor 还是 OpenSCENARIO 启动，由后端和 executor 决定。

## 目标

- 前端只暴露业务配置，不暴露底层 runtime 细节。
- 每次运行都先落一份稳定的 canonical run spec，再生成 per-run 的执行文件。
- 每个场景模板都声明自己的能力边界，避免“任意场景都能任意换图、任意改参数”的误导。
- 保持“模板层统一、执行后端隐藏”这条边界。

## 非目标

- 不接入 `--route` 模式。
- 不把“后台如何启动”做成前端选项。
- 不要求所有场景都改成 OpenSCENARIO。
- 不在这一步引入新的前端状态管理分叉。

## 用户侧心智模型

用户在“场景启动台”只需要理解一条规则：

- 选择测试地图
- 选择场景剧本
- 选择天气
- 选择背景车辆数
- 选择背景行人数
- 按场景模板需要填写少量剧本参数
- 启动运行

用户不需要知道：

- 底层最终是 native descriptor 还是受控子集 OpenSCENARIO 翻译
- 是否生成了中间 `.xosc`
- 背景交通是通过脚本启动还是通过 CARLA API 注入

## 核心原则

### 1. 模板优先，不以前端暴露执行模式

前端展示的是“场景模板”，不是“OpenSCENARIO 文件”或“Python 类”。

后端模板层至少需要隐藏这几个实现差异：

- `launch_mode = native_descriptor`
- `launch_mode = openscenario`
- `generated_artifacts = [json, xosc, logs]`

### 2. canonical run spec 才是真源

每次点击启动时，先持久化一份与执行方式无关的 run spec。建议继续放在：

```text
run_data/scenario_builds/<run_id>/scenario_launch_spec.json
```

再由后端或 executor 派生出真正的执行输入，例如：

```text
run_data/scenario_builds/<run_id>/generated_scenario.xosc
```

这样后续即使某个模板从 OpenSCENARIO 切到 Python Scenario，前端和上层 API 也不用改。

### 3. 模板必须声明能力边界

不是所有场景都应该允许任意切图、任意改天气或无限放大背景车流。

模板至少要声明：

- 支持的地图范围
- 是否允许切天气
- 是否允许改背景车/人数量
- 允许的参数区间
- 默认超时

### 4. 背景交通是外层扰动，不是剧本主逻辑

主剧情 actor、触发条件和测试标准应由模板控制。

背景交通只负责：

- 提供噪声
- 提升场景密度
- 形成更接近真实路况的扰动

因此背景交通需要记录：

- `num_vehicles`
- `num_walkers`
- `seed`
- 具体注入方式

## 推荐的数据结构

### 模板目录项

建议把 `GET /scenarios/catalog` 逐步扩展成“模板目录”。

示例：

```json
{
  "scenario_id": "ped_occluded_crossing_v1",
  "display_name": "行人鬼探头",
  "description": "遮挡后突然进入 ego 前方冲突区的横穿行人场景。",
  "category": "pedestrian",
  "default_map_name": "Town03",
  "map_policy": "whitelist",
  "supported_maps": ["Town03", "Town05"],
  "launch_capabilities": {
    "map_editable": true,
    "weather_editable": true,
    "traffic_vehicle_count_editable": true,
    "traffic_walker_count_editable": true,
    "timeout_editable": true,
    "max_vehicle_count": 24,
    "max_walker_count": 24
  },
  "parameter_schema": [
    {
      "field": "trigger_distance_m",
      "label": "触发距离",
      "type": "number",
      "min": 8,
      "max": 40,
      "default": 18,
      "unit": "m"
    },
    {
      "field": "adversary_speed_mps",
      "label": "行人速度",
      "type": "number",
      "min": 0.8,
      "max": 3.0,
      "default": 1.6,
      "unit": "m/s"
    },
    {
      "field": "occluder_type",
      "label": "遮挡体",
      "type": "enum",
      "options": ["van", "suv", "static_barrier"],
      "default": "van"
    }
  ]
}
```

说明：

- `scenario_id` 是用户和接口看到的稳定模板 ID。
- `parameter_schema` 只描述用户可调字段，不泄露底层执行模式。
- `map_policy` 建议至少支持 `fixed` 和 `whitelist`。

### 启动请求

建议继续让前端提交统一请求，而不是提交 `.xosc` 或 Python 类名。

```json
{
  "scenario_id": "ped_occluded_crossing_v1",
  "map_name": "Town03",
  "weather": {
    "preset": "ClearNoon"
  },
  "traffic": {
    "num_vehicles": 8,
    "num_walkers": 12,
    "seed": 42
  },
  "timeout_seconds": 60,
  "template_params": {
    "trigger_distance_m": 18,
    "adversary_speed_mps": 1.6,
    "occluder_type": "van"
  },
  "auto_start": true
}
```

### canonical run spec

建议继续由后端在每次 launch 时写入：

```json
{
  "scenario_id": "ped_occluded_crossing_v1",
  "display_name": "行人鬼探头",
  "map_name": "Town03",
  "weather": {
    "preset": "ClearNoon"
  },
  "traffic": {
    "num_vehicles": 8,
    "num_walkers": 12,
    "seed": 42,
    "injection_mode": "carla_api"
  },
  "timeout_seconds": 60,
  "template_params": {
    "trigger_distance_m": 18,
    "adversary_speed_mps": 1.6,
    "occluder_type": "van"
  },
  "execution_plan": {
    "backend_kind": "python",
    "entrypoint": "srunner.scenarios.ped_occluded_crossing.PedOccludedCrossing",
    "generated_artifacts": [
      "run_data/scenario_builds/<run_id>/scenario_launch_spec.json"
    ]
  }
}
```

`execution_plan` 只在服务端内部消费，不需要前端使用。

## 后端分层建议

### 1. 模板注册层

建议新增一层“场景模板注册表”，负责输出：

- 模板目录
- 可配参数 schema
- 默认值
- 地图支持范围
- 后端绑定信息

可以理解成当前 `app/scenario/library.py` 的升级版，但不再只等价于“官方 OpenSCENARIO 样例列表”。

### 2. launch builder

`launch_builder` 继续负责：

- 校验用户请求
- 合并模板默认值
- 生成 canonical run spec
- 生成 per-run 执行产物

但它不应该把 OpenSCENARIO 当成唯一出口。

理想输出是：

- `scenario_launch_spec.json`
- 按需生成的 `.xosc`、`.json` 或 `.yaml`

### 3. executor

当前 active path 下，executor 的职责已经收敛为：

- 按 `execution_plan` 启动平台 native runtime
- 在 native runtime 内完成地图加载、参与者生成、TM autopilot、事件触发与清理
- 管理运行期间的背景交通、recorder、HIL sidecar 与 heartbeat

推荐时序：

1. 解析 canonical run spec，决定 `native_descriptor` 还是 `openscenario`
2. 连接 CARLA，加载地图和天气
3. 生成 hero / scenario actors
4. 启动 TM autopilot 和背景交通
5. 进入 native runtime tick loop，持续写 heartbeat
6. 停止 recorder / HIL sidecar，回收 actor 和临时资源

如果后续仍保留官方 ScenarioRunner，也应只作为严格语义验证或重场景回归链路，而不是默认演示执行主链。

## 关于 `generate_traffic.py` 的建议

可以保留它作为可选实现，但不建议把它立刻定成唯一方案。

原因：

- `--reloadWorld` 可能让先启动的交通脚本失效
- 需要单独管理 PID、日志与失败清理
- 远端环境里脚本路径、Python 环境和宿主名解析仍需要标准化

更稳的策略是定义统一的 `background_traffic_adapter` 抽象：

- `carla_api`
- `generate_traffic_script`

首阶段优先把 `carla_api` 跑稳，`generate_traffic.py` 作为后续可切换实现。

## UI 建议

“场景启动台”建议固定成两层：

### 顶层固定字段

- 场景模板
- 测试地图
- 天气预设
- 背景车辆数
- 背景行人数
- 超时

### 模板扩展字段

按 `parameter_schema` 动态渲染：

- 数值输入
- 枚举下拉
- 布尔开关

前端不显示：

- `backend_kind`
- `.xosc` 路径
- Python 场景类名

## 首批推荐模板

### 1. 跟车急刹

- `scenario_id`: `lead_vehicle_brake_v1`
- 推荐底层：`openscenario`
- 适用原因：结构简单，适合保留为受控子集 OpenSCENARIO 输入
- 默认地图：`Town01`
- 关键参数：
  - `lead_vehicle_initial_gap_m`
  - `lead_vehicle_brake_decel_mps2`
  - `ego_initial_speed_mps`

### 2. 行人鬼探头

- `scenario_id`: `ped_occluded_crossing_v1`
- 推荐底层：`native_descriptor`
- 适用原因：遮挡、触发条件和判定逻辑更适合直接落到平台 native runtime
- 默认地图：`Town03`
- 关键参数：
  - `trigger_distance_m`
  - `adversary_speed_mps`
  - `occluder_type`
  - `crossing_offset_m`

### 3. 对向闯红灯

- `scenario_id`: `oncoming_red_light_violation_v1`
- 推荐底层：`native_descriptor`
- 适用原因：信号状态、路口冲突判定和时间窗控制更适合平台原生执行图
- 默认地图：`Town05`
- 关键参数：
  - `violator_entry_delay_s`
  - `violator_speed_mps`
  - `ego_target_speed_mps`

### 4. 邻车 cut-in

- `scenario_id`: `adjacent_vehicle_cut_in_v1`
- 推荐底层：`native_descriptor`
- 适用原因：相对速度、插入间隙与触发阈值更适合平台原生行为编排
- 默认地图：`Town04`
- 关键参数：
  - `cut_in_side`
  - `cut_in_gap_m`
  - `cut_in_speed_delta_mps`

### 5. 无保护左转

- `scenario_id`: `unprotected_left_turn_v1`
- 推荐底层：`native_descriptor`
- 适用原因：冲突区、优先级和通过判定复杂
- 默认地图：`Town05`
- 关键参数：
  - `oncoming_vehicle_speed_mps`
  - `ego_wait_timeout_s`
  - `gap_acceptance_m`

## 标杆模板建议：行人鬼探头

建议把“行人鬼探头”做成首个标杆模板，因为它最能体现“业务模板层”和“底层执行模式解耦”的价值。

推荐默认值：

```yaml
template_id: ped_occluded_crossing_v1
display_name: 行人鬼探头
category: pedestrian
default_map_name: Town03
map_policy: whitelist
supported_maps:
  - Town03
  - Town05
defaults:
  weather_preset: ClearNoon
  timeout_seconds: 60
  num_vehicles: 8
  num_walkers: 12
  seed: 42
tunables:
  trigger_distance_m:
    type: number
    min: 8
    max: 40
    default: 18
  adversary_speed_mps:
    type: number
    min: 0.8
    max: 3.0
    default: 1.6
  occluder_type:
    type: enum
    values: [van, suv, static_barrier]
    default: van
  crossing_offset_m:
    type: number
    min: -2
    max: 2
    default: 0
criteria:
  - collision_free
  - stop_before_conflict_zone
  - timeout
```

## 建议执行顺序

### 第一阶段

- 引入模板注册层
- 扩展 `/scenarios/catalog` 返回 `parameter_schema`
- 扩展 `/scenarios/launch` 支持 `template_params`
- 保持当前主要通过 OpenSCENARIO 生成的链路不破

### 第二阶段

- 新增首个 Python Scenario 模板
- 把“行人鬼探头”接成标杆案例
- 为 Python 场景补生成式 run spec 和验参与日志

### 第三阶段

- 把背景交通注入方式抽象成 adapter
- 稳定 `carla_api`
- 再决定是否把 `generate_traffic.py` 变成可切换实现

## 当前结论

平台后续最合适的方向不是“让前端选择 Python 还是 OpenSCENARIO”，而是“让前端只选择场景模板，由后端隐藏执行模式”。

对业务来说，真正稳定的接口应该是：

- 一个稳定的场景模板目录
- 一个稳定的场景启动请求
- 一份可复现的 canonical run spec

这三层一旦稳定，后续接入 Python Scenario、自定义 XOSC、更多模板参数和背景交通实现时，都不会再反复推翻前后端接口。
