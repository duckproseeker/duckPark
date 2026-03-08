#!/usr/bin/env bash
set -euo pipefail

pkill -f "uvicorn app.api.main:app" >/dev/null 2>&1 || true
pkill -f "python3 -m app.executor.service" >/dev/null 2>&1 || true

echo "duckpark platform stopped"
