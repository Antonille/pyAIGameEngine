from __future__ import annotations

import numpy as np

from poc1_engine.fields.field_source_store import FS_GRAVITY_LIKE


def apply_center_of_mass_field_coupling(rigid_bodies, coord_systems, field_sources):
    rigid_bodies.reset_accumulators()
    sl = rigid_bodies.live_slice()
    if rigid_bodies.count == 0:
        return {'ambient_targets': 0, 'source_target_pairs': 0}

    # ambient gravity from coordinate systems
    for cs_id in np.unique(rigid_bodies.coord_system_id[sl]):
        mask = rigid_bodies.coord_system_id[sl] == cs_id
        idx = np.flatnonzero(mask)
        if idx.size == 0:
            continue
        masses = rigid_bodies.mass[idx][:, None]
        g = coord_systems.gravity_local_xyz[int(cs_id)][None, :]
        rigid_bodies.force_xyz[idx] += masses * g

    pair_count = 0
    # prototype gravity-like point-source field
    for src_idx in range(field_sources.count):
        if not field_sources.active[src_idx]:
            continue
        if (field_sources.field_mask[src_idx] & FS_GRAVITY_LIKE) == 0:
            continue
        owner = int(field_sources.owner_body_id[src_idx])
        if owner < 0 or owner >= rigid_bodies.count:
            continue
        src_pos = rigid_bodies.pos_cm_xyz[owner]
        strength = float(field_sources.gravity_like_strength[src_idx])
        cutoff_sq = float(field_sources.cutoff_radius[src_idx]) ** 2

        delta = rigid_bodies.pos_cm_xyz[sl] - src_pos[None, :]
        dist_sq = np.einsum('ij,ij->i', delta, delta)
        valid = (dist_sq > 1e-8) & (dist_sq <= cutoff_sq)
        target_idx = np.flatnonzero(valid)
        if target_idx.size == 0:
            continue
        r = np.sqrt(dist_sq[target_idx])
        inv_r3 = 1.0 / np.maximum(r * r * r, 1e-8)
        masses = rigid_bodies.mass[target_idx]
        forces = (-strength * masses)[:, None] * delta[target_idx] * inv_r3[:, None]
        rigid_bodies.force_xyz[target_idx] += forces.astype(np.float32)
        pair_count += int(target_idx.size)

    return {'ambient_targets': int(rigid_bodies.count), 'source_target_pairs': pair_count}
