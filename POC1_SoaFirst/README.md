Revision: **0.1.15**

# POC1 — SoA First Fallback Path

**Descriptive name:** *POC1_SoaFirst*  
**Goal:** Establish a performance-friendly architecture baseline using SoA runtime state, explicit plank-tic stages,
fallback-first execution, benchmark/rollout/viewer paths, integrated testing/reporting, and AI/RL boundary hardening without blocking on native physics.

## Current validated path
- **Default backend:** simple integrator
- **Backend modes:** `numpy`, `numba`
- **Optional backend:** PyBullet (deferred / non-blocking)
- **Rendering:** 2D-facing viewer with 3D coordinate/state structures preserved

## Current capabilities
- explicit plank-tic stage loop
- SoA runtime state buffers
- event buffer + queries
- runtime-schema / feature-block / transfer-planning scaffolding
- startup-validated / startup-compiled configurable-interface groundwork slice
- benchmark, rollout, viewer
- integrated testing/archive/report generation path
- deterministic replay check entry point

## Current configurable-interface slice
- canonical manifest: `config/interfaces/agent_hot_control_manifest_v1.json`
- validator/compiler: `src/poc1_engine/interfaces/configurable_interface.py`
- local validation entry point: `scripts/validate_configurable_interface.py`
- current slice scope: one repeated-family hot observation/action subset compiled at startup into an immutable runtime plan
- explicit non-goal for this pass: replacing the authoritative hardcoded hot-path mapping

## Validation
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_poc1_validation.ps1 -BackendMode numpy
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_poc1_validation.ps1 -BackendMode numba
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_poc1_integrated_tests.ps1 -BackendMode numpy -SuiteGroup core
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_poc1_integrated_tests.ps1 -BackendMode numba -WarmupNumba -SuiteGroup core
.\.venv\Scripts\python.exe .\POC1_SoaFirst\scripts\validate_configurable_interface.py --emit-doc --output-json
```

## Artifact/report policy
- `artifacts/test/archive/` and `artifacts/test/generated/runs/` hold durable history and run-linked artifacts.
- `reports/current/` holds the latest human-readable regenerated report surface and can be refreshed from durable data.

## Focus
This POC remains isolated until components have clear promotion criteria into shared engine layers.
