from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np

from ..core.planktic import PlankClock
from ..physics.backend import PhysicsBackend
from ..state.soa_state import SoAState
from .timing import StageTimer, timed


@dataclass
class BenchmarkResult:
    steps: int
    n_bodies: int
    total_s: float
    avg_ms_per_step: float
    stage_stats: dict


def run_headless_benchmark(
    backend: PhysicsBackend,
    state: SoAState,
    steps: int = 5000,
    clock: PlankClock = PlankClock(240),
) -> BenchmarkResult:
    timer = StageTimer()

    backend.connect()
    with timed(timer, "rebuild_world"):
        backend.rebuild_world_from_state(state)

    dt = clock.dt_seconds
    t0 = perf_counter()
    for _ in range(int(steps)):
        with timed(timer, "physics_step"):
            backend.step(state, dt)
    total = perf_counter() - t0

    n_alive = int(state.alive.sum())
    return BenchmarkResult(
        steps=int(steps),
        n_bodies=n_alive,
        total_s=float(total),
        avg_ms_per_step=1000.0 * float(total) / float(steps),
        stage_stats=timer.stats(),
    )
