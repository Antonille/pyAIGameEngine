from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from poc1_engine.physics.mass_properties import box_inertia_diag, box_mass, sphere_inertia_diag, sphere_mass


SHAPE_SPHERE = np.uint8(1)
SHAPE_BOX = np.uint8(2)


@dataclass
class RigidBodyStore:
    capacity: int
    count: int = 0

    body_id: np.ndarray | None = None
    entity_id: np.ndarray | None = None
    coord_system_id: np.ndarray | None = None
    body_local_cs_id: np.ndarray | None = None
    active: np.ndarray | None = None
    pos_cm_xyz: np.ndarray | None = None
    rot_quat: np.ndarray | None = None
    linvel_xyz: np.ndarray | None = None
    angvel_xyz: np.ndarray | None = None
    force_xyz: np.ndarray | None = None
    torque_xyz: np.ndarray | None = None
    mass: np.ndarray | None = None
    inv_mass: np.ndarray | None = None
    inertia_body_diag: np.ndarray | None = None
    inv_inertia_body_diag: np.ndarray | None = None
    shape_kind: np.ndarray | None = None
    radius: np.ndarray | None = None
    half_extents_xyz: np.ndarray | None = None
    field_source_handle: np.ndarray | None = None

    @classmethod
    def create(cls, capacity: int) -> 'RigidBodyStore':
        s = cls(capacity=capacity)
        s.body_id = np.arange(capacity, dtype=np.int32)
        s.entity_id = np.full(capacity, -1, dtype=np.int32)
        s.coord_system_id = np.zeros(capacity, dtype=np.int32)
        s.body_local_cs_id = np.full(capacity, -1, dtype=np.int32)
        s.active = np.zeros(capacity, dtype=np.bool_)
        s.pos_cm_xyz = np.zeros((capacity, 3), dtype=np.float32)
        s.rot_quat = np.zeros((capacity, 4), dtype=np.float32)
        s.rot_quat[:, 0] = 1.0
        s.linvel_xyz = np.zeros((capacity, 3), dtype=np.float32)
        s.angvel_xyz = np.zeros((capacity, 3), dtype=np.float32)
        s.force_xyz = np.zeros((capacity, 3), dtype=np.float32)
        s.torque_xyz = np.zeros((capacity, 3), dtype=np.float32)
        s.mass = np.ones(capacity, dtype=np.float32)
        s.inv_mass = np.ones(capacity, dtype=np.float32)
        s.inertia_body_diag = np.ones((capacity, 3), dtype=np.float32)
        s.inv_inertia_body_diag = np.ones((capacity, 3), dtype=np.float32)
        s.shape_kind = np.zeros(capacity, dtype=np.uint8)
        s.radius = np.zeros(capacity, dtype=np.float32)
        s.half_extents_xyz = np.zeros((capacity, 3), dtype=np.float32)
        s.field_source_handle = np.full(capacity, -1, dtype=np.int32)
        return s

    def live_slice(self) -> slice:
        return slice(0, self.count)

    def reset_accumulators(self) -> None:
        sl = self.live_slice()
        self.force_xyz[sl].fill(0.0)
        self.torque_xyz[sl].fill(0.0)

    def add_sphere(self, *, entity_id: int, coord_system_id: int, body_local_cs_id: int = -1,
                   pos_cm_xyz=(0.0, 0.0, 0.0), radius: float = 0.5, density: float = 1.0,
                   linvel_xyz=(0.0, 0.0, 0.0), angvel_xyz=(0.0, 0.0, 0.0), static: bool = False) -> int:
        if self.count >= self.capacity:
            raise ValueError('RigidBodyStore capacity exhausted')
        idx = self.count
        self.count += 1
        m = sphere_mass(radius, density)
        inertia = sphere_inertia_diag(m, radius)
        self._fill_common(idx, entity_id, coord_system_id, body_local_cs_id, pos_cm_xyz, linvel_xyz, angvel_xyz, m, inertia, static)
        self.shape_kind[idx] = SHAPE_SPHERE
        self.radius[idx] = float(radius)
        return idx

    def add_box(self, *, entity_id: int, coord_system_id: int, body_local_cs_id: int = -1,
                pos_cm_xyz=(0.0, 0.0, 0.0), half_extents_xyz=(0.5, 0.5, 0.5), density: float = 1.0,
                linvel_xyz=(0.0, 0.0, 0.0), angvel_xyz=(0.0, 0.0, 0.0), static: bool = False) -> int:
        if self.count >= self.capacity:
            raise ValueError('RigidBodyStore capacity exhausted')
        idx = self.count
        self.count += 1
        m = box_mass(half_extents_xyz, density)
        inertia = box_inertia_diag(m, half_extents_xyz)
        self._fill_common(idx, entity_id, coord_system_id, body_local_cs_id, pos_cm_xyz, linvel_xyz, angvel_xyz, m, inertia, static)
        self.shape_kind[idx] = SHAPE_BOX
        self.half_extents_xyz[idx] = np.asarray(half_extents_xyz, dtype=np.float32)
        return idx

    def _fill_common(self, idx: int, entity_id: int, coord_system_id: int, body_local_cs_id: int,
                     pos_cm_xyz, linvel_xyz, angvel_xyz, mass: float, inertia_diag: np.ndarray, static: bool) -> None:
        self.active[idx] = True
        self.entity_id[idx] = int(entity_id)
        self.coord_system_id[idx] = int(coord_system_id)
        self.body_local_cs_id[idx] = int(body_local_cs_id)
        self.pos_cm_xyz[idx] = np.asarray(pos_cm_xyz, dtype=np.float32)
        self.linvel_xyz[idx] = np.asarray(linvel_xyz, dtype=np.float32)
        self.angvel_xyz[idx] = np.asarray(angvel_xyz, dtype=np.float32)
        self.mass[idx] = float(mass)
        self.inertia_body_diag[idx] = np.asarray(inertia_diag, dtype=np.float32)
        if static:
            self.inv_mass[idx] = 0.0
            self.inv_inertia_body_diag[idx].fill(0.0)
        else:
            self.inv_mass[idx] = 0.0 if mass <= 1e-8 else (1.0 / float(mass))
            self.inv_inertia_body_diag[idx] = np.where(self.inertia_body_diag[idx] > 1e-8, 1.0 / self.inertia_body_diag[idx], 0.0)
