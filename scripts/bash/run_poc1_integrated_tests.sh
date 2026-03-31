#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYTHON_EXE="${PYTHON_EXE:-python}"

HAS_LOG_PATH=0
for arg in "$@"; do
  if [[ "$arg" == "--console-log-path" ]]; then
    HAS_LOG_PATH=1
    break
  fi
done

ARGS=("$@")
if [[ "$HAS_LOG_PATH" -eq 0 ]]; then
  LOGS_ROOT="$ROOT/POC1_SoaFirst/artifacts/test/generated/console_logs"
  mkdir -p "$LOGS_ROOT"
  TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  CONSOLE_LOG_PATH="$LOGS_ROOT/integrated_tests_${TIMESTAMP}.log"
  echo "console_log_path=$CONSOLE_LOG_PATH"
  ARGS+=("--console-log-path" "$CONSOLE_LOG_PATH")
fi

PYTHONPATH="$ROOT/POC1_SoaFirst/src${PYTHONPATH:+:$PYTHONPATH}"   "$PYTHON_EXE" "$ROOT/POC1_SoaFirst/scripts/run_integrated_tests.py" "${ARGS[@]}"
