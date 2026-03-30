#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
python3.12 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ./POC1_SoaFirst
python -m pip install numpy pyglet moderngl gymnasium numba pybullet torch torchvision torchaudio
python -c "import numpy,pyglet,moderngl,gymnasium,numba,pybullet,torch; print('All baseline imports passed.')"
echo "Install pass complete."
