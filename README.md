# pyAIGameEngine

Revision: **0.0.24**  
Snapshot date: **2026-03-31**

pyAIGameEngine is a Python hybrid game engine / physics simulation engine project with modular AI components.
The current emphasis is fallback-first simulation correctness, AI/RL boundary hardening, reproducible testing/reporting,
and a GitHub-first workflow designed to reduce repo-truth drift, line-ending noise, and snapshot/apply confusion.

## Current status
- Active proof of concept: `POC1_SoaFirst`
- Python baseline: single Python 3.12 `.venv`
- Active validated runtime path: fallback-first CPU path
- Native physics: PyBullet optional / deferred
- Current workflow overlays:
  - lesson-action register
  - truth-tier discipline (`repo-truth` vs `snapshot-truth` vs `supporting local evidence`)
  - current-pointer freshness audit
  - full+sparse reconciliation audit before authoritative full snapshots
  - canonical environment-variable discipline for local automation
  - explicit line-ending policy (`.gitattributes` + renormalize workflow)

## Start here
1. Read `docs/README.md`
2. Read `docs/CURRENT_PROJECT_RESOURCE_GUIDE.md`
3. Read `docs/CURRENT_WORKFLOW.md`
4. Read `docs/CURRENT_GITHUB_WORKFLOW.md`
5. Read `docs/CURRENT_NEXT_STEP_PROMPTS.md`
6. Read `POC1_SoaFirst/README.md`

## Repository layout
- `docs/` — current pointers, active docs, archive index, and curated history
- `docs/archive/` — archived revision series and legacy folders consolidated out of the active surface
- `POC1_SoaFirst/` — isolated proof-of-concept package, reports, durable test artifacts, and source
- `scripts/` — install, validation, snapshot, and repo-maintenance helpers
- `tools/` — helper utilities and placeholders for shared tooling promotion
- `pocs/` — cross-POC index / planning space

## Repo-truth note
GitHub main now reflects the REV4.5 cleanup/consolidation promotion.
Future cleanup or snapshot passes must explicitly state whether they are operating against current `repo-truth`
or a bounded `snapshot-truth` candidate that has not yet been promoted.
