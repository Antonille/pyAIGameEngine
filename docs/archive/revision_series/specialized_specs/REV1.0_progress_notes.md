# pyAIGameEngine Progress Notes — REV 1.0 Addendum
**Date:** 2026-03-28

## POC1 implementation pass 0.0.8
- Added clearer comparison tooling for NumPy vs Numba runtime modes.
- Added `--json` and `--warmup-numba` support to benchmarking to make timing comparisons fairer and easier to parse.
- Began first concrete AI scheduling prototype structures:
  - `ModelFamilySpec`
  - `FreshnessSpec`
  - `FallbackPolicy`
  - `AIScheduler`
- Refined render-facing subset handling by moving visibility selection/snapshot assembly into `render/render_subset.py`.
- Preserved fallback-first architecture and kept PyBullet optional/deferred.

## 2026-03-28 full-snapshot refresh
- merged current sparse 0.0.8 code/doc changes into uploaded project snapshot
- refreshed project instructions/resource guide to REV1.4 / version 0.0.9
- added repo-ready field/runtime-schema/payload implementation spec
- refreshed GitHub/snapshot workflow docs and helper scripts
