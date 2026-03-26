#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)

# shellcheck disable=SC1091
source "${PROJECT_ROOT}/scripts/remote_ops_lib.sh"

REMOTE_HOST_PROJECT_ROOT="${REMOTE_HOST_PROJECT_ROOT:-/home/du/ros2-humble/src/carla_web_platform}"
REMOTE_RUNTIME_PROJECT_ROOT="${REMOTE_RUNTIME_PROJECT_ROOT:-/ros2_ws/src/carla_web_platform}"
REMOTE_PROJECT_ROOT="${REMOTE_RUNTIME_PROJECT_ROOT}"

SYNC_SOURCE_REF="${SYNC_SOURCE_REF:-HEAD}"
SYNC_BRANCH="${SYNC_BRANCH:-rabbitank/carla-web-platform-sync}"
SYNC_REMOTE="${SYNC_REMOTE:-origin}"
SYNC_REPO_URL="${SYNC_REPO_URL:-https://github.com/duckproseeker/duckPark.git}"
REMOTE_OWNER="${REMOTE_OWNER:-${REMOTE_USER}}"
SKIP_PUBLISH=0
SKIP_RESTART=0
SKIP_SMOKE=0

usage() {
  cat <<'EOF'
用法:
  bash scripts/remote_git_sync.sh <deploy|rollback> [options]

deploy:
  1. 本地将当前项目发布到一个可直接 clone 的 deploy 分支
  2. 远端旧目录改名为 carla_web_platform_bak_<timestamp>
  3. 在原路径重新 clone
  4. 恢复 .env.local
  5. 将 run_data / artifacts 挂回新目录
  6. 重启 API / executor
  7. 做 smoke

rollback:
  1. 删除当前新目录
  2. 将最近一次 bak 目录改回原名
  3. 重启 API / executor
  4. 做 smoke

可选参数:
  --source-ref <ref>             发布源提交，默认 HEAD
  --sync-branch <branch>         deploy 分支，默认 rabbitank/carla-web-platform-sync
  --sync-remote <name>           推送 remote，默认 origin
  --repo-url <url>               远端 clone 使用的仓库地址
  --host-project-root <path>     主机目录，默认 /home/du/ros2-humble/src/carla_web_platform
  --runtime-project-root <path>  容器内目录，默认 /ros2_ws/src/carla_web_platform
  --skip-publish                 不重新发布 deploy 分支
  --skip-restart                 不重启 API / executor
  --skip-smoke                   不做 smoke
  --help                         输出帮助
EOF
}

require_arg_value() {
  if [[ $# -lt 2 || -z "${2:-}" ]]; then
    printf '参数 %s 缺少取值\n' "$1" >&2
    usage >&2
    exit 1
  fi
}

require_local_cmds() {
  local missing=0
  local cmd
  for cmd in expect git python3 ssh; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
      printf '[remote-git-sync] missing command: %s\n' "${cmd}" >&2
      missing=1
    fi
  done
  if (( missing != 0 )); then
    exit 1
  fi
}

publish_sync_branch() {
  bash "${PROJECT_ROOT}/scripts/publish_git_sync_branch.sh" \
    --source-ref "${SYNC_SOURCE_REF}" \
    --deploy-branch "${SYNC_BRANCH}" \
    --remote "${SYNC_REMOTE}"
}

deploy_remote_checkout() {
  local remote_script
  remote_script="$(cat <<EOF
set -euo pipefail

project_root=$(printf '%q' "${REMOTE_HOST_PROJECT_ROOT}")
repo_url=$(printf '%q' "${SYNC_REPO_URL}")
branch=$(printf '%q' "${SYNC_BRANCH}")
owner=$(printf '%q' "${REMOTE_OWNER}")
backup_marker=".git-sync-backup-path"
timestamp=\$(date +%Y%m%d_%H%M%S)
backup_path=""

mkdir -p "\$(dirname "\${project_root}")"

if [[ -d "\${project_root}/.git" ]]; then
  git -C "\${project_root}" remote set-url origin "\${repo_url}"
  git -C "\${project_root}" fetch --depth 1 origin "\${branch}"
  git -C "\${project_root}" checkout -B "\${branch}" "origin/\${branch}"
  git -C "\${project_root}" reset --hard "origin/\${branch}"

  if [[ ! -f "\${project_root}/.env.local" && -f "\${project_root}/\${backup_marker}" ]]; then
    backup_path=\$(cat "\${project_root}/\${backup_marker}")
    if [[ -f "\${backup_path}/.env.local" ]]; then
      cp -a "\${backup_path}/.env.local" "\${project_root}/.env.local"
    fi
  fi
else
  if [[ -e "\${project_root}" ]]; then
    backup_path="\${project_root}_bak_\${timestamp}"
    mv "\${project_root}" "\${backup_path}"
  fi

  git clone --depth 1 --branch "\${branch}" "\${repo_url}" "\${project_root}"

  if [[ -n "\${backup_path}" ]]; then
    if [[ -f "\${backup_path}/.env.local" ]]; then
      cp -a "\${backup_path}/.env.local" "\${project_root}/.env.local"
    fi

    for persistent_dir in run_data artifacts; do
      if [[ -e "\${backup_path}/\${persistent_dir}" ]]; then
        rm -rf "\${project_root}/\${persistent_dir}"
        ln -s "\${backup_path}/\${persistent_dir}" "\${project_root}/\${persistent_dir}"
      fi
    done

    printf '%s\n' "\${backup_path}" > "\${project_root}/\${backup_marker}"
  fi
fi

for persistent_dir in run_data artifacts; do
  if [[ ! -e "\${project_root}/\${persistent_dir}" ]]; then
    mkdir -p "\${project_root}/\${persistent_dir}"
  fi
done

chown -R "\${owner}:\${owner}" "\${project_root}"
for persistent_dir in run_data artifacts; do
  if [[ -e "\${project_root}/\${persistent_dir}" ]]; then
    chown -h "\${owner}:\${owner}" "\${project_root}/\${persistent_dir}" || true
  fi
done

printf 'project_root=%s\n' "\${project_root}"
printf 'branch=%s\n' "\${branch}"
if [[ -n "\${backup_path}" ]]; then
  printf 'backup_path=%s\n' "\${backup_path}"
fi
EOF
)"

  remote_host_bash "${remote_script}"
}

rollback_remote_checkout() {
  local remote_script
  remote_script="$(cat <<EOF
set -euo pipefail

project_root=$(printf '%q' "${REMOTE_HOST_PROJECT_ROOT}")
owner=$(printf '%q' "${REMOTE_OWNER}")
backup_marker=".git-sync-backup-path"
backup_path=""

if [[ -f "\${project_root}/\${backup_marker}" ]]; then
  backup_path=\$(cat "\${project_root}/\${backup_marker}")
fi

if [[ -z "\${backup_path}" ]]; then
  backup_path=\$(find "\$(dirname "\${project_root}")" -maxdepth 1 -type d -name "$(basename "${REMOTE_HOST_PROJECT_ROOT}")_bak_*" | sort | tail -n 1)
fi

if [[ -z "\${backup_path}" || ! -d "\${backup_path}" ]]; then
  printf '未找到可回滚的备份目录\n' >&2
  exit 1
fi

rm -rf "\${project_root}"
mv "\${backup_path}" "\${project_root}"
chown -R "\${owner}:\${owner}" "\${project_root}"

printf 'project_root=%s\n' "\${project_root}"
printf 'restored_from=%s\n' "\${backup_path}"
EOF
)"

  remote_host_bash "${remote_script}"
}

restart_and_smoke() {
  if (( SKIP_RESTART == 0 )); then
    restart_remote_services
  fi

  if (( SKIP_SMOKE == 0 )); then
    run_remote_smoke full
  fi
}

COMMAND="${1:-}"
if [[ "${COMMAND}" == "--help" || "${COMMAND}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ -z "${COMMAND}" ]]; then
  usage >&2
  exit 1
fi
shift

while (($# > 0)); do
  case "$1" in
    --source-ref)
      require_arg_value "$@"
      SYNC_SOURCE_REF="$2"
      shift 2
      ;;
    --sync-branch)
      require_arg_value "$@"
      SYNC_BRANCH="$2"
      shift 2
      ;;
    --sync-remote)
      require_arg_value "$@"
      SYNC_REMOTE="$2"
      shift 2
      ;;
    --repo-url)
      require_arg_value "$@"
      SYNC_REPO_URL="$2"
      shift 2
      ;;
    --host-project-root)
      require_arg_value "$@"
      REMOTE_HOST_PROJECT_ROOT="$2"
      shift 2
      ;;
    --runtime-project-root)
      require_arg_value "$@"
      REMOTE_RUNTIME_PROJECT_ROOT="$2"
      REMOTE_PROJECT_ROOT="$2"
      shift 2
      ;;
    --skip-publish)
      SKIP_PUBLISH=1
      shift
      ;;
    --skip-restart)
      SKIP_RESTART=1
      shift
      ;;
    --skip-smoke)
      SKIP_SMOKE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf '未知参数: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

require_local_cmds

case "${COMMAND}" in
  deploy)
    if (( SKIP_PUBLISH == 0 )); then
      publish_sync_branch
    fi
    deploy_remote_checkout
    restart_and_smoke
    ;;
  rollback)
    rollback_remote_checkout
    restart_and_smoke
    ;;
  *)
    printf '未知命令: %s\n' "${COMMAND}" >&2
    usage >&2
    exit 1
    ;;
esac
