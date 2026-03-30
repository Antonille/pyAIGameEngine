from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class FeatureBlockContract:
    """Describes a block of engine state intentionally exposed to AI code."""

    block_name: str
    width: int
    dtype: str = "float32"
    semantics: str = ""
    freshness_policy: str = "reuse_last"


@dataclass(frozen=True)
class AIActionPacket:
    """Versioned AI->engine action/result handoff.

    The packet boundary is intentionally contract-facing. It carries ownership and
    baseline metadata needed to reason about packet reuse, invalidation, delete,
    and delta behavior without exposing raw solver internals.
    """

    protocol_version: str
    actor_family: str
    actor_indices: Sequence[int]
    action_block_name: str
    payload: Sequence[Sequence[float]]
    source_model_family: str = ""
    generated_cycle: int | None = None
    generation_id: int | None = None
    baseline_generation_id: int | None = None
    baseline_ownership_key: str = ""
    supersedes_generation_id: int | None = None
    supersedes_ownership_key: str = ""
    ownership_scope: str = ""
    ownership_key: str = ""
    apply_mode: str = "replace"
    stage_deadline: str = "action_application"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RewardSignalPacket:
    """Engine->AI objective/event packet.

    Current architecture direction: hybrid reward handling.
    Engine exposes canonical objective/event signals.
    AI backends may compose or shape rewards from those signals.
    """

    objective_id: str
    event_name: str
    scalar: float
    metadata: Mapping[str, Any] = field(default_factory=dict)
