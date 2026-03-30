from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..state.soa_state import SoAState


class PhysicsBackend(ABC):
    """Backend interface for physics simulation.

    The SoAState is the source of truth for base transforms/velocities.
    Backend owns its internal solver representation and must sync.
    """

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def rebuild_world_from_state(self, state: SoAState) -> None:
        """(Re)create backend bodies to match the current SoA alive set."""

    @abstractmethod
    def step(self, state: SoAState, dt: float) -> None:
        """Advance simulation by dt seconds and write results into state."""
