# pyAIGameEngine

Revision: **0.0.10**  
Snapshot date: **2026-03-29**

pyAIGameEngine is a Python hybrid game engine / physics simulation engine project with modular AI components. The current phase is early architecture definition, field/runtime-schema planning, AI scheduling architecture work, and Proof of Concept 1 (**POC1_SoaFirst**) implementation/performance exploration.

## Current status
- Active proof of concept: **POC1_SoaFirst**
- Python baseline: **single Python 3.12 `.venv`**
- Active validated runtime path: **fallback-first CPU path**
- Native physics: **PyBullet optional / deferred**
- POC1 currently includes:
  - explicit plank-tic stage loop
  - SoA runtime state buffers
  - event buffer and event queries
  - agent-subset observation building
  - simple integrator backend with **NumPy / Numba** runtime modes
  - benchmark, rollout, viewer
  - per-stage timing/profiling
  - render visibility selection / snapshot-culling precursor
  - first AI scheduling prototype structures
- Current architecture direction also includes:
  - fixed runtime schemas and feature-pack plans for repeated object families
  - AI scheduling by model family, cadence, freshness, and fallback policy
  - new coordinate-system / gravity / field / property architecture spec and runtime-schema/field-payload prototype plan

## Repository layout
- `docs/` — project-wide specs, workflow, status, prompts, lessons learned, manifests, current-truth guides
- `POC1_SoaFirst/` — isolated proof-of-concept package and docs
- `scripts/` — root-level install, repo, snapshot, validation, and packaging scripts
- `tools/` — helper utilities and placeholders for cross-POC tooling
- `pocs/` — proof-of-concept index and future shared promotion notes

## Start here
1. Read `docs/CURRENT_PROJECT_RESOURCE_GUIDE.md`
2. Read `docs/CURRENT_PROJECT_INSTRUCTIONS.md`
3. Run `scripts/windows/install_project.ps1`
4. Validate POC1 with `scripts/windows/run_poc1_validation.ps1 -BackendMode numpy`
5. Use `docs/CURRENT_NEXT_STEP_PROMPTS.md` for ready-to-paste next prompts


## Current primary architecture spec
- `docs/2026 03 29 REV1.5 Rigid-Body, Field, and Runtime-Schema Implementation Spec.md`
