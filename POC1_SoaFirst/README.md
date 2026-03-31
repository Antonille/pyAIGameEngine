Revision: **0.1.3**

# POC1 — SoA First Fallback Path

**Descriptive name:** *POC1_SoaFirst*  
**Goal:** Establish a performance-friendly architecture baseline using SoA runtime state, explicit plank-tic stages,
fallback-first execution, benchmark/rollout/viewer paths, and AI/RL boundary hardening without blocking on native physics.

## Current validated path
- **Default backend:** simple integrator
- **Backend modes:** `numpy`, `numba`
- **Optional backend:** PyBullet (deferred / non-blocking)
- **Rendering:** 2D-facing viewer with 3D coordinate/state structures preserved

## Current capabilities
- explicit plank-tic stage loop
- SoA runtime state buffers
- event buffer + queries
- agent-subset observation building
- benchmark, rollout, viewer
- render visibility selection / snapshot-culling precursor
- AI scheduling prototype structures:
  - `ModelFamilySpec`
  - `FreshnessSpec`
  - `FallbackPolicy`
  - `AIScheduler`
- NumPy vs Numba comparison tooling
- integrated testing/archive/report generation path
- deterministic replay check entry point

## Install (editable)
From repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install_project.ps1
```

## Validation
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windowsun_poc1_validation.ps1 -BackendMode numpy
powershell -ExecutionPolicy Bypass -File .\scripts\windowsun_poc1_validation.ps1 -BackendMode numba
powershell -ExecutionPolicy Bypass -File .\scripts\windowsun_poc1_integrated_tests.ps1
```

## Artifact/report policy
- `artifacts/test/archive/` and `artifacts/test/generated/runs/` hold durable history and run-linked artifacts.
- `reports/current/` holds the latest human-readable regenerated report surface and can be refreshed from durable data.

## Focus
This POC remains isolated until components have clear promotion criteria into shared engine layers.
