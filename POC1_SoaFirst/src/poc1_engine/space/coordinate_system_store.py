from __future__ import annotations

from dataclasses import dataclass
import numpy as np


CSF_ACTIVE = np.uint32(1 << 0)
CSF_SIMULATION_FRAME = np.uint32(1 << 1)
CSF_BODY_LOCAL = np.uint32(1 << 2)
CSF_DIRTY = np.uint32(1 << 3)


def _normalize_quat(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=np.float32)
    n = float(np.linalg.norm(q))
    if n <= 1e-8:
        return np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    return (q / n).astype(np.float32)


def quat_to_rotmat(q: np.ndarray) -> np.ndarray:
    w, x, y, z = _normalize_quat(q)
    return np.asarray([
        [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
        [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
        [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
    ], dtype=np.float32)


@dataclass
class CoordinateSystemStore:
    capacity: int
    master_gravity_xyz: np.ndarray
    gravity_revision: int = 0
    constants_revision: int = 0
    count: int = 0

    coord_system_id: np.ndarray | None = None
    parent_id: np.ndarray | None = None
    flags: np.ndarray | None = None
    transform_revision: np.ndarray | None = None
    inherited_field_revision: np.ndarray | None = None
    parent_field_revision_seen: np.ndarray | None = None
    parent_transform_revision_seen: np.ndarray | None = None
    pos_parent_xyz: np.ndarray | None = None
    rot_parent_quat: np.ndarray | None = None
    R_parent_to_local: np.ndarray | None = None
    R_local_to_parent: np.ndarray | None = None
    gravity_local_xyz: np.ndarray | None = None
    static_field_atlas_id: np.ndarray | None = None

    @classmethod
    def create(cls, capacity: int, master_gravity=(0.0, -9.81, 0.0)) -> 'CoordinateSystemStore':
        store = cls(capacity=capacity, master_gravity_xyz=np.asarray(master_gravity, dtype=np.float32))
        store.coord_system_id = np.arange(capacity, dtype=np.int32)
        store.parent_id = np.full(capacity, -1, dtype=np.int32)
        store.flags = np.zeros(capacity, dtype=np.uint32)
        store.transform_revision = np.zeros(capacity, dtype=np.uint32)
        store.inherited_field_revision = np.zeros(capacity, dtype=np.uint32)
        store.parent_field_revision_seen = np.zeros(capacity, dtype=np.uint32)
        store.parent_transform_revision_seen = np.zeros(capacity, dtype=np.uint32)
        store.pos_parent_xyz = np.zeros((capacity, 3), dtype=np.float32)
        store.rot_parent_quat = np.zeros((capacity, 4), dtype=np.float32)
        store.rot_parent_quat[:, 0] = 1.0
        store.R_parent_to_local = np.zeros((capacity, 3, 3), dtype=np.float32)
        store.R_local_to_parent = np.zeros((capacity, 3, 3), dtype=np.float32)
        store.gravity_local_xyz = np.zeros((capacity, 3), dtype=np.float32)
        store.static_field_atlas_id = np.full(capacity, -1, dtype=np.int32)
        for i in range(capacity):
            store.R_parent_to_local[i] = np.eye(3, dtype=np.float32)
            store.R_local_to_parent[i] = np.eye(3, dtype=np.float32)
        # master system at slot 0
        store.count = 1
        store.flags[0] = CSF_ACTIVE | CSF_SIMULATION_FRAME
        store.gravity_local_xyz[0] = store.master_gravity_xyz
        store.inherited_field_revision[0] = 1
        return store

    def add_system(self, parent_id: int = 0, *, simulation_frame: bool = True, body_local: bool = False,
                   pos_parent=(0.0, 0.0, 0.0), rot_parent_quat=(1.0, 0.0, 0.0, 0.0)) -> int:
        if self.count >= self.capacity:
            raise ValueError('CoordinateSystemStore capacity exhausted')
        idx = self.count
        self.count += 1
        self.parent_id[idx] = int(parent_id)
        flags = CSF_ACTIVE
        if simulation_frame:
            flags |= CSF_SIMULATION_FRAME
        if body_local:
            flags |= CSF_BODY_LOCAL
        self.flags[idx] = flags | CSF_DIRTY
        self.set_local_transform(idx, pos_parent=pos_parent, rot_parent_quat=rot_parent_quat, mark_dirty=False)
        self.propagate_inherited_fields()
        return idx

    def set_master_gravity(self, gravity_xyz) -> None:
        self.master_gravity_xyz = np.asarray(gravity_xyz, dtype=np.float32)
        self.gravity_revision += 1
        self.gravity_local_xyz[0] = self.master_gravity_xyz
        self.inherited_field_revision[0] += 1
        if self.count > 1:
            self.flags[1:self.count] |= CSF_DIRTY

    def set_local_transform(self, coord_system_id: int, *, pos_parent=(0.0, 0.0, 0.0), rot_parent_quat=(1.0, 0.0, 0.0, 0.0), mark_dirty: bool = True) -> None:
        idx = int(coord_system_id)
        self.pos_parent_xyz[idx] = np.asarray(pos_parent, dtype=np.float32)
        q = _normalize_quat(np.asarray(rot_parent_quat, dtype=np.float32))
        self.rot_parent_quat[idx] = q
        R = quat_to_rotmat(q)
        self.R_parent_to_local[idx] = R
        self.R_local_to_parent[idx] = R.T
        self.transform_revision[idx] += 1
        if mark_dirty:
            self.flags[idx] |= CSF_DIRTY

    def propagate_inherited_fields(self) -> int:
        updates = 0
        if self.count == 0:
            return updates
        self.gravity_local_xyz[0] = self.master_gravity_xyz
        for idx in range(1, self.count):
            parent = int(self.parent_id[idx])
            needs_update = bool(
                (self.flags[idx] & CSF_DIRTY) != 0
                or self.parent_field_revision_seen[idx] != self.inherited_field_revision[parent]
                or self.parent_transform_revision_seen[idx] != self.transform_revision[idx]
            )
            if not needs_update:
                continue
            self.gravity_local_xyz[idx] = self.R_parent_to_local[idx] @ self.gravity_local_xyz[parent]
            self.parent_field_revision_seen[idx] = self.inherited_field_revision[parent]
            self.parent_transform_revision_seen[idx] = self.transform_revision[idx]
            self.inherited_field_revision[idx] += 1
            self.flags[idx] &= ~CSF_DIRTY
            updates += 1
        return updates
