from __future__ import annotations

import numpy as np

from ..state.soa_state import SoAState


def make_demo_world(state: SoAState, n_bodies: int = 64, seed: int = 0) -> None:
    rng = np.random.default_rng(seed)

    # Ground
    state.spawn_box(half_extents=(20.0, 20.0, 0.25), position=(0.0, 0.0, -0.25), mass=0.0, color_rgba=(0.3, 0.3, 0.35, 1.0))

    for i in range(int(n_bodies)):
        if i % 2 == 0:
            r = float(rng.uniform(0.12, 0.35))
            x, y = rng.uniform(-4.0, 4.0, size=2)
            z = float(rng.uniform(1.0, 6.0))
            state.spawn_sphere(radius=r, position=(float(x), float(y), z), mass=1.0)
        else:
            hx, hy, hz = rng.uniform(0.15, 0.45, size=3)
            x, y = rng.uniform(-4.0, 4.0, size=2)
            z = float(rng.uniform(1.0, 6.0))
            state.spawn_box(half_extents=(float(hx), float(hy), float(hz)), position=(float(x), float(y), z), mass=1.0)
