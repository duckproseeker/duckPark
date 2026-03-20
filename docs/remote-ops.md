# 远端部署与清理

## 适用环境

- 本机职责：只负责修改代码、跑本地验证、触发远端部署。
- 正式服务：`192.168.110.151`
- 远端容器：`ros2-dev`
- 正式代码目录：`/ros2_ws/src/carla_web_platform`
- CARLA 服务：单独容器，通常通过 `~/startCarla.sh` 拉起

不要把正式远端目录当作 Git 审查工作区。它是运行时镜像目录，真正的代码审查、提交和变更范围确认都应该以本机仓库为准。

如果你这次目标不是“部署代码”，而是“把主机上的 Web、headed CARLA、跟车显示链真的拉起来”，优先看：

- `docs/host-bringup.md`

## 入口脚本

### 1. 清理远端垃圾文件

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
REMOTE_PASSWORD='***' bash scripts/remote_cleanup.sh
```

清理内容：

- `._*` AppleDouble 垃圾文件
- `.DS_Store`
- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- `frontend/tmp/`
- 项目目录上一层的 `._*` 残留

如果只想预览：

```bash
REMOTE_PASSWORD='***' bash scripts/remote_cleanup.sh --dry-run
```

如果要顺手把正式目录顶层不在白名单里的旧文件也一起清掉：

```bash
REMOTE_PASSWORD='***' bash scripts/remote_cleanup.sh --prune-top-level
```

### 2. 部署到正式远端

```bash
cd /Users/kavin/Documents/GitHub/duckPark/src/carla_web_platform
REMOTE_PASSWORD='***' bash scripts/remote_deploy.sh --smoke-mode basic
```

支持的 smoke 模式：

- `basic`
  - 校验 `/healthz`
  - 校验 `/system/status`
  - 校验 `/ui`
- `scenario`
  - 在 `basic` 基础上，再启动一条短时 `free_drive_sensor_collection` 并停止
- `capture`
  - 在 `scenario` 基础上，再验证 recorder、手动开始/停止传感器采集、viewer 抓帧

常用例子：

```bash
REMOTE_PASSWORD='***' bash scripts/remote_deploy.sh --smoke-mode scenario
REMOTE_PASSWORD='***' bash scripts/remote_deploy.sh --smoke-mode capture
REMOTE_PASSWORD='***' bash scripts/remote_deploy.sh --skip-contract-sync --skip-frontend-build
```

也可以直接走 Makefile 包装：

```bash
make remote-clean
SMOKE_MODE=scenario make remote-deploy
SMOKE_MODE=capture make remote-deploy
```

## 部署脚本做的事

`scripts/remote_deploy.sh` 会按顺序执行：

1. 可选执行 `make contract-sync`
2. 可选执行 `frontend` 生产构建
3. 打包本地要同步的目标文件
4. 在远端正式目录生成备份 tar
5. 把远端目标目录整目录删除后再解压新的 bundle
6. 清理远端垃圾文件
7. 重启 API 和 executor
8. 运行 smoke
9. 如果 smoke 失败，自动回滚到备份并再次重启

这套流程的关键点是“整目录替换”，不是“覆盖拷贝”。这样可以一起清掉历史部署遗留的旧文件。

## 顶层保留白名单

部署和 `--prune-top-level` 清理时，远端正式目录只保留这些长期存在的顶层项：

- `.env.local`
- `.git`
- `artifacts/`
- `run_data/`
- 当前 bundle 应该同步的源码和文档目录

这意味着历史遗留的顶层旧文件、旧目录、错误同步出来的孤儿文件都会被清掉，不会继续混在正式目录里。

## 当前同步范围

部署脚本默认同步这些目录和文件：

- `.dockerignore`
- `.env.local.example`
- `.gitignore`
- `DESIGN.md`
- `FRONTEND_REACT_PHASE1.md`
- `Makefile`
- `README.md`
- `app/`
- `configs/`
- `contracts/`
- `docker/`
- `docs/`
- `environment.web.yml`
- `frontend/`
- `pyproject.toml`
- `pytest.ini`
- `requirements-dev.txt`
- `requirements.txt`
- `scripts/`
- `tests/`

不会同步：

- `.env.local`
- `run_data/`
- `artifacts/`
- `frontend/node_modules/`
- `frontend/tmp/`
- 本地缓存目录

注意：

- 这个平台部署 bundle 当前只覆盖 `src/carla_web_platform/`
- `src/hil_runtime/` 下的 host / Pi / Jetson 运行资产需要按目标机器单独同步，不会被这条平台部署链自动带上
- 换句话说：`remote_deploy.sh` 能把 `/ui`、API 和 executor 更新到远端，但不会自动替你部署 headed CARLA 或主机/Pi/Jetson sidecar 脚本

## 回滚说明

部署时会在远端容器内生成类似下面的备份：

```text
/tmp/duckpark_remote_backup_<timestamp>.tgz
```

如果 smoke 失败，脚本会自动：

1. 删除本次同步进去的目标目录
2. 还原备份 tar
3. 重启 API 和 executor
4. 再跑一次 `basic` smoke

## 建议流程

1. 本机先跑：
   - `make lint`
   - `pytest -q`
   - `make contract-sync`
   - `cd frontend && npm run check-types && npm run build`
2. 远端先清理一次：
   - `bash scripts/remote_cleanup.sh`
3. 再部署：
   - `bash scripts/remote_deploy.sh --smoke-mode scenario`
4. 涉及采集链路时，再补一轮：
   - `bash scripts/remote_deploy.sh --smoke-mode capture`

如果这次目标是观察 native runtime 的执行速率，建议在 `scenario` smoke 之后再补一次最小 run：

- traffic 设为 `0/0`
- 关闭不必要的 recorder / sidecar
- 结束后读取 `GET /runs/{run_id}` 里的 `achieved_tick_rate_hz`

这样得到的值更接近“native runtime 自身执行链”的基线，不会把背景交通或采集链路的额外开销混进一起看。

如果这次只改了文档、脚本或后端非契约逻辑，可以先用：

- `bash scripts/remote_deploy.sh --smoke-mode basic --skip-contract-sync --skip-frontend-build`

## 已知注意事项

- `capture` smoke 会依赖 CARLA、平台 native runtime、viewer 和传感器链路，耗时最长，也最容易暴露环境问题。
- CARLA recorder 目前状态链路已接通，但 recorder 文件落盘还受 CARLA server 容器与 executor 容器之间的路径共享方式影响。部署 smoke 不应只看“recorder 状态为 RUNNING”，还要结合产物验证。
- 当前远端重启日志默认写到：
  - `/tmp/carla_api_restore.log`
  - `/tmp/carla_executor_restore.log`
  如果 smoke 失败，先看这两个日志，再判断是不是需要回滚。
- 部署脚本重启服务时会带上 `PYTHONDONTWRITEBYTECODE=1`，避免正式目录里不断累积 `__pycache__/`，减少远端误判“源码脏了”的噪音。
