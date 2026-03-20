#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
HIL_RUNTIME_ROOT=$(cd -- "${SCRIPT_DIR}/../.." && pwd)
SRC_ROOT="${DUCKPARK_SRC_ROOT:-$(cd -- "${HIL_RUNTIME_ROOT}/.." && pwd)}"
PROJECT_ROOT="${DUCKPARK_PLATFORM_ROOT:-${SRC_ROOT}/carla_web_platform}"

DETECTOR_COMMAND="${JETSON_DETECTOR_COMMAND:-}"
METRICS_FILE="${JETSON_METRICS_FILE:-$HOME/duckpark_non_ros_metrics.json}"
MODEL_NAME="${JETSON_MODEL_NAME:-tensorrt_detector}"
RESULT_URL="${JETSON_RESULT_URL:-http://192.168.50.1:18765/dut-results}"
RESULT_FILE="${JETSON_RESULT_FILE:-$HOME/duckpark_non_ros_result.json}"
CAMERA_DEVICE="${JETSON_CAMERA_DEVICE:-}"
SOURCE_HOST="${JETSON_SOURCE_HOST:-$(hostname)}"
RUN_ID="${JETSON_RUN_ID:-}"
INPUT_ENDPOINT="${JETSON_INPUT_ENDPOINT:-udp://0.0.0.0:5000}"
OUTPUT_ENDPOINT="${JETSON_OUTPUT_ENDPOINT:-http_push}"
TEGRASTATS_COMMAND="${JETSON_TEGRASTATS_COMMAND:-tegrastats --interval 1000}"
RESULT_TIMEOUT_SECONDS="${JETSON_RESULT_TIMEOUT_SECONDS:-2}"
RESULT_MAX_RETRIES="${JETSON_RESULT_MAX_RETRIES:-3}"
RESULT_RETRY_BACKOFF_SECONDS="${JETSON_RESULT_RETRY_BACKOFF_SECONDS:-1}"
POLL_INTERVAL_SECONDS="${JETSON_METRICS_POLL_INTERVAL_SECONDS:-0.2}"

usage() {
  cat <<'EOF'
Usage:
  JETSON_DETECTOR_COMMAND='/path/to/non_ros_detector --metrics-file ...' \
  bash hil_runtime/jetson/scripts/start_jetson_non_ros_demo.sh

Notes:
  - This script assumes the detector itself handles RTP ingest, TensorRT inference, and local display.
  - The detector should periodically write JSON metrics to JETSON_METRICS_FILE.
  - Metrics are posted to the Pi using the existing /dut-results payload contract.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ -z "${DETECTOR_COMMAND}" ]]; then
  echo "JETSON_DETECTOR_COMMAND is required" >&2
  exit 1
fi

export PROJECT_ROOT
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

DETECTOR_PID=""
METRICS_PID=""

cleanup() {
  local exit_code=$?
  if [[ -n "${DETECTOR_PID}" ]] && kill -0 "${DETECTOR_PID}" >/dev/null 2>&1; then
    kill "${DETECTOR_PID}" >/dev/null 2>&1 || true
    wait "${DETECTOR_PID}" 2>/dev/null || true
  fi
  if [[ -n "${METRICS_PID}" ]] && kill -0 "${METRICS_PID}" >/dev/null 2>&1; then
    kill -INT "${METRICS_PID}" >/dev/null 2>&1 || true
    wait "${METRICS_PID}" 2>/dev/null || true
  fi
  exit "${exit_code}"
}
trap cleanup EXIT INT TERM

mkdir -p "$(dirname "${METRICS_FILE}")"
rm -f "${METRICS_FILE}"

echo "Jetson non-ROS demo configuration:"
echo "  detector_command: ${DETECTOR_COMMAND}"
echo "  metrics_file: ${METRICS_FILE}"
echo "  model_name: ${MODEL_NAME}"
echo "  input_endpoint: ${INPUT_ENDPOINT}"
echo "  output_endpoint: ${OUTPUT_ENDPOINT}"
echo "  result_url: ${RESULT_URL:-<disabled>}"

echo "Starting detector"
bash -lc "${DETECTOR_COMMAND}" &
DETECTOR_PID=$!
sleep 1

echo "Starting metrics reporter"
python3 "${SCRIPT_DIR}/jetson_non_ros_metrics.py" \
  --metrics-file "${METRICS_FILE}" \
  --model-name "${MODEL_NAME}" \
  --camera-device "${CAMERA_DEVICE}" \
  --run-id "${RUN_ID}" \
  --source-host "${SOURCE_HOST}" \
  --input-topic "${INPUT_ENDPOINT}" \
  --output-topic "${OUTPUT_ENDPOINT}" \
  --result-url "${RESULT_URL}" \
  --result-file "${RESULT_FILE}" \
  --tegrastats-command "${TEGRASTATS_COMMAND}" \
  --result-timeout-seconds "${RESULT_TIMEOUT_SECONDS}" \
  --result-max-retries "${RESULT_MAX_RETRIES}" \
  --result-retry-backoff-seconds "${RESULT_RETRY_BACKOFF_SECONDS}" \
  --poll-interval-seconds "${POLL_INTERVAL_SECONDS}" &
METRICS_PID=$!

wait "${DETECTOR_PID}"
