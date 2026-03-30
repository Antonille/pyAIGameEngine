from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def integrate_numba(pos, linvel, force, inv_mass, gravity, dt, linear_damping):
    n = pos.shape[0]
    for i in range(n):
        for j in range(3):
            accel = force[i, j] * inv_mass[i] + gravity[j]
            linvel[i, j] += accel * dt
            linvel[i, j] *= (1.0 - linear_damping)
            pos[i, j] += linvel[i, j] * dt
            force[i, j] = 0.0


def integrate_numpy(pos, linvel, force, inv_mass, gravity, dt, linear_damping):
    accel = force * inv_mass[:, None] + gravity[None, :]
    linvel += accel * dt
    linvel *= (1.0 - linear_damping)
    pos += linvel * dt
    force.fill(0.0)
