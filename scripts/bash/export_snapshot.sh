#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-C:/PythonDev/Dev1/pyGames/pyAIGameEngine}"
REV="${2:-0.0.9}"
STAMP="$(date +%F_%H-%M)"
OUTDIR="$ROOT/snapshots_out"
TMPDIR="$(mktemp -d)"
mkdir -p "$OUTDIR"
mkdir -p "$TMPDIR/pyAIGameEngine"
rsync -a \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.mypy_cache' \
  --exclude '.ruff_cache' \
  --exclude '.git' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  --exclude '*.nbc' \
  --exclude '*.nbi' \
  --exclude '*.egg-info' \
  --exclude 'build' \
  --exclude 'dist' \
  --exclude 'snapshots_out' \
  "$ROOT/" "$TMPDIR/pyAIGameEngine/"
(
  cd "$TMPDIR"
  zip -r "$OUTDIR/pyAIGameEngine_Rev_${REV}_${STAMP}.zip" pyAIGameEngine >/dev/null
)
rm -rf "$TMPDIR"
echo "created_clean_snapshot=$OUTDIR/pyAIGameEngine_Rev_${REV}_${STAMP}.zip"
echo "snapshot_layout=standard-root-folder"
