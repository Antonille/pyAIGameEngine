from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ModelArtifact:
    """Serializable model-side asset or definition handle.

    Examples:
    - geometry definition bundle
    - property/material bundle
    - actor archetype bundle
    - objective/scenario bundle
    """

    artifact_id: str
    artifact_type: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioBundle:
    """Top-level model-developer handoff into the engine.

    This is a thin contract, not the final implementation format.
    """

    scenario_id: str
    coordinate_systems: Sequence[ModelArtifact] = field(default_factory=tuple)
    geometry_assets: Sequence[ModelArtifact] = field(default_factory=tuple)
    actor_assets: Sequence[ModelArtifact] = field(default_factory=tuple)
    objective_assets: Sequence[ModelArtifact] = field(default_factory=tuple)
    initial_conditions: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelRuntimeView:
    """Subset of engine state intentionally exposed back to model tooling.

    The model developer should not need direct access to solver internals.
    """

    scenario_id: str
    entity_count: int
    coordinate_system_count: int
    diagnostics: Mapping[str, Any] = field(default_factory=dict)
