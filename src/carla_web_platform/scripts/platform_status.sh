#!/usr/bin/env bash
set -euo pipefail

API_PORT="${API_PORT:-8000}"

echo "[processes]"
ps -ef | grep -E "uvicorn app.api.main:app|python3 -m app.executor.service" | grep -v grep || true
echo

echo "[healthz]"
curl -s "http://127.0.0.1:${API_PORT}/healthz" || true
echo
echo

echo "[system-status]"
curl -s "http://127.0.0.1:${API_PORT}/system/status" || true
echo
