from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Dict, Optional


@dataclass
class StageTimer:
    """Tiny timing utility for plank-tic cycle breakdown."""

    totals: Dict[str, float] = field(default_factory=dict)
    counts: Dict[str, int] = field(default_factory=dict)

    def reset(self) -> None:
        self.totals.clear()
        self.counts.clear()

    def add(self, name: str, dt: float) -> None:
        self.totals[name] = self.totals.get(name, 0.0) + float(dt)
        self.counts[name] = self.counts.get(name, 0) + 1

    def stats(self) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for k, total in self.totals.items():
            n = max(1, self.counts.get(k, 1))
            out[k] = {
                "total_s": total,
                "count": float(n),
                "avg_ms": 1000.0 * total / n,
            }
        return out


class timed:
    """Context manager for StageTimer."""

    def __init__(self, timer: StageTimer, name: str):
        self.timer = timer
        self.name = name
        self.t0: Optional[float] = None

    def __enter__(self):
        self.t0 = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        t1 = perf_counter()
        assert self.t0 is not None
        self.timer.add(self.name, t1 - self.t0)
        return False
