from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class FallbackPolicy(str, Enum):
    REUSE_LAST = "reuse_last"
    WAIT_UNTIL_DEADLINE = "wait_until_deadline"
    FALLBACK_DEFAULT = "fallback_default"


@dataclass(frozen=True)
class FreshnessSpec:
    max_input_staleness: int
    max_output_staleness: int


@dataclass(frozen=True)
class ModelFamilySpec:
    family_name: str
    source_family: str
    cadence_planktics: int
    freshness: FreshnessSpec
    stage_deadline: str
    fallback_policy: FallbackPolicy
    feature_blocks: Sequence[str] = field(default_factory=tuple)
    output_blocks: Sequence[str] = field(default_factory=tuple)
    preferred_batch_size: int = 256

    def due_this_cycle(self, cycle: int, last_run_cycle: int | None) -> bool:
        if last_run_cycle is None:
            return True
        return (cycle - last_run_cycle) >= self.cadence_planktics
