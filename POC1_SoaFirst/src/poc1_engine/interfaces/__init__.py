"""Thin interface-facing stubs for role-based engine boundaries.

These modules are intentionally lightweight. They define the early contracts and
ownership boundaries for model developers, AI developers, and future UI developers
without committing the repo to a premature large package split.
"""

from .model_api import ModelArtifact, ModelRuntimeView, ScenarioBundle
from .ai_api import AIActionPacket, FeatureBlockContract, RewardSignalPacket
from .ui_api import ControlIntentPacket, RenderSnapshotView

__all__ = [
    "ModelArtifact",
    "ModelRuntimeView",
    "ScenarioBundle",
    "AIActionPacket",
    "FeatureBlockContract",
    "RewardSignalPacket",
    "ControlIntentPacket",
    "RenderSnapshotView",
]
