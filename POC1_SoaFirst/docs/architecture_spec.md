# POC1 Architecture Spec — PlankTick SoA BulletGL

This document is a **snapshot** of the POC1 architecture that we are scaffolding into code.

## Core principle
Keep the per-plank-tic update loop **data-oriented** and **backend-pluggable**:
- Core state in NumPy SoA buffers (contiguous, vectorizable)
- Physics hidden behind a `PhysicsBackend` interface
- Rendering reads from SoA buffers (no physics → render coupling)
- AI sees a clean observation/action interface (Gymnasium-compatible)

## High-level block flow (per plank-tic)

```
[Input] → [AI Policy] → [Action Buffer]
                 ↓
         [PhysicsBackend.step(dt)]
                 ↓
      [SoA State Updated In-Place]
                 ↓
   [Render Snapshot] → [Renderer.draw()]
```

### Where multithreading / vectorization will live
- **SoA transforms & bookkeeping:** NumPy vector ops / Numba kernels
- **Broadphase & contact candidates (future):** spatial hashing / BVH kernels (Numba / Warp / Taichi)
- **Narrowphase & solver (future):** GPU kernels or a dedicated backend (Warp/Taichi) for throughput mode
- **AI:** parallel policy eval (CPU threads or GPU batches) using stable observation tensors

## SoA buffers (initial)
- `pos[N,3]`, `vel[N,3]`, `quat[N,4]`, `ang_vel[N,3]` (float32)
- `shape_type[N]` (int8: 0=sphere, 1=box)
- `shape_param[N,4]` (float32: sphere radius in [0]; box half-extents in [0:3])
- `mass[N]`, `friction[N]`, `restitution[N]` (float32)
- `color[N,4]` (float32)
- `force_accum[N,3]` (float32) — cleared each step
- `alive[N]` (bool), `entity_id[N]` (int32)

## PhysicsBackend boundary
Backend is responsible for:
- consuming SoA state to build a physics world
- stepping the world
- pushing base transforms/velocities back into SoA state

Backend is *not* allowed to own “truth” for gameplay state. SoA remains source of truth.

## CPU ↔ GPU transfer decision (POC1)
- Render copies positions into uniforms; no persistent GPU-resident simulation buffers yet.
- Physics is CPU-based via PyBullet.
- GPU transfers are limited to rendering resources.

Future: introduce “kernel backends” that keep simulation buffers on GPU and only stage small readbacks for UI.

## Milestones (3 iterations)
1. **POC1a:** SoA + PyBullet step + viewer renders a few objects; benchmark prints ms/tick.
2. **POC1b:** Add Gymnasium wrapper and validate deterministic stepping + reset; add simple scripted AI.
3. **POC1c:** Introduce one accelerated kernel (e.g., SoA integration / force accumulation) via Numba; compare timings.

