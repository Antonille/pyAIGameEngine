from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from poc1_engine.ai.model_family import ModelFamilySpec


@dataclass
class FamilyRuntimeRecord:
    last_run_cycle: int | None = None
    last_input_cycle: int | None = None
    last_output_cycle: int | None = None


@dataclass
class ScheduleDecision:
    family_name: str
    source_family: str
    entity_indices: np.ndarray
    feature_blocks: tuple[str, ...]
    output_blocks: tuple[str, ...]
    cadence_planktics: int
    stage_deadline: str
    fallback_policy: str
    preferred_batch_size: int
    max_input_staleness: int
    max_output_staleness: int


class AIScheduler:
    def __init__(self, family_specs: Iterable[ModelFamilySpec]):
        self.family_specs = {spec.family_name: spec for spec in family_specs}
        self.runtime = {name: FamilyRuntimeRecord() for name in self.family_specs}

    def plan_cycle(self, cycle: int, entity_index_map: dict[str, np.ndarray]) -> list[ScheduleDecision]:
        decisions: list[ScheduleDecision] = []
        for name, spec in self.family_specs.items():
            runtime = self.runtime[name]
            candidates = entity_index_map.get(spec.source_family, np.zeros(0, dtype=np.int32))
            if candidates.size == 0:
                continue
            if not spec.due_this_cycle(cycle, runtime.last_run_cycle):
                continue
            decisions.append(
                ScheduleDecision(
                    family_name=name,
                    source_family=spec.source_family,
                    entity_indices=candidates.astype(np.int32, copy=False),
                    feature_blocks=tuple(spec.feature_blocks),
                    output_blocks=tuple(spec.output_blocks),
                    cadence_planktics=spec.cadence_planktics,
                    stage_deadline=spec.stage_deadline,
                    fallback_policy=spec.fallback_policy.value,
                    preferred_batch_size=spec.preferred_batch_size,
                    max_input_staleness=spec.freshness.max_input_staleness,
                    max_output_staleness=spec.freshness.max_output_staleness,
                )
            )
        return decisions

    def mark_family_started(self, family_name: str, cycle: int) -> None:
        self.runtime[family_name].last_run_cycle = cycle
        self.runtime[family_name].last_input_cycle = cycle

    def mark_family_completed(self, family_name: str, cycle: int) -> None:
        self.runtime[family_name].last_output_cycle = cycle
