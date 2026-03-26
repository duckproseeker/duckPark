# Git 同步远端部署

## 适用环境

- 本机仓库是唯一的代码审查与提交来源。
- 正式主机：`192.168.110.151`
- 主机 checkout：`/home/du/ros2-humble/src/carla_web_platform`
- 运行容器：`ros2-dev`
- 容器内项目目录：`/ros2_ws/src/carla_web_platform`
- Git 同步分支：`rabbitank/carla-web-platform-sync`

不要把主机上的运行目录当作人工改代码的工作区。现在正式环境已经切到 Git checkout，同步方式统一走脚本，不再走 bundle 覆盖或远端手工清目录。

如果目标是把 headed CARLA、主机显示链、Pi/Jetson 一起带起来，优先看：

- `docs/host-bringup.md`

## 入口脚本

- `scripts/publish_git_sync_branch.sh`
  - 把 `src/carla_web_platform` 做 `git subtree split`
  - 强推到 `rabbitank/carla-web-platform-sync`
- `scripts/remote_git_sync.sh`
  - 执行主机 checkout 更新、前端构建、服务重启和 smoke
- `scripts/remote_smoke.py`
  - 对已经跑起来的远端 API 做 smoke，不走 SSH

## 快速命令

部署：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
REMOTE_PASSWORD='***' bash scripts/remote_git_sync.sh deploy
```

回滚：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
REMOTE_PASSWORD='***' bash scripts/remote_git_sync.sh rollback
```

Makefile 包装：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
make remote-sync
make remote-rollback
SMOKE_MODE=scenario make remote-smoke
SMOKE_MODE=capture make remote-smoke
```

只做远端 smoke：

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
python3 scripts/remote_smoke.py --base-url http://192.168.110.151:8000 --mode basic
python3 scripts/remote_smoke.py --base-url http://192.168.110.151:8000 --mode core
python3 scripts/remote_smoke.py --base-url http://192.168.110.151:8000 --mode scenario
python3 scripts/remote_smoke.py --base-url http://192.168.110.151:8000 --mode capture
```

## `deploy` 实际做的事

`scripts/remote_git_sync.sh deploy` 会按顺序执行：

1. 发布 `src/carla_web_platform` 的 subtree 分支。
2. 停掉主机上当前 API、executor 和 recorder worker。
3. 在主机上执行下面两种路径之一：
   - 现有目录已经是 Git checkout：直接 `fetch + checkout + reset --hard`
   - 现有目录不是 Git checkout：先改名为 `carla_web_platform_bak_<timestamp>`，再重新 clone
4. 从备份目录恢复：
   - `.env.local`
   - `run_data/`
   - `artifacts/`
5. 确保新目录和持久目录归属为 `du:du`。
6. 重新构建 `frontend/dist`。
   - 优先在主机上用 Node 20 helper container 构建
   - 如果主机拉不到 Node 镜像，则回退到本机构建并上传 `frontend/dist`
7. 重启 API 和 executor。
8. 跑 `basic` smoke：
   - `/healthz`
   - `/system/status`
   - `/ui`

这条链路的关键点是“主机目录本身变成 Git checkout”，以后同步只需要更新 branch，而不是反复打 bundle 覆盖。

## `rollback` 实际做的事

`scripts/remote_git_sync.sh rollback` 会：

1. 停掉当前 API 和 executor。
2. 删除当前主机 checkout。
3. 把最近一次 `carla_web_platform_bak_<timestamp>` 改回原路径。
4. 重新构建 `frontend/dist`、重启服务、再跑 `basic` smoke。

当前 checkout 根目录会写一个 `.git-sync-backup-path`，用于记录最近一次可回滚的备份目录。

## 常用选项

- `--source-ref <ref>`
  - 指定 subtree split 的来源，默认 `main`
- `--sync-branch <branch>`
  - 指定发布到远端主机的同步分支
- `--skip-publish`
  - 不重新发布 subtree，直接用远端已有 branch 部署
- `--skip-frontend-build`
  - 跳过 `frontend/dist` 构建，适合只验证代码 checkout/服务重启
- `--skip-restart`
  - 只同步目录，不重启服务
- `--skip-smoke`
  - 不跑 smoke

## 验证分层

- `basic`
  - 只证明远端 API、executor 和 `/ui` 基本可用
- `core`
  - 在 `basic` 基础上跑一条最小 native runtime run
- `scenario`
  - 在 `basic` 基础上跑短时 `free_drive_sensor_collection`
- `capture`
  - 在 `scenario` 基础上再验证 capture / recorder 证据链

注意：

- `remote_git_sync.sh` 自带的部署后 smoke 固定是 `basic`
- 更深的运行链验证要额外执行 `python3 scripts/remote_smoke.py --mode ...`
- `remote_smoke.py` 是直接打 HTTP，不需要 `REMOTE_PASSWORD`

## 建议流程

1. 本机先跑：
   - `make contract-sync`
   - `make lint`
   - `pytest -q`
   - `cd frontend && npm run check-types && npm run build`
2. 部署主机：
   - `REMOTE_PASSWORD='***' bash scripts/remote_git_sync.sh deploy`
3. 如果改动涉及 native runtime、环境控制或采集链路，再补：
   - `python3 scripts/remote_smoke.py --base-url http://192.168.110.151:8000 --mode scenario`
   - 或 `python3 scripts/remote_smoke.py --base-url http://192.168.110.151:8000 --mode capture`

## 范围边界

- 这条 Git 同步链只覆盖 `src/carla_web_platform/`
- `src/hil_runtime/` 下的 host / Pi / Jetson 运行资产仍需单独同步
- 换句话说：它负责平台 `/ui`、API、executor 和前端 bundle，不负责 headed CARLA 或 Pi/Jetson sidecar 的发布

## 已知注意事项

- `basic` smoke 不能证明 CARLA、Pi、Jetson、viewer 或 HDMI 链路是 live 的。
- `capture` smoke 依赖更多外部环境，最容易因为现场环境而失败。
- 设备页的实时在线判定依赖 Pi `gateway_agent` heartbeat，不是只看 Jetson 结果文件。
- 远端重启日志默认写到：
  - `/tmp/carla_api_restore.log`
  - `/tmp/carla_executor_restore.log`
- 服务重启时会带上 `PYTHONDONTWRITEBYTECODE=1`，避免远端目录继续长出 `__pycache__/` 噪音。
