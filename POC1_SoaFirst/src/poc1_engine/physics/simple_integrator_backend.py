from __future__ import annotations

import numpy as np

from poc1_engine.kernels.numba.simple_integrate import integrate_numba, integrate_numpy


class SimpleIntegratorBackend:
    name = "simple_integrator"
    device = "cpu"

    def __init__(self, gravity=(0.0, -9.81, 0.0), linear_damping: float = 0.01, world_bounds=(-12.0, 12.0, 0.0, 12.0), mode: str = "numpy"):
        self.gravity = np.asarray(gravity, dtype=np.float32)
        self.linear_damping = float(linear_damping)
        self.world_bounds = world_bounds
        self.last_hit_wall = None
        self.mode = mode

    def connect(self) -> None:
        return None

    def disconnect(self) -> None:
        return None

    def warmup(self) -> None:
        if self.mode != "numba":
            return
        pos = np.zeros((8, 3), dtype=np.float32)
        linvel = np.zeros((8, 3), dtype=np.float32)
        force = np.zeros((8, 3), dtype=np.float32)
        inv_mass = np.ones((8,), dtype=np.float32)
        integrate_numba(pos, linvel, force, inv_mass, self.gravity, np.float32(1.0 / 120.0), np.float32(self.linear_damping))

    def step(self, state, dt: float) -> None:
        sl = state.live_slice()
        if state.body_count == 0:
            self.last_hit_wall = np.zeros(0, dtype=np.bool_)
            return

        pos = state.pos[sl]
        linvel = state.linvel[sl]
        force = state.force[sl]
        inv_mass = state.inv_mass[sl]

        if self.mode == "numba":
            integrate_numba(pos, linvel, force, inv_mass, self.gravity, np.float32(dt), np.float32(self.linear_damping))
        else:
            integrate_numpy(pos, linvel, force, inv_mass, self.gravity, np.float32(dt), np.float32(self.linear_damping))

        x_min, x_max, y_min, y_max = self.world_bounds
        low_x = pos[:, 0] < x_min
        high_x = pos[:, 0] > x_max
        low_y = pos[:, 1] < y_min
        high_y = pos[:, 1] > y_max
        hit_wall = low_x | high_x | low_y | high_y
        self.last_hit_wall = hit_wall.copy()

        if np.any(low_x):
            pos[low_x, 0] = x_min
            linvel[low_x, 0] *= -0.8
        if np.any(high_x):
            pos[high_x, 0] = x_max
            linvel[high_x, 0] *= -0.8
        if np.any(low_y):
            pos[low_y, 1] = y_min
            linvel[low_y, 1] *= -0.8
        if np.any(high_y):
            pos[high_y, 1] = y_max
            linvel[high_y, 1] *= -0.8
