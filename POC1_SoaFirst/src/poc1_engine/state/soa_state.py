from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SoAState:
    capacity: int
    action_dim: int = 4
    obs_dim: int = 24
    dtype: np.dtype = np.float32

    entity_id: np.ndarray | None = None
    alive: np.ndarray | None = None
    pos: np.ndarray | None = None
    rot: np.ndarray | None = None
    linvel: np.ndarray | None = None
    angvel: np.ndarray | None = None
    force: np.ndarray | None = None
    torque: np.ndarray | None = None
    inv_mass: np.ndarray | None = None
    inv_inertia_diag: np.ndarray | None = None
    shape_type: np.ndarray | None = None
    shape_param: np.ndarray | None = None
    render_enabled: np.ndarray | None = None
    mesh_id: np.ndarray | None = None
    material_id: np.ndarray | None = None
    scale: np.ndarray | None = None
    color: np.ndarray | None = None
    xform44_snapshot: np.ndarray | None = None
    render_visible: np.ndarray | None = None
    agent_active: np.ndarray | None = None
    agent_id: np.ndarray | None = None
    policy_id: np.ndarray | None = None
    team_id: np.ndarray | None = None
    reward_accum: np.ndarray | None = None
    action: np.ndarray | None = None
    action_mask: np.ndarray | None = None
    obs_buf: np.ndarray | None = None
    obs_index: np.ndarray | None = None
    body_count: int = 0

    SNAPSHOT_FIELDS = (
        "entity_id",
        "alive",
        "pos",
        "rot",
        "linvel",
        "angvel",
        "force",
        "torque",
        "inv_mass",
        "inv_inertia_diag",
        "shape_type",
        "shape_param",
        "render_enabled",
        "mesh_id",
        "material_id",
        "scale",
        "color",
        "xform44_snapshot",
        "render_visible",
        "agent_active",
        "agent_id",
        "policy_id",
        "team_id",
        "reward_accum",
        "action",
        "action_mask",
        "obs_buf",
        "obs_index",
    )

    @classmethod
    def create(cls, capacity: int, action_dim: int = 4, obs_dim: int = 24) -> "SoAState":
        s = cls(capacity=capacity, action_dim=action_dim, obs_dim=obs_dim)
        s.entity_id = np.arange(capacity, dtype=np.int32)
        s.alive = np.zeros(capacity, dtype=np.bool_)
        s.pos = np.zeros((capacity, 3), dtype=np.float32)
        s.rot = np.zeros((capacity, 4), dtype=np.float32)
        s.rot[:, 0] = 1.0
        s.linvel = np.zeros((capacity, 3), dtype=np.float32)
        s.angvel = np.zeros((capacity, 3), dtype=np.float32)
        s.force = np.zeros((capacity, 3), dtype=np.float32)
        s.torque = np.zeros((capacity, 3), dtype=np.float32)
        s.inv_mass = np.ones(capacity, dtype=np.float32)
        s.inv_inertia_diag = np.ones((capacity, 3), dtype=np.float32)
        s.shape_type = np.zeros(capacity, dtype=np.uint8)
        s.shape_param = np.zeros((capacity, 4), dtype=np.float32)
        s.render_enabled = np.zeros(capacity, dtype=np.uint8)
        s.mesh_id = np.zeros(capacity, dtype=np.int32)
        s.material_id = np.zeros(capacity, dtype=np.int32)
        s.scale = np.ones((capacity, 3), dtype=np.float32)
        s.color = np.ones((capacity, 4), dtype=np.float32)
        s.xform44_snapshot = np.zeros((capacity, 16), dtype=np.float32)
        s.render_visible = np.zeros(capacity, dtype=np.uint8)
        s.agent_active = np.zeros(capacity, dtype=np.uint8)
        s.agent_id = np.full(capacity, -1, dtype=np.int32)
        s.policy_id = np.zeros(capacity, dtype=np.int16)
        s.team_id = np.zeros(capacity, dtype=np.int16)
        s.reward_accum = np.zeros(capacity, dtype=np.float32)
        s.action = np.zeros((capacity, action_dim), dtype=np.float32)
        s.action_mask = np.ones((capacity, action_dim), dtype=np.uint8)
        s.obs_buf = np.zeros((capacity, obs_dim), dtype=np.float32)
        s.obs_index = np.arange(capacity, dtype=np.int32)
        return s

    def reset_runtime_buffers(self) -> None:
        self.force.fill(0.0)
        self.torque.fill(0.0)
        self.reward_accum.fill(0.0)
        self.action.fill(0.0)
        self.obs_buf.fill(0.0)

    def spawn_body(self, pos=(0.0, 0.0, 0.0), linvel=(0.0, 0.0, 0.0), shape_type=0, shape_param=(0.5, 0.0, 0.0, 0.0), render_enabled=True, is_agent=False, inv_mass=1.0) -> int:
        if self.body_count >= self.capacity:
            raise ValueError("SoAState capacity exhausted")
        i = self.body_count
        self.body_count += 1
        self.alive[i] = True
        self.pos[i] = np.asarray(pos, dtype=np.float32)
        self.linvel[i] = np.asarray(linvel, dtype=np.float32)
        self.shape_type[i] = np.uint8(shape_type)
        self.shape_param[i] = np.asarray(shape_param, dtype=np.float32)
        self.render_enabled[i] = 1 if render_enabled else 0
        self.render_visible[i] = self.render_enabled[i]
        self.agent_active[i] = 1 if is_agent else 0
        self.agent_id[i] = i if is_agent else -1
        self.inv_mass[i] = float(inv_mass)
        return i

    def live_slice(self) -> slice:
        return slice(0, self.body_count)

    def live_indices(self) -> np.ndarray:
        return np.arange(self.body_count, dtype=np.int32)

    def agent_indices(self) -> np.ndarray:
        sl = self.live_slice()
        return np.flatnonzero(self.agent_active[sl]).astype(np.int32)

    def build_observations_for(self, entity_indices: np.ndarray) -> np.ndarray:
        if entity_indices.size == 0:
            return np.zeros((0, self.obs_dim), dtype=np.float32)
        self.obs_buf[entity_indices].fill(0.0)
        self.obs_buf[entity_indices, 0:3] = self.pos[entity_indices]
        self.obs_buf[entity_indices, 3:6] = self.linvel[entity_indices]
        self.obs_buf[entity_indices, 6:10] = self.rot[entity_indices]
        self.obs_buf[entity_indices, 10:13] = self.angvel[entity_indices]
        self.obs_buf[entity_indices, 13:17] = self.shape_param[entity_indices]
        self.obs_buf[entity_indices, 17] = self.shape_type[entity_indices]
        self.obs_buf[entity_indices, 18] = self.render_enabled[entity_indices]
        self.obs_buf[entity_indices, 19] = self.agent_active[entity_indices]
        self.obs_buf[entity_indices, 20:24] = self.action[entity_indices, :4]
        return self.obs_buf[entity_indices]

    def update_render_visibility(self, view_x=(-10.0, 10.0), view_y=(-1.0, 10.0)) -> np.ndarray:
        sl = self.live_slice()
        self.render_visible[sl] = 0
        if self.body_count == 0:
            return np.zeros(0, dtype=np.int32)
        visible = (
            (self.render_enabled[sl] == 1)
            & (self.pos[sl, 0] >= view_x[0])
            & (self.pos[sl, 0] <= view_x[1])
            & (self.pos[sl, 1] >= view_y[0])
            & (self.pos[sl, 1] <= view_y[1])
        )
        self.render_visible[sl] = visible.astype(np.uint8)
        return np.flatnonzero(visible).astype(np.int32)

    def build_render_snapshot(self, visible_indices: np.ndarray | None = None) -> None:
        sl = self.live_slice()
        self.xform44_snapshot[sl].fill(0.0)
        if visible_indices is None:
            visible_indices = self.live_indices()
        if visible_indices.size == 0:
            return
        self.xform44_snapshot[visible_indices, 0] = self.scale[visible_indices, 0]
        self.xform44_snapshot[visible_indices, 5] = self.scale[visible_indices, 1]
        self.xform44_snapshot[visible_indices, 10] = self.scale[visible_indices, 2]
        self.xform44_snapshot[visible_indices, 12] = self.pos[visible_indices, 0]
        self.xform44_snapshot[visible_indices, 13] = self.pos[visible_indices, 1]
        self.xform44_snapshot[visible_indices, 14] = self.pos[visible_indices, 2]
        self.xform44_snapshot[visible_indices, 15] = 1.0

    def export_runtime_snapshot(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = {
            "capacity": int(self.capacity),
            "action_dim": int(self.action_dim),
            "obs_dim": int(self.obs_dim),
            "body_count": int(self.body_count),
        }
        for name in self.SNAPSHOT_FIELDS:
            value = getattr(self, name)
            if value is None:
                continue
            snapshot[name] = np.array(value, copy=True)
        return snapshot

    def restore_runtime_snapshot(self, snapshot: dict[str, Any]) -> None:
        if int(snapshot["capacity"]) != self.capacity:
            raise ValueError(f"Snapshot capacity {snapshot['capacity']} does not match state capacity {self.capacity}")
        if int(snapshot["action_dim"]) != self.action_dim:
            raise ValueError(f"Snapshot action_dim {snapshot['action_dim']} does not match state action_dim {self.action_dim}")
        if int(snapshot["obs_dim"]) != self.obs_dim:
            raise ValueError(f"Snapshot obs_dim {snapshot['obs_dim']} does not match state obs_dim {self.obs_dim}")
        self.body_count = int(snapshot["body_count"])
        for name in self.SNAPSHOT_FIELDS:
            if name not in snapshot:
                continue
            target = getattr(self, name)
            value = np.asarray(snapshot[name])
            if target is None:
                setattr(self, name, np.array(value, copy=True))
                continue
            if target.shape != value.shape:
                raise ValueError(f"Snapshot field {name} shape {value.shape} does not match target shape {target.shape}")
            target[...] = value
