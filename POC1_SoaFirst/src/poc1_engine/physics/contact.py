from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class ContactPoint:
    body_a: int
    body_b: int
    point_world: np.ndarray
    normal_world: np.ndarray
    penetration_depth: float
    ra_world: np.ndarray | None = None
    rb_world: np.ndarray | None = None
    accumulated_normal_impulse: float = 0.0
    accumulated_tangent_impulse: float = 0.0


@dataclass
class ContactManifold:
    body_a: int
    body_b: int
    contacts: list[ContactPoint] = field(default_factory=list)
    manifold_kind: str = 'generic'

    def add_contact(self, contact: ContactPoint) -> None:
        self.contacts.append(contact)

    @property
    def contact_count(self) -> int:
        return len(self.contacts)
