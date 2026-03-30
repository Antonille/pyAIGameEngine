from __future__ import annotations

from dataclasses import dataclass
import numpy as np


FS_GRAVITY_LIKE = np.uint32(1 << 0)
FS_STATIC = np.uint32(1 << 1)
FS_DYNAMIC = np.uint32(1 << 2)


@dataclass
class FieldSourceStore:
    capacity: int
    count: int = 0

    source_id: np.ndarray | None = None
    owner_body_id: np.ndarray | None = None
    coord_system_id: np.ndarray | None = None
    field_mask: np.ndarray | None = None
    gravity_like_strength: np.ndarray | None = None
    cutoff_radius: np.ndarray | None = None
    active: np.ndarray | None = None

    @classmethod
    def create(cls, capacity: int) -> 'FieldSourceStore':
        s = cls(capacity=capacity)
        s.source_id = np.arange(capacity, dtype=np.int32)
        s.owner_body_id = np.full(capacity, -1, dtype=np.int32)
        s.coord_system_id = np.zeros(capacity, dtype=np.int32)
        s.field_mask = np.zeros(capacity, dtype=np.uint32)
        s.gravity_like_strength = np.zeros(capacity, dtype=np.float32)
        s.cutoff_radius = np.zeros(capacity, dtype=np.float32)
        s.active = np.zeros(capacity, dtype=np.bool_)
        return s

    def add_gravity_source(self, *, owner_body_id: int, coord_system_id: int, strength: float, cutoff_radius: float, dynamic: bool = False) -> int:
        if self.count >= self.capacity:
            raise ValueError('FieldSourceStore capacity exhausted')
        idx = self.count
        self.count += 1
        self.active[idx] = True
        self.owner_body_id[idx] = int(owner_body_id)
        self.coord_system_id[idx] = int(coord_system_id)
        self.gravity_like_strength[idx] = float(strength)
        self.cutoff_radius[idx] = float(cutoff_radius)
        mask = FS_GRAVITY_LIKE | (FS_DYNAMIC if dynamic else FS_STATIC)
        self.field_mask[idx] = np.uint32(mask)
        return idx
