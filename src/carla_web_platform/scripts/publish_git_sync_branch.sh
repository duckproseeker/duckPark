#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
REPO_ROOT=$(git -C "${PROJECT_ROOT}" rev-parse --show-toplevel)

SOURCE_REF="${SOURCE_REF:-HEAD}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-rabbitank/carla-web-platform-sync}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
SKIP_PUSH=0

usage() {
  cat <<'EOF'
用法:
  bash scripts/publish_git_sync_branch.sh [options]

作用:
  将当前项目目录发布为一个可直接 clone 的 Git 分支。
  在 monorepo 中会自动从 src/carla_web_platform 做 subtree split。

可选参数:
  --source-ref <ref>         源提交或分支，默认 HEAD
  --deploy-branch <branch>   发布分支，默认 rabbitank/carla-web-platform-sync
  --remote <name>            Git remote，默认 origin
  --skip-push                只计算 split commit，不推送
  --help                     输出帮助
EOF
}

require_arg_value() {
  if [[ $# -lt 2 || -z "${2:-}" ]]; then
    printf '参数 %s 缺少取值\n' "$1" >&2
    usage >&2
    exit 1
  fi
}

while (($# > 0)); do
  case "$1" in
    --source-ref)
      require_arg_value "$@"
      SOURCE_REF="$2"
      shift 2
      ;;
    --deploy-branch)
      require_arg_value "$@"
      DEPLOY_BRANCH="$2"
      shift 2
      ;;
    --remote)
      require_arg_value "$@"
      REMOTE_NAME="$2"
      shift 2
      ;;
    --skip-push)
      SKIP_PUSH=1
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

PROJECT_RELATIVE_PATH=$(
  python3 - "${REPO_ROOT}" "${PROJECT_ROOT}" <<'PY'
from pathlib import Path
import sys

repo_root = Path(sys.argv[1]).resolve()
project_root = Path(sys.argv[2]).resolve()

if project_root == repo_root:
    print("")
else:
    print(project_root.relative_to(repo_root).as_posix())
PY
)

if [[ -n "${PROJECT_RELATIVE_PATH}" ]]; then
  SPLIT_COMMIT=$(git -C "${REPO_ROOT}" subtree split --prefix="${PROJECT_RELATIVE_PATH}" "${SOURCE_REF}")
else
  SPLIT_COMMIT=$(git -C "${REPO_ROOT}" rev-parse "${SOURCE_REF}^{commit}")
fi

if (( SKIP_PUSH == 0 )); then
  git -C "${REPO_ROOT}" push --force "${REMOTE_NAME}" "${SPLIT_COMMIT}:refs/heads/${DEPLOY_BRANCH}"
fi

printf 'repo_root=%s\n' "${REPO_ROOT}"
printf 'project_prefix=%s\n' "${PROJECT_RELATIVE_PATH:-.}"
printf 'source_ref=%s\n' "${SOURCE_REF}"
printf 'split_commit=%s\n' "${SPLIT_COMMIT}"
printf 'deploy_branch=%s\n' "${DEPLOY_BRANCH}"
printf 'remote=%s\n' "${REMOTE_NAME}"
