from __future__ import annotations

import importlib.util
import time
from pathlib import Path
from typing import Any

import numpy as np

from poc1_engine.ai.action_bridge import build_default_action_bridge
from poc1_engine.ai.gate_d_acceptance import build_scheduler, build_transfer_planner, seed_state
from poc1_engine.ai.transfer_planner import summarize_transfer_plans
from poc1_engine.engine.loop import EngineConfig, EngineLoop
from poc1_engine.fields.coupling import apply_center_of_mass_field_coupling
from poc1_engine.fields.field_source_store import FieldSourceStore
from poc1_engine.physics.contact import ContactManifold, ContactPoint
from poc1_engine.physics.simple_integrator_backend import SimpleIntegratorBackend
from poc1_engine.runtime.rigid_body_store import RigidBodyStore
from poc1_engine.space.coordinate_system_store import CoordinateSystemStore
from poc1_engine.state.event_buffer import EventBuffer
from poc1_engine.state.soa_state import SoAState


def parse_stage_lines(lines: list[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for line in lines:
        if not line.startswith("stage::"):
            continue
        tail = line[len("stage::") :]
        name, rest = tail.split(": ", 1)
        parts = dict(item.split("=") for item in rest.split(" "))
        result[name] = float(parts["avg_ms"])
    return result


def capture_headless_benchmark(*, steps: int, bodies: int, backend_mode: str, warmup_numba: bool) -> tuple[dict[str, Any], SoAState]:
    state = SoAState.create(capacity=bodies)
    seed_state(state)
    backend = SimpleIntegratorBackend(mode=backend_mode)
    if warmup_numba:
        backend.warmup()
    backend.connect()

    scheduler = build_scheduler()
    transfer_planner = build_transfer_planner()
    action_bridge = build_default_action_bridge()
    loop = EngineLoop(
        state=state,
        backend=backend,
        config=EngineConfig(dt=1.0 / 120.0),
        ai_scheduler=scheduler,
        transfer_planner=transfer_planner,
        action_bridge=action_bridge,
    )

    start = time.perf_counter()
    loop.run_steps(steps)
    elapsed = time.perf_counter() - start
    stage_lines = loop.stage_summary_lines()
    stage_avg_ms = parse_stage_lines([f"stage::{line}" for line in stage_lines])
    cache_hits = int(loop.cumulative_action_packet_summary["cache_hits"])
    cache_misses = int(loop.cumulative_action_packet_summary["cache_misses"])
    reuse_ratio = (cache_hits / (cache_hits + cache_misses)) if (cache_hits + cache_misses) else 0.0

    payload = {
        "backend": f"{backend.name}:{backend.mode}",
        "backend_mode": backend.mode,
        "steps": int(steps),
        "bodies": int(bodies),
        "elapsed_s": float(elapsed),
        "ms_per_step": float((elapsed / steps) * 1000.0),
        "events": dict(loop.last_event_summary),
        "agent_obs_shape": list(loop.last_agent_obs.shape),
        "visible_count": int(loop.last_visible_indices.size),
        "hit_ground_query_count": int(loop.query_events(EventBuffer.EVENT_HIT_GROUND).size),
        "scheduled_families": sorted(loop.ai_schedule_counts.keys()),
        "schedule_counts": dict(loop.ai_schedule_counts),
        "transfer_batches": int(loop.cumulative_ai_transfer_summary["batch_count"]),
        "transfer_entities": int(loop.cumulative_ai_transfer_summary["entity_count"]),
        "transfer_bytes": int(loop.cumulative_ai_transfer_summary["bytes_total"]),
        "action_packets": int(loop.cumulative_action_packet_summary["packet_count"]),
        "action_packet_entities": int(loop.cumulative_action_packet_summary["entity_count"]),
        "action_packet_bytes": int(loop.cumulative_action_packet_summary["bytes_total"]),
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_invalidations": int(loop.cumulative_action_packet_summary["cache_invalidations"]),
        "reuse_ratio": float(reuse_ratio),
        "no_change_count": int(loop.cumulative_action_packet_summary["no_change_count"]),
        "delete_count": int(loop.cumulative_action_packet_summary["delete_count"]),
        "invalidate_count": int(loop.cumulative_action_packet_summary["invalidate_count"]),
        "applied_packets": int(loop.cumulative_action_application_summary["packet_count"]),
        "applied_packet_bytes": int(loop.cumulative_action_application_summary["bytes_total"]),
        "applied_no_change_count": int(loop.cumulative_action_application_summary["no_change_count"]),
        "applied_delete_count": int(loop.cumulative_action_application_summary["delete_count"]),
        "applied_invalidate_count": int(loop.cumulative_action_application_summary["invalidate_count"]),
        "last_transfer_plan_lines": list(summarize_transfer_plans(loop.last_ai_transfer_plans)),
        "last_action_packet_lines": list(loop.last_action_packet_lines),
        "stage_avg_ms": stage_avg_ms,
        "warmup_numba": bool(warmup_numba),
        "final_positions_xyz": state.pos[: state.body_count].copy().tolist(),
        "final_agent_flags": state.agent_active[: state.body_count].astype(np.int32).tolist(),
    }
    return payload, state


def capture_rigidbody_field_prototype(*, gravity_y: float) -> dict[str, Any]:
    coord = CoordinateSystemStore.create(capacity=8, master_gravity=(0.0, gravity_y, 0.0))
    sim_child = coord.add_system(parent_id=0, simulation_frame=True, body_local=False)
    body_local = coord.add_system(parent_id=sim_child, simulation_frame=False, body_local=True)

    rigid = RigidBodyStore.create(capacity=8)
    sphere_id = rigid.add_sphere(
        entity_id=100,
        coord_system_id=0,
        body_local_cs_id=-1,
        pos_cm_xyz=(0.0, 4.0, 0.0),
        radius=0.5,
        density=2.0,
    )
    box_id = rigid.add_box(
        entity_id=101,
        coord_system_id=sim_child,
        body_local_cs_id=body_local,
        pos_cm_xyz=(1.0, 2.0, 0.0),
        half_extents_xyz=(0.5, 0.25, 0.25),
        density=3.0,
    )

    fields = FieldSourceStore.create(capacity=4)
    source_id = fields.add_gravity_source(owner_body_id=sphere_id, coord_system_id=0, strength=0.75, cutoff_radius=10.0, dynamic=True)
    rigid.field_source_handle[sphere_id] = source_id

    summary0 = apply_center_of_mass_field_coupling(rigid, coord, fields)

    contact = ContactPoint(
        body_a=sphere_id,
        body_b=box_id,
        point_world=np.asarray((0.5, 2.5, 0.0), dtype=np.float32),
        normal_world=np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
        penetration_depth=0.05,
    )
    manifold = ContactManifold(body_a=sphere_id, body_b=box_id, manifold_kind="prototype")
    manifold.add_contact(contact)

    coord.set_master_gravity((0.0, -3.5, 0.0))
    updates = coord.propagate_inherited_fields()
    summary1 = apply_center_of_mass_field_coupling(rigid, coord, fields)

    return {
        "coord_system_count": int(coord.count),
        "gravity_revision": int(coord.gravity_revision),
        "propagated_updates": int(updates),
        "master_gravity": coord.gravity_local_xyz[0].tolist(),
        "child_gravity": coord.gravity_local_xyz[sim_child].tolist(),
        "sphere_mass": float(rigid.mass[sphere_id]),
        "sphere_inertia_diag": rigid.inertia_body_diag[sphere_id].tolist(),
        "box_mass": float(rigid.mass[box_id]),
        "box_inertia_diag": rigid.inertia_body_diag[box_id].tolist(),
        "field_summary_initial": dict(summary0),
        "field_summary_after_master_update": dict(summary1),
        "sphere_force": rigid.force_xyz[sphere_id].tolist(),
        "box_force": rigid.force_xyz[box_id].tolist(),
        "contact_count": int(manifold.contact_count),
        "contact_normal": manifold.contacts[0].normal_world.tolist(),
    }


def capture_gym_rollout(*, steps: int, backend_mode: str, seed: int = 0, action_seed: int = 99) -> dict[str, Any]:
    env_module_path = Path(__file__).resolve().parents[1] / "gym" / "env.py"
    spec = importlib.util.spec_from_file_location("poc1_engine.gym.env", env_module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load gym environment module from {env_module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    env_class = getattr(module, "POC1GymEnv")

    env = env_class(backend_mode=backend_mode)
    obs, info = env.reset(seed=seed)
    total_reward = 0.0
    last_info = info
    resets = 0

    rng = np.random.default_rng(action_seed)
    for _ in range(steps):
        action = rng.uniform(-1.0, 1.0, size=(4,)).astype(np.float32)
        obs, reward, terminated, truncated, info = env.step(action)
        last_info = info
        total_reward += reward
        if terminated or truncated:
            obs, info = env.reset(seed=seed)
            resets += 1

    return {
        "backend": f"simple_integrator:{backend_mode}",
        "steps": int(steps),
        "backend_mode": backend_mode,
        "seed": int(seed),
        "action_seed": int(action_seed),
        "total_reward": float(total_reward),
        "last_event_summary": dict(last_info.get("event_summary", {})),
        "resets": int(resets),
        "last_observation": np.asarray(obs).tolist(),
    }
