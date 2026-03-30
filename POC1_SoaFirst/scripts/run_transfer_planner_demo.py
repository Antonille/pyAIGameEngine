from __future__ import annotations

import numpy as np

from poc1_engine.ai.action_bridge import build_default_action_bridge, summarize_action_packets
from poc1_engine.ai.feature_blocks import build_default_feature_block_registry, build_default_feature_pack_registry
from poc1_engine.ai.model_family import FallbackPolicy, FreshnessSpec, ModelFamilySpec
from poc1_engine.ai.scheduler import AIScheduler
from poc1_engine.ai.transfer_planner import TransferPlanner, summarize_transfer_plans
from poc1_engine.runtime.runtime_schema import build_default_runtime_schema_registry
from poc1_engine.state.soa_state import SoAState


def seed_demo_state(state: SoAState) -> None:
    for i in range(6):
        state.spawn_body(
            pos=(float(i), 2.0 + (0.25 * i), 0.0),
            linvel=(0.1 * i, 0.0, 0.0),
            shape_type=1,
            shape_param=(0.25, 0.0, 0.0, 0.0),
            render_enabled=True,
            is_agent=(i < 5),
            inv_mass=1.0,
        )
        state.team_id[i] = np.int16(i % 2)
        state.policy_id[i] = np.int16(7 + (i % 3))
        state.reward_accum[i] = np.float32(0.5 * i)
        state.mesh_id[i] = np.int32(100 + i)
        state.material_id[i] = np.int32(200 + i)


def build_scheduler() -> AIScheduler:
    families = [
        ModelFamilySpec(
            family_name="agent_reflex_v1",
            source_family="agent_family",
            cadence_planktics=2,
            freshness=FreshnessSpec(max_input_staleness=1, max_output_staleness=2),
            stage_deadline="action_application",
            fallback_policy=FallbackPolicy.REUSE_LAST,
            feature_blocks=("kinematics_local_v1", "status_local_v1"),
            output_blocks=("action4_v1",),
            preferred_batch_size=2,
        ),
        ModelFamilySpec(
            family_name="agent_contextual_v1",
            source_family="agent_family",
            cadence_planktics=4,
            freshness=FreshnessSpec(max_input_staleness=2, max_output_staleness=4),
            stage_deadline="action_application",
            fallback_policy=FallbackPolicy.REUSE_LAST,
            feature_blocks=("kinematics_local_v1", "status_local_v1", "action_context_v1", "sparse_handle_refs_v1"),
            output_blocks=("action4_delta_v1",),
            preferred_batch_size=3,
        ),
        ModelFamilySpec(
            family_name="agent_hold_v1",
            source_family="agent_family",
            cadence_planktics=1,
            freshness=FreshnessSpec(max_input_staleness=6, max_output_staleness=6),
            stage_deadline="action_application",
            fallback_policy=FallbackPolicy.REUSE_LAST,
            feature_blocks=("policy_identity_v1",),
            output_blocks=("action4_hold_v1",),
            preferred_batch_size=4,
        ),
        ModelFamilySpec(
            family_name="agent_cleanup_v1",
            source_family="agent_family",
            cadence_planktics=1,
            freshness=FreshnessSpec(max_input_staleness=6, max_output_staleness=6),
            stage_deadline="action_application",
            fallback_policy=FallbackPolicy.REUSE_LAST,
            feature_blocks=("policy_identity_v1", "sparse_handle_refs_v1"),
            output_blocks=("action4_delete_v1",),
            preferred_batch_size=5,
        ),
    ]
    return AIScheduler(families)


def main() -> int:
    state = SoAState.create(capacity=8)
    seed_demo_state(state)

    runtime_schemas = build_default_runtime_schema_registry()
    feature_blocks = build_default_feature_block_registry(runtime_schemas)
    feature_packs = build_default_feature_pack_registry(feature_blocks)
    planner = TransferPlanner(runtime_schemas, feature_blocks, feature_packs)
    action_bridge = build_default_action_bridge()

    scheduler = build_scheduler()
    all_packets = []
    packet_summary_total = {
        "packet_count": 0,
        "entity_count": 0,
        "bytes_total": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "cache_invalidations": 0,
        "no_change_count": 0,
        "delete_count": 0,
        "invalidate_count": 0,
    }
    first_cycle_plans = []
    first_cycle_summary = {}
    first_cycle_decisions = []
    first_batch_shape = None
    first_batch_row0 = None
    for cycle in (0, 1):
        decisions = scheduler.plan_cycle(cycle, {"agent_family": state.agent_indices()})
        plans = planner.plan_cycle(decisions)
        summary = planner.materialize_cycle(state, plans)
        for family_plan in plans:
            for batch in family_plan.batches:
                staging = planner.build_staging_buffer(state, batch)
                build_result = action_bridge.build_packets_for_batch(family_plan, batch, staging, cycle=cycle)
                all_packets.extend(build_result.packets)
                for key, value in build_result.summary.items():
                    packet_summary_total[key] += int(value)
                if cycle == 0 and first_batch_shape is None:
                    first_batch_shape = tuple(staging.shape)
                    first_batch_row0 = staging[0].tolist()
        if cycle == 0:
            first_cycle_plans = plans
            first_cycle_summary = summary
            first_cycle_decisions = decisions
        for decision in decisions:
            scheduler.mark_family_started(decision.family_name, cycle)
            scheduler.mark_family_completed(decision.family_name, cycle)

    print(f"runtime_schema_family={runtime_schemas.get('agent_family').family_name}")
    print(f"agent_hot_width={runtime_schemas.get('agent_family').total_hot_width}")
    print(f"agent_sparse_width={runtime_schemas.get('agent_family').total_sparse_width}")
    print(f"scheduled_families={[d.family_name for d in first_cycle_decisions]}")
    print(f"transfer_summary={first_cycle_summary}")
    print(f"action_packet_count={packet_summary_total['packet_count']}")
    print(f"packet_cache_hits={packet_summary_total['cache_hits']}")
    print(f"packet_cache_misses={packet_summary_total['cache_misses']}")
    print(f"packet_cache_invalidations={packet_summary_total['cache_invalidations']}")
    for line in summarize_transfer_plans(first_cycle_plans):
        print(f"transfer::{line}")
    for line in summarize_action_packets(all_packets):
        print(f"action_packet::{line}")

    if first_batch_shape is not None:
        print(f"first_batch_shape={first_batch_shape}")
        print(f"first_batch_row0={first_batch_row0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
