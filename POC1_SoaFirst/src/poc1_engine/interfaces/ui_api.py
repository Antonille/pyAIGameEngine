from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class RenderSnapshotView:
    """Future engine->UI contract.

    Intentionally small and presentation-oriented. This should evolve
    independently from solver internals.
    """

    visible_entity_indices: Sequence[int]
    transform_buffer_name: str = "xform44_snapshot"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ControlIntentPacket:
    """Future UI->engine control contract."""

    source: str
    command_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
