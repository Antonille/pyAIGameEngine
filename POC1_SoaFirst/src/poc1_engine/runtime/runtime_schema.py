from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class RuntimeFieldSpec:
    """One field intentionally tracked in a repeated-family runtime schema."""

    field_name: str
    width: int
    dtype: str
    semantics: str
    hot_path: bool = True
    sparse_handle: bool = False


@dataclass(frozen=True)
class RepeatedObjectFamilyRuntimeSchema:
    """Describes the fixed runtime layout for one repeated object family.

    This is intentionally a schema/contract object, not the storage itself.
    The current POC storage remains CPU-authoritative SoA state.
    """

    family_name: str
    index_method_name: str
    active_mask_field: str
    hot_fields: tuple[RuntimeFieldSpec, ...] = field(default_factory=tuple)
    sparse_handle_fields: tuple[RuntimeFieldSpec, ...] = field(default_factory=tuple)
    metadata: Mapping[str, str] = field(default_factory=dict)

    @property
    def total_hot_width(self) -> int:
        return sum(field.width for field in self.hot_fields)

    @property
    def total_sparse_width(self) -> int:
        return sum(field.width for field in self.sparse_handle_fields)

    def eligible_indices(self, state) -> np.ndarray:
        selector = getattr(state, self.index_method_name)
        indices = selector()
        return np.asarray(indices, dtype=np.int32)

    def field_specs_by_name(self) -> dict[str, RuntimeFieldSpec]:
        combined = self.hot_fields + self.sparse_handle_fields
        return {field.field_name: field for field in combined}


@dataclass
class RuntimeSchemaRegistry:
    family_schemas: dict[str, RepeatedObjectFamilyRuntimeSchema]

    def get(self, family_name: str) -> RepeatedObjectFamilyRuntimeSchema:
        return self.family_schemas[family_name]


AGENT_HOT_FIELDS: tuple[RuntimeFieldSpec, ...] = (
    RuntimeFieldSpec("pos", 3, "float32", "world position xyz"),
    RuntimeFieldSpec("linvel", 3, "float32", "world linear velocity xyz"),
    RuntimeFieldSpec("rot", 4, "float32", "rotation quaternion wxyz"),
    RuntimeFieldSpec("angvel", 3, "float32", "world angular velocity xyz"),
    RuntimeFieldSpec("action", 4, "float32", "last action buffer"),
    RuntimeFieldSpec("reward_accum", 1, "float32", "engine-side accumulated reward"),
    RuntimeFieldSpec("team_id", 1, "int16", "team/group membership id"),
    RuntimeFieldSpec("policy_id", 1, "int16", "model/policy selection id"),
    RuntimeFieldSpec("alive", 1, "bool", "entity liveness flag"),
    RuntimeFieldSpec("render_visible", 1, "uint8", "last render visibility bit"),
    RuntimeFieldSpec("inv_mass", 1, "float32", "inverse mass"),
    RuntimeFieldSpec("shape_type", 1, "uint8", "coarse shape enum"),
    RuntimeFieldSpec("shape_param", 4, "float32", "coarse shape parameters"),
)

AGENT_SPARSE_HANDLE_FIELDS: tuple[RuntimeFieldSpec, ...] = (
    RuntimeFieldSpec("mesh_id", 1, "int32", "optional mesh/presentation handle", hot_path=False, sparse_handle=True),
    RuntimeFieldSpec("material_id", 1, "int32", "optional material/property handle", hot_path=False, sparse_handle=True),
)


def build_agent_family_runtime_schema() -> RepeatedObjectFamilyRuntimeSchema:
    return RepeatedObjectFamilyRuntimeSchema(
        family_name="agent_family",
        index_method_name="agent_indices",
        active_mask_field="agent_active",
        hot_fields=AGENT_HOT_FIELDS,
        sparse_handle_fields=AGENT_SPARSE_HANDLE_FIELDS,
        metadata={
            "storage_owner": "SoAState",
            "authority": "cpu_authoritative",
            "runtime_path": "fallback_first",
        },
    )


def build_default_runtime_schema_registry() -> RuntimeSchemaRegistry:
    agent_schema = build_agent_family_runtime_schema()
    return RuntimeSchemaRegistry({agent_schema.family_name: agent_schema})
