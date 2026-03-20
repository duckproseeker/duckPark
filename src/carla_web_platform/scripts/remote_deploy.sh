#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/remote_ops_lib.sh
source "${SCRIPT_DIR}/remote_ops_lib.sh"

SMOKE_MODE="${SMOKE_MODE:-basic}"
RUN_CONTRACT_SYNC=1
RUN_FRONTEND_BUILD=1
KEEP_LOCAL_ARCHIVE=0
BUNDLE_PATH=""
REMOTE_HOST_ARCHIVE=""
REMOTE_CONTAINER_ARCHIVE=""
REMOTE_BACKUP_ARCHIVE=""
ROLLBACK_NEEDED=0

usage() {
  cat <<'EOF'
Usage: bash scripts/remote_deploy.sh [options]

Options:
  --smoke-mode basic|scenario|capture  Smoke mode after restart. Default: basic
  --skip-contract-sync                 Skip OpenAPI export and TS type generation
  --skip-frontend-build                Skip frontend production build
  --keep-local-archive                 Keep the generated /tmp deploy archive
  -h, --help                           Show this help

Environment:
  REMOTE_PASSWORD                      SSH password for remote host
  REMOTE_HOST                          Default: 192.168.110.151
  REMOTE_USER                          Default: du
  REMOTE_CONTAINER                     Default: ros2-dev
  REMOTE_PROJECT_ROOT                  Default: /ros2_ws/src/carla_web_platform
  REMOTE_API_BASE_URL                  Default: http://<REMOTE_HOST>:8000
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke-mode)
      SMOKE_MODE="$2"
      shift 2
      ;;
    --skip-contract-sync)
      RUN_CONTRACT_SYNC=0
      shift
      ;;
    --skip-frontend-build)
      RUN_FRONTEND_BUILD=0
      shift
      ;;
    --keep-local-archive)
      KEEP_LOCAL_ARCHIVE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf '[remote-deploy] unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$SMOKE_MODE" in
  basic|scenario|capture)
    ;;
  *)
    printf '[remote-deploy] unsupported smoke mode: %s\n' "$SMOKE_MODE" >&2
    exit 1
    ;;
esac

rollback_remote_deploy() {
  if (( ROLLBACK_NEEDED == 0 )) || [[ -z "$REMOTE_BACKUP_ARCHIVE" ]]; then
    return 0
  fi

  remote_log "deploy failed, rolling back from ${REMOTE_BACKUP_ARCHIVE}"
  local targets_array
  local keep_array
  local cleanup_snippet
  local prune_snippet
  targets_array="$(render_remote_targets_array)"
  keep_array="$(render_remote_keep_array)"
  cleanup_snippet="$(render_remote_cleanup_snippet)"
  prune_snippet="$(render_remote_prune_top_level_snippet)"

  if ! remote_container_bash "
set -euo pipefail
cd $(printf '%q' "$REMOTE_PROJECT_ROOT")
${targets_array}
${keep_array}
for target in \"\${targets[@]}\"; do
  rm -rf \"\$target\"
done
tar xzf $(printf '%q' "$REMOTE_BACKUP_ARCHIVE")
${cleanup_snippet}
${prune_snippet}
"; then
    remote_log "rollback restore failed"
    return 1
  fi

  if ! restart_remote_services; then
    remote_log "rollback service restart failed"
    return 1
  fi

  if ! run_remote_smoke basic; then
    remote_log "rollback smoke failed"
    return 1
  fi

  remote_log "rollback completed"
  return 0
}

cleanup_local_archive() {
  if (( KEEP_LOCAL_ARCHIVE == 0 )) && [[ -n "$BUNDLE_PATH" ]]; then
    rm -f "$BUNDLE_PATH"
  fi
}

on_exit() {
  local exit_code="$1"
  if (( exit_code != 0 )); then
    rollback_remote_deploy || true
  fi
  cleanup_local_archive
}

trap 'on_exit $?' EXIT

require_remote_ops_cmds
ensure_remote_password

if (( RUN_CONTRACT_SYNC == 1 )); then
  remote_log "running contract sync"
  (
    cd "$PROJECT_ROOT"
    make contract-sync
  )
fi

if (( RUN_FRONTEND_BUILD == 1 )); then
  remote_log "building frontend"
  (
    cd "$PROJECT_ROOT/frontend"
    npm run build
  )
fi

timestamp="$(date +%Y%m%d%H%M%S)"
BUNDLE_PATH="/tmp/duckpark_remote_deploy_${timestamp}.tgz"
REMOTE_HOST_ARCHIVE="/tmp/duckpark_remote_deploy_${timestamp}.tgz"
REMOTE_CONTAINER_ARCHIVE="/tmp/duckpark_remote_deploy_${timestamp}.tgz"
REMOTE_BACKUP_ARCHIVE="/tmp/duckpark_remote_backup_${timestamp}.tgz"

remote_log "creating local bundle ${BUNDLE_PATH}"
create_remote_bundle "$BUNDLE_PATH"

targets_array="$(render_remote_targets_array)"
keep_array="$(render_remote_keep_array)"
cleanup_snippet="$(render_remote_cleanup_snippet)"
prune_snippet="$(render_remote_prune_top_level_snippet)"

remote_log "creating remote backup ${REMOTE_BACKUP_ARCHIVE}"
remote_container_bash "
set -euo pipefail
cd $(printf '%q' "$REMOTE_PROJECT_ROOT")
${targets_array}
existing=()
for target in \"\${targets[@]}\"; do
  if [ -e \"\$target\" ]; then
    existing+=(\"\$target\")
  fi
done
if [ \"\${#existing[@]}\" -gt 0 ]; then
  tar czf $(printf '%q' "$REMOTE_BACKUP_ARCHIVE") \"\${existing[@]}\"
else
  tar czf $(printf '%q' "$REMOTE_BACKUP_ARCHIVE") --files-from /dev/null
fi
"

ROLLBACK_NEEDED=1

remote_log "uploading bundle to ${REMOTE_HOST}:${REMOTE_HOST_ARCHIVE}"
remote_scp "$BUNDLE_PATH" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_HOST_ARCHIVE}"
remote_host_bash "
set -euo pipefail
docker cp $(printf '%q' "$REMOTE_HOST_ARCHIVE") ${REMOTE_CONTAINER}:$(printf '%q' "$REMOTE_CONTAINER_ARCHIVE")
rm -f $(printf '%q' "$REMOTE_HOST_ARCHIVE")
"

remote_log "replacing remote source tree"
remote_container_bash "
set -euo pipefail
cd $(printf '%q' "$REMOTE_PROJECT_ROOT")
${targets_array}
${keep_array}
for target in \"\${targets[@]}\"; do
  rm -rf \"\$target\"
done
tar xzf $(printf '%q' "$REMOTE_CONTAINER_ARCHIVE")
rm -f $(printf '%q' "$REMOTE_CONTAINER_ARCHIVE")
${cleanup_snippet}
${prune_snippet}
"

remote_log "restarting remote API and executor"
restart_remote_services

if [[ "$SMOKE_MODE" != "basic" ]]; then
  remote_log "ensuring remote CARLA is ready for ${SMOKE_MODE} smoke"
  ensure_remote_carla_ready
fi

remote_log "running remote smoke (${SMOKE_MODE})"
run_remote_smoke "$SMOKE_MODE"

ROLLBACK_NEEDED=0
remote_log "deploy succeeded; backup archive kept at ${REMOTE_BACKUP_ARCHIVE}"
