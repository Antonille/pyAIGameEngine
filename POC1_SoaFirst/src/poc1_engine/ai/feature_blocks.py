from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np

from poc1_engine.interfaces.ai_api import FeatureBlockContract
from poc1_engine.runtime.runtime_schema import RepeatedObjectFamilyRuntimeSchema, RuntimeSchemaRegistry


def _field_to_2d_float32(state, field_name: str, entity_indices: np.ndarray) -> np.ndarray:
    values = getattr(state, field_name)[entity_indices]
    values = np.asarray(values)
    if values.ndim == 1:
        values = values.reshape(-1, 1)
    return values.astype(np.float32, copy=False)


@dataclass(frozen=True)
class FeatureBlockSchema:
    """Schema + extractor contract for one AI-visible feature block."""

    block_name: str
    runtime_family: str
    field_names: tuple[str, ...]
    contract: FeatureBlockContract

    def extract(self, state, entity_indices: np.ndarray) -> np.ndarray:
        if entity_indices.size == 0:
            return np.zeros((0, self.contract.width), dtype=np.float32)
        columns = [_field_to_2d_float32(state, name, entity_indices) for name in self.field_names]
        result = np.concatenate(columns, axis=1)
        if result.shape[1] != self.contract.width:
            raise ValueError(
                f"Feature block {self.block_name} width mismatch: "
                f"expected {self.contract.width}, built {result.shape[1]}"
            )
        return result


@dataclass
class FeatureBlockRegistry:
    runtime_schemas: RuntimeSchemaRegistry
    blocks: dict[str, FeatureBlockSchema] = field(default_factory=dict)

    def register(self, block: FeatureBlockSchema) -> None:
        runtime_schema = self.runtime_schemas.get(block.runtime_family)
        valid_names = runtime_schema.field_specs_by_name()
        missing = [name for name in block.field_names if name not in valid_names]
        if missing:
            raise KeyError(f"Unknown runtime fields for block {block.block_name}: {missing}")
        self.blocks[block.block_name] = block

    def get(self, block_name: str) -> FeatureBlockSchema:
        return self.blocks[block_name]

    def extract_concat(self, state, entity_indices: np.ndarray, block_names: Sequence[str]) -> np.ndarray:
        if not block_names:
            return np.zeros((entity_indices.size, 0), dtype=np.float32)
        mats = [self.get(name).extract(state, entity_indices) for name in block_names]
        return np.concatenate(mats, axis=1) if mats else np.zeros((entity_indices.size, 0), dtype=np.float32)

    def combined_width(self, block_names: Sequence[str]) -> int:
        return sum(self.get(name).contract.width for name in block_names)


@dataclass(frozen=True)
class FeaturePackPlan:
    """Maps one model family to the feature blocks it consumes."""

    model_family: str
    runtime_family: str
    feature_blocks: tuple[str, ...]
    output_blocks: tuple[str, ...]
    preferred_batch_size: int
    total_feature_width: int


@dataclass
class FeaturePackRegistry:
    feature_blocks: FeatureBlockRegistry
    packs: dict[str, FeaturePackPlan] = field(default_factory=dict)

    def register(self, plan: FeaturePackPlan) -> None:
        for block_name in plan.feature_blocks:
            self.feature_blocks.get(block_name)
        self.packs[plan.model_family] = plan

    def get(self, model_family: str) -> FeaturePackPlan:
        return self.packs[model_family]


def _width_for_fields(runtime_schema: RepeatedObjectFamilyRuntimeSchema, field_names: Iterable[str]) -> int:
    field_specs = runtime_schema.field_specs_by_name()
    return sum(field_specs[name].width for name in field_names)


KINEMATICS_FIELDS = ("pos", "linvel", "rot", "angvel")
STATUS_FIELDS = ("alive", "render_visible", "team_id", "policy_id", "reward_accum", "inv_mass")
ACTION_CONTEXT_FIELDS = ("action", "shape_type", "shape_param")
SPARSE_HANDLE_FIELDS = ("mesh_id", "material_id")
POLICY_IDENTITY_FIELDS = ("team_id", "policy_id")


def build_default_feature_block_registry(runtime_schemas: RuntimeSchemaRegistry) -> FeatureBlockRegistry:
    registry = FeatureBlockRegistry(runtime_schemas=runtime_schemas)
    agent_schema = runtime_schemas.get("agent_family")

    registry.register(
        FeatureBlockSchema(
            block_name="kinematics_local_v1",
            runtime_family="agent_family",
            field_names=KINEMATICS_FIELDS,
            contract=FeatureBlockContract(
                block_name="kinematics_local_v1",
                width=_width_for_fields(agent_schema, KINEMATICS_FIELDS),
                dtype="float32",
                semantics="agent-local kinematics subset from fallback SoA state",
                freshness_policy="cadence_aligned",
            ),
        )
    )
    registry.register(
        FeatureBlockSchema(
            block_name="status_local_v1",
            runtime_family="agent_family",
            field_names=STATUS_FIELDS,
            contract=FeatureBlockContract(
                block_name="status_local_v1",
                width=_width_for_fields(agent_schema, STATUS_FIELDS),
                dtype="float32",
                semantics="status/reward/team/policy subset from fallback SoA state",
                freshness_policy="reuse_last",
            ),
        )
    )
    registry.register(
        FeatureBlockSchema(
            block_name="action_context_v1",
            runtime_family="agent_family",
            field_names=ACTION_CONTEXT_FIELDS,
            contract=FeatureBlockContract(
                block_name="action_context_v1",
                width=_width_for_fields(agent_schema, ACTION_CONTEXT_FIELDS),
                dtype="float32",
                semantics="last action plus coarse shape context",
                freshness_policy="reuse_last",
            ),
        )
    )
    registry.register(
        FeatureBlockSchema(
            block_name="sparse_handle_refs_v1",
            runtime_family="agent_family",
            field_names=SPARSE_HANDLE_FIELDS,
            contract=FeatureBlockContract(
                block_name="sparse_handle_refs_v1",
                width=_width_for_fields(agent_schema, SPARSE_HANDLE_FIELDS),
                dtype="float32",
                semantics="optional sparse mesh/material handles for secondary lookup",
                freshness_policy="static_or_slow",
            ),
        )
    )
    registry.register(
        FeatureBlockSchema(
            block_name="policy_identity_v1",
            runtime_family="agent_family",
            field_names=POLICY_IDENTITY_FIELDS,
            contract=FeatureBlockContract(
                block_name="policy_identity_v1",
                width=_width_for_fields(agent_schema, POLICY_IDENTITY_FIELDS),
                dtype="float32",
                semantics="stable policy/team identity block for packet-cache experiments",
                freshness_policy="static_or_slow",
            ),
        )
    )
    return registry


def build_default_feature_pack_registry(feature_blocks: FeatureBlockRegistry) -> FeaturePackRegistry:
    registry = FeaturePackRegistry(feature_blocks=feature_blocks)
    reflex_blocks = ("kinematics_local_v1", "status_local_v1")
    registry.register(
        FeaturePackPlan(
            model_family="agent_reflex_v1",
            runtime_family="agent_family",
            feature_blocks=reflex_blocks,
            output_blocks=("action4_v1",),
            preferred_batch_size=128,
            total_feature_width=feature_blocks.combined_width(reflex_blocks),
        )
    )
    contextual_blocks = (
        "kinematics_local_v1",
        "status_local_v1",
        "action_context_v1",
        "sparse_handle_refs_v1",
    )
    registry.register(
        FeaturePackPlan(
            model_family="agent_contextual_v1",
            runtime_family="agent_family",
            feature_blocks=contextual_blocks,
            output_blocks=("action4_delta_v1",),
            preferred_batch_size=64,
            total_feature_width=feature_blocks.combined_width(contextual_blocks),
        )
    )
    hold_blocks = ("policy_identity_v1",)
    registry.register(
        FeaturePackPlan(
            model_family="agent_hold_v1",
            runtime_family="agent_family",
            feature_blocks=hold_blocks,
            output_blocks=("action4_hold_v1",),
            preferred_batch_size=96,
            total_feature_width=feature_blocks.combined_width(hold_blocks),
        )
    )
    cleanup_blocks = ("policy_identity_v1", "sparse_handle_refs_v1")
    registry.register(
        FeaturePackPlan(
            model_family="agent_cleanup_v1",
            runtime_family="agent_family",
            feature_blocks=cleanup_blocks,
            output_blocks=("action4_delete_v1",),
            preferred_batch_size=96,
            total_feature_width=feature_blocks.combined_width(cleanup_blocks),
        )
    )
    return registry
