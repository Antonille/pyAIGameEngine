from __future__ import annotations

from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass, field
import time
from typing import Any


@dataclass
class StageProfiler:
    totals: OrderedDict[str, float] = field(default_factory=OrderedDict)
    counts: OrderedDict[str, int] = field(default_factory=OrderedDict)

    @contextmanager
    def measure(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.totals[name] = self.totals.get(name, 0.0) + elapsed
            self.counts[name] = self.counts.get(name, 0) + 1

    def summary_lines(self) -> list[str]:
        lines = []
        for name, total in self.totals.items():
            count = self.counts.get(name, 1)
            avg_ms = (total / max(count, 1)) * 1000.0
            lines.append(f"{name}: total_s={total:.6f} avg_ms={avg_ms:.6f} count={count}")
        return lines

    def summary_dict(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for name, total in self.totals.items():
            count = self.counts.get(name, 1)
            result[name] = {
                "total_s": float(total),
                "avg_ms": float((total / max(count, 1)) * 1000.0),
                "count": int(count),
            }
        return result

    def reset(self) -> None:
        self.totals.clear()
        self.counts.clear()
