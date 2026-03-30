# ADR 0001 — POC1 stack: SoA + PyBullet + pyglet/ModernGL + Gymnasium

- Date: 2026-03-25
- Status: Accepted (POC scope)

## Context
We need an early architecture that:
- supports very fast per-plank-tic updates
- preserves headroom for AI compute
- is modular and swap-friendly (backends can change)

## Decision
For POC1 we adopt:
- **NumPy SoA** for core state buffers
- **PyBullet** as an initial PhysicsBackend implementation (CPU)
- **pyglet + ModernGL** for rendering (simple, controllable pipeline)
- **Gymnasium** wrapper for a standard observation/action API
- **Python 3.12.x** as the current local baseline interpreter line

## Rationale
- SoA buffers are immediately vectorizable and can migrate to Numba/Warp/Taichi later.
- PyBullet is a mature “do not build this yet” option for rigid-body simulation and collision detection.
- pyglet provides windowing/input; ModernGL offers a leaner OpenGL interface and is performance-friendly.
- Python 3.12 currently offers a cleaner compatibility baseline for the chosen package set than Python 3.14.

## Consequences / tradeoffs
- The local project intentionally stays on Python 3.12 for now instead of the newest interpreter line.
- Rendering in POC1 is not instanced; this is acceptable for correctness-first benchmarking.
- CPU↔GPU transfers remain render-only in POC1; physics stays CPU.

## Follow-ups
- Revisit newer Python baselines only after package compatibility is no longer a recurring friction point.
- Add a “kernel backend” experiment (Numba) for at least one stage to validate migration path.
