# pyAIGameEngine

Revision: **0.0.25**  
Snapshot date: **2026-03-31**

pyAIGameEngine is a Python hybrid game engine / physics simulation engine project with modular AI components.
The current emphasis is fallback-first simulation correctness, integrated testing/reporting, AI/RL boundary hardening,
and a startup-compiled configurable-interface groundwork slice that does not disturb the hot-path runtime.

## Current status
- Active proof of concept: `POC1_SoaFirst`
- Python baseline: single Python 3.12 `.venv`
- Active validated runtime path: fallback-first CPU path
- Native physics: PyBullet optional / deferred
- Current configurable-interface status:
  - canonical manifest added for the first bounded hot control-plane slice
  - startup validation + startup compilation into an immutable runtime plan
  - existing hardcoded hot-path mapping intentionally preserved for now

## Start here
1. Read `docs/README.md`
2. Read `docs/CURRENT_PROJECT_RESOURCE_GUIDE.md`
3. Read `docs/CURRENT_WORKFLOW.md`
4. Read `docs/CURRENT_CONFIGURABLE_INTERFACE_CONTROL.md`
5. Read `docs/CURRENT_TEST_REPORT_PROCEDURE.md`
6. Read `docs/CURRENT_NEXT_STEP_PROMPTS.md`
7. Read `POC1_SoaFirst/README.md`

## Repository layout
- `docs/` — current pointers, active docs, research notes, archive index, and curated history
- `docs/research/` — architecture/research inputs that inform current boundary decisions
- `POC1_SoaFirst/` — isolated proof-of-concept package, reports, durable test artifacts, source, and interface manifest
- `scripts/` — install, validation, snapshot, and repo-maintenance helpers
- `tools/` — helper utilities and placeholders for shared tooling promotion
- `pocs/` — cross-POC index / planning space
