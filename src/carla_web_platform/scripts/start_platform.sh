#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)

export PROJECT_ROOT
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

python3 -m app.executor.service &
EXECUTOR_PID=$!

cleanup() {
  if kill -0 "${EXECUTOR_PID}" >/dev/null 2>&1; then
    kill "${EXECUTOR_PID}" || true
  fi
}

trap cleanup EXIT INT TERM

exec uvicorn app.api.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}"
