#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
LOG_FILE="${LOG_FILE:-/tmp/duckpark-platform.log}"

cd "${PROJECT_ROOT}"
nohup bash scripts/start_platform.sh "$@" >"${LOG_FILE}" 2>&1 &

echo "duckpark platform started in background"
echo "pid=$!"
echo "log=${LOG_FILE}"
