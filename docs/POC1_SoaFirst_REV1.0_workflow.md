# POC1_SoaFirst Workflow — REV 1.0 Addendum
**Date:** 2026-03-28

## Current local validation commands
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_poc1_validation.ps1 -BackendMode numpy
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_poc1_validation.ps1 -BackendMode numba
.\.venv\Scripts\python.exe .\POC1_SoaFirst\scripts\run_benchmark.py --steps 2000 --bodies 1024 --backend-mode numpy
.\.venv\Scripts\python.exe .\POC1_SoaFirst\scripts\run_benchmark.py --steps 2000 --bodies 1024 --backend-mode numba --warmup-numba
.\.venv\Scripts\python.exe .\POC1_SoaFirst\scripts\compare_backend_modes.py --steps 2000 --bodies 1024 --warmup-numba
.\.venv\Scripts\python.exe .\POC1_SoaFirst\scripts\run_gym_rollout.py --steps 256 --backend-mode numpy
.\.venv\Scripts\python.exe .\POC1_SoaFirst\scripts\run_gym_rollout.py --steps 256 --backend-mode numba
.\.venv\Scripts\python.exe .\POC1_SoaFirst\scripts\run_viewer.py
```
