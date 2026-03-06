# 设计说明（修正型迭代）

## 1. 为什么 API 层与 executor 层分离

本项目保持“控制平面 / 执行平面”分离：

- API 层职责：参数校验、run 创建、状态查询、控制命令下发
- executor 职责：连接 CARLA、地图加载、同步模式配置、tick 推进、资源清理

这样做的工程收益：
- Web 请求线程不会直接持有 CARLA world 对象
- 避免 API handler 变成长时间阻塞执行器
- 生命周期逻辑集中在 executor，异常恢复更清晰
- 为后续扩展（例如 HIL gateway 适配）保留稳定边界

## 2. 为什么 synchronous mode 只能有一个控制方

在 CARLA synchronous mode 下，`world.tick()` 的调用方就是仿真时钟所有者。

若出现多方同时 tick：
- 仿真时间推进权冲突
- 传感器时间戳和 actor 行为非确定
- stop/cancel 语义可能竞争
- 结果不可复现，排障难度显著上升

当前约束：
- tick 控制权只在 executor
- API 不直接操作 CARLA world
- 同步参数设置集中在 `SimController`

## 3. 当前版本与 HIL 的关系

当前版本是“场景仿真控制层 MVP”，**未接入 HIL 数据链路**。

明确未做：
- 树莓派网关
- USB 摄像头模拟
- DUT 实时注入
- HIL 时钟同步

但结构上保留扩展点：
- `app/executor/sim_controller.py`：生命周期主控点，可挂接 injector/hil client
- `app/executor/telemetry.py`：可扩展为统一遥测出口
- `app/executor/recorder.py`：可扩展记录与索引能力
- `app/orchestrator/run_manager.py`：可保持 API 契约稳定

## 4. ScenarioRunner / Leaderboard 当前状态

当前系统并不是完整 ScenarioRunner 编排系统：
- 现阶段通过自定义最小 executor 运行内置场景
- ScenarioRunner / Leaderboard 尚未形成完整调用链与评测闭环
- 相关依赖/目录仅作为后续集成前置条件

结论：
- 现在可用于“仿真控制层 MVP”验证
- 不应宣称为“完整 ScenarioRunner/Leaderboard 运行平台”

## 5. 已知限制与下一阶段建议

已知限制：
- 仅最小 Web 控制台，未实现复杂前端
- 事件查询采用轮询
- `PAUSED` 状态仅预留接口，未完整实现
- 运行存储是文件型，不适合高并发多实例

下一阶段建议：
1. 增加 executor 插件接口（HIL I/O 适配器）
2. 扩展 descriptor（可选 `hil` 区段）
3. 增加 ScenarioRunner/OpenSCENARIO 适配层（保持现有 run API 不变）
4. 增加 run watchdog/heartbeat 与超时恢复
5. 增强指标与日志采集（如 OTLP/Prometheus）
