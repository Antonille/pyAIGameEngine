Revision: **0.1.2**

# POC1 — SoA First Fallback Path

**Descriptive name:** *POC1_SoaFirst*  
**Goal:** Establish a high-performance-friendly architecture baseline using SoA runtime state, explicit plank-tic stages, fallback-first execution, benchmark/rollout/viewer paths, and performance exploration without blocking on native physics.

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

## Install (editable)
From repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install_project.ps1
```

## Validation
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windowsun_poc1_validation.ps1 -BackendMode numpy
powershell -ExecutionPolicy Bypass -File .\scripts\windowsun_poc1_validation.ps1 -BackendMode numba
```

## Focus
This POC remains isolated until components have clear promotion criteria into shared engine layers.
