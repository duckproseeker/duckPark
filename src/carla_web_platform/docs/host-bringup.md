# 主机端部署与启动

## 适用范围

这份文档描述当前 DuckPark 演示链在 Ubuntu 主机上的推荐启动方式，目标是保持下面这条链路成立：

`CARLA headed 窗口 -> 主机 HDMI 输出 -> 树莓派 HDMI 采集 -> Jetson 推理 -> Web 平台观测与控制`

当前结论：

- Web/API 与 executor 由 `src/carla_web_platform/` 提供
- Host / Pi / Jetson 的运行时脚本由 sibling 目录 `src/hil_runtime/` 提供
- 平台默认执行链已经切到 `native runtime`
- `.xosc` 仍可作为输入格式导入，但不再由官方 `scenario_runner.py` 直接执行

## 已验证远端环境

- 主机地址：`192.168.110.151`
- 登录用户：`du`
- 主机源码根目录：`/home/du/ros2-humble/src`
- 平台目录：`/home/du/ros2-humble/src/carla_web_platform`
- HIL 运行时目录：`/home/du/ros2-humble/src/hil_runtime`
- 主开发容器：`ros2-dev`
- 容器内平台目录：`/ros2_ws/src/carla_web_platform`

重要约束：

- `scripts/remote_git_sync.sh` 负责把 `carla_web_platform/` 作为 Git checkout 同步到主机
- `hil_runtime/` 需要单独同步到主机
- headed CARLA 在物理主机上启动，不在 `ros2-dev` 容器里启动

## 目录准备

主机上建议保持下面的同级目录结构：

```text
/home/du/ros2-humble/src/
  carla_web_platform/
  hil_runtime/
```

如果本机已经有完整仓库，可以直接把 sibling 目录一并同步过去，例如：

```bash
rsync -av /path/to/duckPark/src/hil_runtime/ du@192.168.110.151:/home/du/ros2-humble/src/hil_runtime/
```

## 1. 启动平台 Web / API / executor

### 方式 A：直接用远端部署脚本更新正式环境

在本机执行：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
REMOTE_PASSWORD='***' bash scripts/remote_git_sync.sh deploy
```

这会在远端重启 API 和 executor，并校验：

- `/healthz`
- `/system/status`
- `/ui`

### 方式 B：在远端容器里手动启动

先登录主机：

```bash
ssh du@192.168.110.151
```

进入开发容器：

```bash
docker exec -it ros2-dev bash
```

在容器内启动平台：

```bash
cd /ros2_ws/src/carla_web_platform
bash scripts/start_platform.sh \
  --api-host 0.0.0.0 \
  --api-port 8000 \
  --carla-host 192.168.110.151 \
  --carla-port 2000 \
  --traffic-manager-port 8010
```

如果只想先看 Web/API，不想启动 executor：

```bash
cd /ros2_ws/src/carla_web_platform
bash scripts/start_platform.sh \
  --api-host 0.0.0.0 \
  --api-port 8000 \
  --no-executor \
  --carla-host 192.168.110.151 \
  --carla-port 2000 \
  --traffic-manager-port 8010
```

启动后检查：

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/system/status
```

## 2. 在主机上启动 headed CARLA

登录主机后，不进容器，直接在物理主机 shell 执行：

```bash
cd /home/du/ros2-humble/src
bash hil_runtime/host/scripts/start_carla_headed.sh
```

这个脚本会：

- 先确保主机 `HDMI-0` 真正被激活为 `DP-0` 的镜像输出，避免 Pi 只有 HPD 没有 TMDS
- 清掉冲突的旧 CARLA 容器
- 启动 `carla-headed`
- 等待 RPC 端口 ready
- 再用 `ros2-dev` 容器里的 `python3 + carla.Client(...)` 做一次真正的 world readiness 检查

常用检查：

```bash
docker ps | grep carla-headed
docker logs --tail 100 carla-headed
```

如果只想单独修主机 HDMI 镜像，可以先手动执行：

```bash
cd /home/du/ros2-humble/src
bash hil_runtime/host/scripts/ensure_host_hdmi_mirror.sh
```

看到 `xrandr --listmonitors` 里同时出现 `DP-0` 和 `HDMI-0`，Pi 侧才有机会拿到稳定 TMDS/sync。

如果要手动停掉：

```bash
docker rm -f carla-headed
```

## 3. 启动主机跟车显示链

如果只是想先把跟车画面挂在主机显示器上：

```bash
cd /home/du/ros2-humble/src
bash hil_runtime/host/scripts/start_carla_front_rgb_preview.sh \
  --display-mode native_follow \
  --map-name Town10HD_Opt \
  --no-spawn-ego-if-missing \
  --no-enable-autopilot \
  --traffic-vehicles 0
```

如果是由平台 HIL 编排通过 SSH 回到主机拉起显示链，入口是：

```bash
cd /home/du/ros2-humble/src
bash hil_runtime/host/scripts/start_host_display_remote.sh
```

当前默认行为：

- 预览启动前会先确保主机 `HDMI-0` 已经被激活为镜像输出
- display mode 为 `native_follow`
- 默认等待 hero 的时间继承 `DUCKPARK_HIL_TIMEOUT_SECONDS`
- 如果没有显式设置，就按 `86400` 秒等待，不会像旧版那样在 `90` 秒后自己退出

查看显示链日志：

```bash
tail -f /tmp/carla_front_rgb_preview.log
```

看到下面这类日志说明主机跟车画面已经稳定起来：

```text
preview ready map=Town10HD_Opt display_mode=native_follow
native_follow loop_hz=59.8
```

## 4. 让 Web 场景启动时自动拉起主机链路

如果希望在 Web 里点运行时，由 executor 自动调起：

- host CARLA
- host display
- Pi RTP pipeline

需要在 `carla_web_platform/.env.local` 或远端运行环境里设置这些命令：

```bash
HIL_ORCHESTRATION_ENABLED=true
HIL_HOST_CARLA_START_COMMAND="bash hil_runtime/host/scripts/start_host_carla_remote.sh"
HIL_HOST_CARLA_STOP_COMMAND="bash hil_runtime/host/scripts/stop_host_carla_remote.sh"
HIL_HOST_DISPLAY_START_COMMAND="bash hil_runtime/host/scripts/start_host_display_remote.sh"
HIL_HOST_DISPLAY_STOP_COMMAND="bash hil_runtime/host/scripts/stop_host_display_remote.sh"
HIL_PI_START_COMMAND="bash hil_runtime/host/scripts/start_pi_rtp_stream_remote.sh"
HIL_PI_STOP_COMMAND="bash hil_runtime/host/scripts/stop_pi_rtp_stream_remote.sh"
```

如果 executor 运行在 `ros2-dev` 容器里，而 headed CARLA 在物理主机上，还需要补 SSH 回跳配置：

```bash
DUCKPARK_HOST_SSH_HOST=192.168.110.151
DUCKPARK_HOST_SSH_USER=du
DUCKPARK_HOST_SSH_PORT=22
DUCKPARK_HOST_SRC_ROOT=/home/du/ros2-humble/src
```

注意：

- 这套编排默认只自动处理 Host + Pi
- Jetson 启停当前建议手动维护，除非已经确认 `HIL_JETSON_START_COMMAND` / `HIL_JETSON_STOP_COMMAND` 在远端可稳定执行

## 5. 最小演示启动顺序

推荐的 live bring-up 顺序：

1. 主机上确认 `carla_web_platform/` 和 `hil_runtime/` 都在 `/home/du/ros2-humble/src`
2. 在 `ros2-dev` 里启动平台 Web/API/executor
3. 在主机 shell 启动 headed CARLA
4. 打开 `http://192.168.110.151:8000/ui`
5. 从 Web 下发 `town10_autonomous_demo` 或 `free_drive_sensor_collection`
6. 观察主机显示器上的 CARLA 跟车画面是否已经出来
7. 再打开 Pi 和 Jetson 链路，确认 HDMI -> RTP -> 推理链继续成立
8. 如果需要在 Web `设备中心 / 单 DUT 运行观测` 里看到在线曲线，再确认 Pi `gateway_agent` 正在持续 heartbeat

补充说明：

- 当前 `POST /scenarios/launch` 会按场景目录默认补齐 HIL 编排配置，因此这条入口更适合“真正演示链”。
- 如果只是想验证 native runtime 核心链，不想把 Pi / Jetson sidecar 一起拉起来，建议直接走 `POST /runs`，或者使用 `python3 scripts/remote_smoke.py --mode core`。
- 当前 Web 默认可见的内置模板已经限制在远端实机确认存在的地图集合内：`Town01`、`Town02`、`Town03`、`Town04`、`Town05`、`Town10HD_Opt`。
- 内置巡航模板默认都由平台内置 Traffic Manager 自动驾驶控制 hero，不走官方 `ScenarioRunner` 主执行链。

## 6. 常见问题

### CARLA 窗口一闪就退

优先检查：

- 是否还有旧 CARLA 容器占着 `2000` 端口
- `start_carla_headed.sh` 是否真的等到了 simulator world ready
- `docker logs carla-headed` 里有没有显卡或 X11 权限错误

### 主机显示器没跟车视角

优先检查：

- `/tmp/carla_front_rgb_preview.log`
- run 事件里是否已经出现 `EGO_SPAWNED`
- 当前场景是否已经进入 `RUNNING`

### Web 可以看到 run，但主机 CARLA 没画面

这通常不是 Web 问题，而是 Host sidecar 没起来。先检查：

- `HIL_HOST_CARLA_START_COMMAND`
- `HIL_HOST_DISPLAY_START_COMMAND`
- SSH 回跳配置
- 主机上 `/home/du/ros2-humble/src/hil_runtime/...` 是否存在

### 设备中心看不到单 DUT 实时观测

先分清两条状态链：

- `Pi chain READY`
  - 只代表平台能通过 SSH 触达 Pi，并能执行 Pi 链路启动命令
- `Gateway BUSY / READY`
  - 代表 Pi `gateway_agent` 正在把心跳和 DUT 指标持续上报到平台

如果 Jetson 推理已经在跑，但 `设备中心` 仍然没有实时观测，优先检查：

- Pi 上 `dut_result_receiver` 是否还在跑
- Pi 上 `python3 -m app.hil.gateway_agent ...` 是否常驻
- 平台 `GET /gateways` 返回的 `last_heartbeat_at_utc` 是否在持续刷新
- 平台 `GET /devices/workspace` 返回的 `online_device_count` 是否大于 `0`

在 Pi 上手动补起一次 `gateway_agent` 的最小命令：

```bash
cd /home/kavin/duckpark/carla_web_platform
python3 -m app.hil.gateway_agent \
  --api-base-url http://192.168.110.151:8000 \
  --gateway-id rpi5-x1301-01 \
  --gateway-name bench-a \
  --input-video-device /dev/video0
```

如果只想做一次注入和状态确认，可以加 `--once`。

## 7. 关联文档

- [README.md](/Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform/README.md)
- [remote-ops.md](/Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform/docs/remote-ops.md)
- [pi_jetson_rtp_pipeline.md](/Users/kavin/Documents/GitHub/duckPark/src/hil_runtime/docs/pi_jetson_rtp_pipeline.md)
