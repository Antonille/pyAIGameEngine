from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlankClock:
    """Converts between clock seconds and plank-tics.

    In engine terms:
    - plank-tic = smallest unit of sim time (integer tick)
    - frame rate = plank-tics per real second

    POC1 uses a fixed dt = 1 / tics_per_second seconds per tick.
    """

    tics_per_second: int = 240

    @property
    def dt_seconds(self) -> float:
        return 1.0 / float(self.tics_per_second)

    def seconds_to_tics(self, seconds: float) -> int:
        return int(round(seconds * self.tics_per_second))

    def tics_to_seconds(self, tics: int) -> float:
        return float(tics) / float(self.tics_per_second)
