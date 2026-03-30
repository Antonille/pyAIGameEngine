from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from poc1_engine.ai.feature_blocks import FeatureBlockRegistry, FeaturePackPlan, FeaturePackRegistry
from poc1_engine.ai.scheduler import ScheduleDecision
from poc1_engine.runtime.runtime_schema import RuntimeSchemaRegistry


@dataclass(frozen=True)
class TransferBatchPlan:
    family_name: str
    runtime_family: str
    batch_index: int
    entity_indices: np.ndarray
    feature_blocks: tuple[str, ...]
    output_blocks: tuple[str, ...]
    feature_width: int
    preferred_batch_size: int
    cadence_planktics: int
    stage_deadline: str
    fallback_policy: str
    max_input_staleness: int
    max_output_staleness: int

    @property
    def entity_count(self) -> int:
        return int(self.entity_indices.size)

    @property
    def staging_shape(self) -> tuple[int, int]:
        return (self.entity_count, self.feature_width)


@dataclass
class FamilyTransferPlan:
    family_name: str
    runtime_family: str
    entity_indices: np.ndarray
    feature_pack: FeaturePackPlan
    stage_deadline: str
    fallback_policy: str
    cadence_planktics: int
    max_input_staleness: int
    max_output_staleness: int
    batches: list[TransferBatchPlan] = field(default_factory=list)

    @property
    def entity_count(self) -> int:
        return int(self.entity_indices.size)


class TransferPlanner:
    """Prototype planner that turns scheduling decisions into batchable transfer groups."""

    def __init__(
        self,
        runtime_schemas: RuntimeSchemaRegistry,
        feature_blocks: FeatureBlockRegistry,
        feature_packs: FeaturePackRegistry,
    ):
        self.runtime_schemas = runtime_schemas
        self.feature_blocks = feature_blocks
        self.feature_packs = feature_packs

    def plan_cycle(self, schedule_decisions: Sequence[ScheduleDecision]) -> list[FamilyTransferPlan]:
        plans: list[FamilyTransferPlan] = []
        for decision in schedule_decisions:
            feature_pack = self.feature_packs.get(decision.family_name)
            runtime_schema = self.runtime_schemas.get(feature_pack.runtime_family)
            entity_indices = np.asarray(decision.entity_indices, dtype=np.int32)
            plan = FamilyTransferPlan(
                family_name=decision.family_name,
                runtime_family=runtime_schema.family_name,
                entity_indices=entity_indices,
                feature_pack=feature_pack,
                stage_deadline=decision.stage_deadline,
                fallback_policy=decision.fallback_policy,
                cadence_planktics=decision.cadence_planktics,
                max_input_staleness=decision.max_input_staleness,
                max_output_staleness=decision.max_output_staleness,
            )
            batch_size = max(int(decision.preferred_batch_size), 1)
            for batch_index, start in enumerate(range(0, entity_indices.size, batch_size)):
                batch_indices = entity_indices[start : start + batch_size]
                plan.batches.append(
                    TransferBatchPlan(
                        family_name=decision.family_name,
                        runtime_family=runtime_schema.family_name,
                        batch_index=batch_index,
                        entity_indices=batch_indices,
                        feature_blocks=tuple(feature_pack.feature_blocks),
                        output_blocks=tuple(feature_pack.output_blocks),
                        feature_width=feature_pack.total_feature_width,
                        preferred_batch_size=batch_size,
                        cadence_planktics=decision.cadence_planktics,
                        stage_deadline=decision.stage_deadline,
                        fallback_policy=decision.fallback_policy,
                        max_input_staleness=decision.max_input_staleness,
                        max_output_staleness=decision.max_output_staleness,
                    )
                )
            plans.append(plan)
        return plans

    def build_staging_buffer(self, state, batch: TransferBatchPlan) -> np.ndarray:
        return self.feature_blocks.extract_concat(state, batch.entity_indices, batch.feature_blocks)

    def materialize_cycle(self, state, family_plans: Sequence[FamilyTransferPlan]) -> dict[str, int]:
        summary = {
            "family_count": 0,
            "batch_count": 0,
            "entity_count": 0,
            "feature_width_total": 0,
            "float32_values_total": 0,
            "bytes_total": 0,
        }
        for family_plan in family_plans:
            summary["family_count"] += 1
            summary["entity_count"] += family_plan.entity_count
            for batch in family_plan.batches:
                staging = self.build_staging_buffer(state, batch)
                summary["batch_count"] += 1
                summary["feature_width_total"] += batch.feature_width
                summary["float32_values_total"] += int(staging.size)
                summary["bytes_total"] += int(staging.nbytes)
        return summary


def summarize_transfer_plans(plans: Sequence[FamilyTransferPlan]) -> list[str]:
    lines: list[str] = []
    for plan in plans:
        lines.append(
            "family={family} runtime_family={runtime} entities={entities} batches={batches} "
            "feature_blocks={blocks} feature_width={width} cadence={cadence} "
            "input_staleness<={input_stale} output_staleness<={output_stale} deadline={deadline} fallback={fallback}".format(
                family=plan.family_name,
                runtime=plan.runtime_family,
                entities=plan.entity_count,
                batches=len(plan.batches),
                blocks=list(plan.feature_pack.feature_blocks),
                width=plan.feature_pack.total_feature_width,
                cadence=plan.cadence_planktics,
                input_stale=plan.max_input_staleness,
                output_stale=plan.max_output_staleness,
                deadline=plan.stage_deadline,
                fallback=plan.fallback_policy,
            )
        )
    return lines
