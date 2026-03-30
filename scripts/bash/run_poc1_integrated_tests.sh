#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYTHON_EXE="${PYTHON_EXE:-python}"
PYTHONPATH="$ROOT/POC1_SoaFirst/src${PYTHONPATH:+:$PYTHONPATH}" \
  "$PYTHON_EXE" "$ROOT/POC1_SoaFirst/scripts/run_integrated_tests.py" "$@"
