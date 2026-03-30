from __future__ import annotations

import argparse
import time
import numpy as np

from poc1_engine.kernels.numba.simple_integrate import integrate_numba, integrate_numpy


def make_arrays(n: int):
    rng = np.random.default_rng(321)
    pos = rng.uniform(-5.0, 5.0, size=(n, 3)).astype(np.float32)
    linvel = rng.uniform(-1.0, 1.0, size=(n, 3)).astype(np.float32)
    force = rng.uniform(-0.25, 0.25, size=(n, 3)).astype(np.float32)
    inv_mass = rng.uniform(0.5, 1.5, size=(n,)).astype(np.float32)
    gravity = np.asarray((0.0, -9.81, 0.0), dtype=np.float32)
    return pos, linvel, force, inv_mass, gravity


def main() -> int:
    parser = argparse.ArgumentParser(description="POC1 NumPy vs Numba simple integrator experiment")
    parser.add_argument("--bodies", type=int, default=20000)
    parser.add_argument("--steps", type=int, default=400)
    args = parser.parse_args()

    dt = np.float32(1.0 / 120.0)
    linear_damping = np.float32(0.01)

    pos_n, vel_n, force_n, inv_mass_n, gravity = make_arrays(args.bodies)
    pos_j, vel_j, force_j, inv_mass_j, gravity_j = make_arrays(args.bodies)

    # Warm-up JIT
    integrate_numba(pos_j[:8].copy(), vel_j[:8].copy(), force_j[:8].copy(), inv_mass_j[:8].copy(), gravity_j, dt, linear_damping)

    t0 = time.perf_counter()
    for _ in range(args.steps):
        integrate_numpy(pos_n, vel_n, force_n, inv_mass_n, gravity, dt, linear_damping)
    numpy_elapsed = time.perf_counter() - t0

    t1 = time.perf_counter()
    for _ in range(args.steps):
        integrate_numba(pos_j, vel_j, force_j, inv_mass_j, gravity_j, dt, linear_damping)
    numba_elapsed = time.perf_counter() - t1

    print(f"bodies={args.bodies}")
    print(f"steps={args.steps}")
    print(f"numpy_elapsed_s={numpy_elapsed:.6f}")
    print(f"numba_elapsed_s={numba_elapsed:.6f}")
    print(f"numpy_ms_per_step={(numpy_elapsed / args.steps) * 1000.0:.6f}")
    print(f"numba_ms_per_step={(numba_elapsed / args.steps) * 1000.0:.6f}")
    if numba_elapsed > 0:
        print(f"speedup={(numpy_elapsed / numba_elapsed):.3f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
