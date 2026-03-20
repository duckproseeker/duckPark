#!/usr/bin/env bash

set -euo pipefail

if [[ "${REMOTE_OPS_LIB_SOURCED:-0}" == "1" ]]; then
  return 0 2>/dev/null || exit 0
fi
REMOTE_OPS_LIB_SOURCED=1

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_HOST="${REMOTE_HOST:-192.168.110.151}"
REMOTE_USER="${REMOTE_USER:-du}"
REMOTE_PORT="${REMOTE_PORT:-22}"
REMOTE_CONTAINER="${REMOTE_CONTAINER:-ros2-dev}"
REMOTE_PROJECT_ROOT="${REMOTE_PROJECT_ROOT:-/ros2_ws/src/carla_web_platform}"
REMOTE_API_BASE_URL="${REMOTE_API_BASE_URL:-http://${REMOTE_HOST}:8000}"
REMOTE_PASSWORD="${REMOTE_PASSWORD:-}"
EXPECT_TIMEOUT="${EXPECT_TIMEOUT:-600}"

REMOTE_DEPLOY_TARGETS=(
  .dockerignore
  .env.local.example
  .gitignore
  DESIGN.md
  FRONTEND_REACT_PHASE1.md
  Makefile
  README.md
  app
  configs
  contracts
  docker
  docs
  environment.web.yml
  frontend
  pyproject.toml
  pytest.ini
  requirements-dev.txt
  requirements.txt
  scripts
  tests
)

REMOTE_BUNDLE_EXCLUDES=(
  .pytest_cache
  .ruff_cache
  __pycache__
  .DS_Store
  frontend/node_modules
  frontend/tmp
  frontend/*.tsbuildinfo
  run_data
  artifacts
)

REMOTE_PERSISTENT_KEEP=(
  .env.local
  .git
  artifacts
  run_data
)

remote_log() {
  printf '[remote-ops] %s\n' "$*"
}

require_remote_ops_cmds() {
  local missing=0
  local cmd
  for cmd in expect python3 tar scp ssh; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      printf '[remote-ops] missing command: %s\n' "$cmd" >&2
      missing=1
    fi
  done
  if (( missing != 0 )); then
    return 1
  fi
}

ensure_remote_password() {
  if [[ -n "${REMOTE_PASSWORD}" ]]; then
    return 0
  fi
  if [[ ! -t 0 ]]; then
    printf '[remote-ops] REMOTE_PASSWORD is required in non-interactive mode\n' >&2
    return 1
  fi
  read -r -s -p "Remote password for ${REMOTE_USER}@${REMOTE_HOST}: " REMOTE_PASSWORD
  printf '\n'
}

expect_spawn() {
  ensure_remote_password
  local quoted_command=""
  printf -v quoted_command '%q ' "$@"
  REMOTE_PASSWORD="$REMOTE_PASSWORD" EXPECT_TIMEOUT="$EXPECT_TIMEOUT" EXPECT_COMMAND="$quoted_command" expect <<'EOF'
set timeout $env(EXPECT_TIMEOUT)
set password $env(REMOTE_PASSWORD)
eval spawn -noecho $env(EXPECT_COMMAND)
expect {
  -re {(?i)yes/no} {
    send -- "yes\r"
    exp_continue
  }
  -re {(?i)password:} {
    send -- "$password\r"
    exp_continue
  }
  eof
}
lassign [wait] _pid _spawn_id _os_error exit_code
exit $exit_code
EOF
}

remote_ssh() {
  local remote_command="$1"
  expect_spawn ssh -p "$REMOTE_PORT" -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "$remote_command"
}

remote_scp() {
  expect_spawn scp -P "$REMOTE_PORT" -o StrictHostKeyChecking=no "$@"
}

_b64_no_wrap() {
  python3 -c 'import base64,sys; sys.stdout.write(base64.b64encode(sys.stdin.buffer.read()).decode("ascii"))'
}

remote_host_bash() {
  local script="$1"
  local encoded
  local python_cmd
  encoded="$(printf '%s' "$script" | _b64_no_wrap)"
  python_cmd="import base64,subprocess; script=base64.b64decode('${encoded}').decode('utf-8'); subprocess.run(['bash','-lc',script], check=True)"
  remote_ssh "python3 -c $(printf '%q' "$python_cmd")"
}

remote_container_bash() {
  local script="$1"
  local encoded
  local python_cmd
  encoded="$(printf '%s' "$script" | _b64_no_wrap)"
  python_cmd="import base64,subprocess; script=base64.b64decode('${encoded}').decode('utf-8'); subprocess.run(['docker','exec','${REMOTE_CONTAINER}','bash','-lc',script], check=True)"
  remote_ssh "python3 -c $(printf '%q' "$python_cmd")"
}

remote_container_bash_capture() {
  local script="$1"
  local encoded
  local python_cmd
  encoded="$(printf '%s' "$script" | _b64_no_wrap)"
  python_cmd="import base64,subprocess,sys; script=base64.b64decode('${encoded}').decode('utf-8'); result=subprocess.run(['docker','exec','${REMOTE_CONTAINER}','bash','-lc',script], check=True, text=True, capture_output=True); sys.stdout.write(result.stdout)"
  remote_ssh "python3 -c $(printf '%q' "$python_cmd")"
}

render_remote_targets_array() {
  local target
  printf 'targets=('
  for target in "${REMOTE_DEPLOY_TARGETS[@]}"; do
    printf ' %q' "$target"
  done
  printf ' )'
}

render_remote_keep_array() {
  local keep_entry
  printf 'keep_entries=('
  for keep_entry in "${REMOTE_PERSISTENT_KEEP[@]}"; do
    printf ' %q' "$keep_entry"
  done
  printf ' )'
}

render_remote_cleanup_snippet() {
  cat <<'EOF'
find . -name '._*' -delete || true
find . -name '.DS_Store' -delete || true
find . -name '__pycache__' -type d -prune -exec rm -rf {} + || true
rm -rf .pytest_cache .ruff_cache frontend/tmp || true
find "$(dirname "$PWD")" -maxdepth 1 -name '._*' -delete || true
EOF
}

render_remote_prune_top_level_snippet() {
  cat <<'EOF'
shopt -s dotglob nullglob
allowed_entries=("${targets[@]}" "${keep_entries[@]}")
for entry in * .*; do
  name="$(basename "$entry")"
  case "$name" in
    .|..)
      continue
      ;;
  esac

  keep=0
  for allowed in "${allowed_entries[@]}"; do
    if [[ "$name" == "$allowed" ]]; then
      keep=1
      break
    fi
  done

  if (( keep == 0 )); then
    rm -rf "$name"
  fi
done
shopt -u dotglob nullglob
EOF
}

create_remote_bundle() {
  local archive_path="$1"
  local exclude_args=()
  local pattern
  for pattern in "${REMOTE_BUNDLE_EXCLUDES[@]}"; do
    exclude_args+=(--exclude="$pattern")
    exclude_args+=(--exclude="./$pattern")
    exclude_args+=(--exclude="*/$pattern")
  done
  COPYFILE_DISABLE=1 COPY_EXTENDED_ATTRIBUTES_DISABLE=1 \
    tar czf "$archive_path" --no-mac-metadata --no-xattrs "${exclude_args[@]}" -C "$PROJECT_ROOT" "${REMOTE_DEPLOY_TARGETS[@]}"
}

restart_remote_services() {
  local restart_script
  restart_script="$(cat <<'PY'
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def load_launch_env(project_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env_file = project_root / ".env.local"
    if not env_file.exists():
        return env

    result = subprocess.run(
        ["bash", "-lc", "set -a; source ./.env.local; env -0"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    for chunk in result.stdout.split(b"\0"):
        if not chunk or b"=" not in chunk:
            continue
        key, value = chunk.split(b"=", 1)
        env[key.decode("utf-8", errors="ignore")] = value.decode("utf-8", errors="ignore")
    return env


def find_matching_pids(pattern: str) -> list[int]:
    result = subprocess.run(
        ["pgrep", "-f", pattern],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"pgrep failed for pattern {pattern!r}: {result.stderr.strip()}")
    if result.returncode == 1:
        return []

    current_pid = os.getpid()
    parent_pid = os.getppid()
    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        pid = int(line)
        if pid not in (current_pid, parent_pid):
            pids.append(pid)
    return pids


def terminate_patterns(patterns: list[str], timeout_seconds: float) -> None:
    pending: set[int] = set()
    for pattern in patterns:
        pending.update(find_matching_pids(pattern))

    for pid in pending:
        os.kill(pid, signal.SIGTERM)

    deadline = time.monotonic() + timeout_seconds
    while pending and time.monotonic() < deadline:
        time.sleep(0.5)
        pending = {pid for pid in pending if Path(f"/proc/{pid}").exists()}

    for pid in list(pending):
        os.kill(pid, signal.SIGKILL)


def spawn_process(command: list[str], project_root: Path, env: dict[str, str], log_path: Path) -> int:
    log_handle = log_path.open("ab")
    try:
        process = subprocess.Popen(
            command,
            cwd=project_root,
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        return process.pid
    finally:
        log_handle.close()


project_root = Path(os.environ["DUCKPARK_REMOTE_PROJECT_ROOT"]).resolve()
api_log_path = Path("/tmp/carla_api_restore.log")
executor_log_path = Path("/tmp/carla_executor_restore.log")

api_patterns = [
    "".join(["python3 -m", " uvicorn app.api.main:app --host 0.0.0.0 --port 8000"]),
    "".join(["uvicorn", " app.api.main:app --host 0.0.0.0 --port 8000"]),
]
executor_patterns = [
    "".join(["python3 -m", " app.executor.service"]),
]
worker_patterns = [
    "".join(["python3 -m", " app.executor.sensor_recorder_worker"]),
    "app.executor.sensor_recorder_worker",
]

terminate_patterns(api_patterns + executor_patterns + worker_patterns, timeout_seconds=10.0)

launch_env = load_launch_env(project_root)
launch_env["PYTHONDONTWRITEBYTECODE"] = "1"
launch_env["PYTHONUNBUFFERED"] = "1"

api_pid = spawn_process(
    [sys.executable, "-m", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"],
    project_root,
    launch_env,
    api_log_path,
)
executor_pid = spawn_process(
    [sys.executable, "-m", "app.executor.service"],
    project_root,
    launch_env,
    executor_log_path,
)

time.sleep(4)

running = {
    "api": find_matching_pids(api_patterns[0]) or find_matching_pids(api_patterns[1]),
    "executor": find_matching_pids(executor_patterns[0]),
}
if not running["api"]:
    raise RuntimeError("API process did not stay up after restart")
if not running["executor"]:
    raise RuntimeError("executor process did not stay up after restart")

print(
    json.dumps(
        {
            "requested": {"api_pid": api_pid, "executor_pid": executor_pid},
            "running": running,
        },
        ensure_ascii=False,
    )
)
PY
)"

  remote_container_bash "
set -euo pipefail
cd $(printf '%q' "$REMOTE_PROJECT_ROOT")
export DUCKPARK_REMOTE_PROJECT_ROOT=$(printf '%q' "$REMOTE_PROJECT_ROOT")
python3 - <<'PY'
${restart_script}
PY
"
}

ensure_remote_carla_ready() {
  remote_log "checking CARLA availability on ${REMOTE_HOST}:2000"
  if remote_host_bash "
python3 - <<'PY'
import socket
import sys

sock = socket.socket()
sock.settimeout(2.0)
try:
    sock.connect(('127.0.0.1', 2000))
except OSError:
    sys.exit(1)
finally:
    sock.close()

print('carla-port-ok')
PY
"; then
    return 0
  fi

  remote_log "CARLA not reachable; starting ~/startCarla.sh"
  remote_host_bash "
set -euo pipefail
bash ~/startCarla.sh
"

  remote_log "waiting for CARLA to accept connections"
  remote_host_bash "
python3 - <<'PY'
import socket
import sys
import time

deadline = time.time() + 90.0
last_error = None
while time.time() < deadline:
    sock = socket.socket()
    sock.settimeout(2.0)
    try:
        sock.connect(('127.0.0.1', 2000))
    except OSError as exc:
        last_error = exc
        time.sleep(1.0)
    else:
        print('carla-port-ok')
        sys.exit(0)
    finally:
        sock.close()

print(f'carla-port-not-ready: {last_error}')
sys.exit(1)
PY
"
}

run_remote_smoke() {
  local mode="$1"
  python3 "$PROJECT_ROOT/scripts/remote_smoke.py" --base-url "$REMOTE_API_BASE_URL" --mode "$mode"
}
