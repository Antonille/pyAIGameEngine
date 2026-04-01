from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from poc1_engine.ai.action_bridge import ActionBridge, build_default_action_bridge, summarize_action_packets
from poc1_engine.ai.feature_blocks import build_default_feature_block_registry, build_default_feature_pack_registry
from poc1_engine.ai.model_family import FallbackPolicy, FreshnessSpec, ModelFamilySpec
from poc1_engine.ai.scheduler import AIScheduler, ScheduleDecision
from poc1_engine.ai.transfer_planner import FamilyTransferPlan, TransferPlanner
from poc1_engine.interfaces.configurable_interface import load_and_compile_default_manifest
from poc1_engine.runtime.runtime_schema import build_default_runtime_schema_registry
from poc1_engine.state.soa_state import SoAState


@dataclass(frozen=True)
class AcceptanceCheck:
    name: str
    passed: bool
    details: str


@dataclass(frozen=True)
class AcceptanceRunResult:
    gate_status: str
    checks: tuple[AcceptanceCheck, ...]
    summary: dict[str, Any]


def seed_state(state: SoAState) -> None:
    rng = np.random.default_rng(123)
    agent_count = min(max(state.capacity // 16, 4), state.capacity)
    for i in range(state.capacity):
        x = float(rng.uniform(-8.0, 8.0))
        y = float(rng.uniform(1.0, 9.0))
        vx = float(rng.uniform(-1.5, 1.5))
        vy = float(rng.uniform(-1.5, 1.5))
        state.spawn_body(
            pos=(x, y, 0.0),
            linvel=(vx, vy, 0.0),
            shape_type=0,
            shape_param=(0.3, 0.0, 0.0, 0.0),
            render_enabled=True,
            is_agent=(i < agent_count),
            inv_mass=1.0,
        )
        if i < agent_count:
            state.team_id[i] = np.int16(i % 2)
            state.policy_id[i] = np.int16(7 + (i % 3))
            state.reward_accum[i] = np.float32(0.05 * i)
            state.mesh_id[i] = np.int32(1000 + i)
            state.material_id[i] = np.int32(2000 + (i % 5))


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
            preferred_batch_size=128,
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
            preferred_batch_size=64,
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
            preferred_batch_size=96,
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
            preferred_batch_size=96,
        ),
    ]
    return AIScheduler(families)


def build_transfer_planner() -> TransferPlanner:
    runtime_schemas = build_default_runtime_schema_registry()
    feature_blocks = build_default_feature_block_registry(runtime_schemas)
    feature_packs = build_default_feature_pack_registry(feature_blocks)
    return TransferPlanner(runtime_schemas, feature_blocks, feature_packs)




def build_default_interface_summary() -> dict[str, Any]:
    runtime_schemas = build_default_runtime_schema_registry()
    feature_blocks = build_default_feature_block_registry(runtime_schemas)
    action_bridge = build_default_action_bridge()
    plan = load_and_compile_default_manifest(runtime_schemas, feature_blocks, action_bridge)
    return plan.summary()

def _require(name: str, passed: bool, details: str) -> AcceptanceCheck:
    return AcceptanceCheck(name=name, passed=passed, details=details)


def _packet_lines(packets) -> tuple[str, ...]:
    return tuple(summarize_action_packets(packets))


def run_gate_d_acceptance() -> AcceptanceRunResult:
    checks: list[AcceptanceCheck] = []

    state = SoAState.create(capacity=64)
    seed_state(state)
    scheduler = build_scheduler()
    transfer_planner = build_transfer_planner()
    action_bridge = build_default_action_bridge()
    interface_summary = build_default_interface_summary()

    family_specs = scheduler.family_specs
    schedule_counts = {name: 0 for name in family_specs}
    agent_map = {"agent_family": state.agent_indices()}

    # Scheduling acceptance over the smoke window used elsewhere in the project.
    for cycle in range(20):
        decisions = scheduler.plan_cycle(cycle, agent_map)
        decision_map = {d.family_name: d for d in decisions}
        for name, spec in family_specs.items():
            due_expected = (cycle == 0) or (cycle % spec.cadence_planktics == 0)
            due_actual = name in decision_map
            checks.append(
                _require(
                    name=f"scheduler.cadence.{name}.cycle_{cycle}",
                    passed=(due_expected == due_actual),
                    details=f"expected_due={due_expected} actual_due={due_actual} cadence={spec.cadence_planktics}",
                )
            )
            if due_actual:
                schedule_counts[name] += 1
                decision = decision_map[name]
                checks.extend(
                    [
                        _require(
                            name=f"scheduler.freshness.{name}",
                            passed=(
                                decision.max_input_staleness == spec.freshness.max_input_staleness
                                and decision.max_output_staleness == spec.freshness.max_output_staleness
                            ),
                            details=(
                                f"input={decision.max_input_staleness}/{spec.freshness.max_input_staleness} "
                                f"output={decision.max_output_staleness}/{spec.freshness.max_output_staleness}"
                            ),
                        ),
                        _require(
                            name=f"scheduler.fallback.{name}",
                            passed=(decision.fallback_policy == spec.fallback_policy.value),
                            details=f"decision={decision.fallback_policy} expected={spec.fallback_policy.value}",
                        ),
                        _require(
                            name=f"scheduler.batchability_field.{name}",
                            passed=(decision.preferred_batch_size == spec.preferred_batch_size),
                            details=f"decision={decision.preferred_batch_size} expected={spec.preferred_batch_size}",
                        ),
                    ]
                )
                scheduler.mark_family_started(name, cycle)
                scheduler.mark_family_completed(name, cycle)

    expected_counts = {
        "agent_reflex_v1": 10,
        "agent_contextual_v1": 5,
        "agent_hold_v1": 20,
        "agent_cleanup_v1": 20,
    }
    for name, expected in expected_counts.items():
        checks.append(
            _require(
                name=f"scheduler.count.{name}",
                passed=(schedule_counts[name] == expected),
                details=f"actual={schedule_counts[name]} expected={expected}",
            )
        )

    # Explicit batchability split check using a synthetic narrow preferred batch size.
    batch_test_decision = ScheduleDecision(
        family_name="agent_reflex_v1",
        source_family="agent_family",
        entity_indices=np.asarray([0, 1, 2, 3, 4], dtype=np.int32),
        feature_blocks=("kinematics_local_v1", "status_local_v1"),
        output_blocks=("action4_v1",),
        cadence_planktics=2,
        stage_deadline="action_application",
        fallback_policy="reuse_last",
        preferred_batch_size=2,
        max_input_staleness=1,
        max_output_staleness=2,
    )
    batch_test_plan = transfer_planner.plan_cycle([batch_test_decision])[0]
    batch_sizes = [batch.entity_count for batch in batch_test_plan.batches]
    checks.append(
        _require(
            name="scheduler.batchability.split",
            passed=(batch_sizes == [2, 2, 1]),
            details=f"batch_sizes={batch_sizes} expected=[2, 2, 1]",
        )
    )

    # Packet-lane acceptance checks using deterministic family plans and batches.
    packet_scheduler = build_scheduler()
    family_plans = transfer_planner.plan_cycle(packet_scheduler.plan_cycle(0, {"agent_family": state.agent_indices()}))
    family_by_name = {plan.family_name: plan for plan in family_plans}

    reflex_plan = family_by_name["agent_reflex_v1"]
    reflex_batch = reflex_plan.batches[0]
    reflex_staging = transfer_planner.build_staging_buffer(state, reflex_batch)
    reflex_first = action_bridge.build_packets_for_batch(reflex_plan, reflex_batch, reflex_staging, cycle=0)
    reflex_packet = reflex_first.packets[0]
    checks.append(
        _require(
            name="packet.replace.initial",
            passed=(
                reflex_packet.apply_mode == "replace"
                and reflex_packet.generation_id is not None
                and reflex_packet.baseline_generation_id is None
                and reflex_packet.supersedes_generation_id is None
            ),
            details=_packet_lines(reflex_first.packets)[0],
        )
    )
    # Force a miss-build refresh on the same lane.
    state.pos[reflex_batch.entity_indices[0], 0] += np.float32(0.5)
    reflex_staging_2 = transfer_planner.build_staging_buffer(state, reflex_batch)
    reflex_second = action_bridge.build_packets_for_batch(reflex_plan, reflex_batch, reflex_staging_2, cycle=1)
    reflex_refresh = reflex_second.packets[-1]
    checks.append(
        _require(
            name="packet.replace.supersede",
            passed=(
                reflex_refresh.apply_mode == "replace"
                and reflex_refresh.baseline_generation_id == reflex_packet.generation_id
                and reflex_refresh.supersedes_generation_id == reflex_packet.generation_id
                and reflex_refresh.ownership_scope == reflex_packet.ownership_scope
                and reflex_refresh.ownership_key == reflex_packet.ownership_key
            ),
            details=_packet_lines(reflex_second.packets)[-1],
        )
    )

    contextual_plan = family_by_name["agent_contextual_v1"]
    contextual_batch = contextual_plan.batches[0]
    contextual_staging = transfer_planner.build_staging_buffer(state, contextual_batch)
    contextual_first = action_bridge.build_packets_for_batch(contextual_plan, contextual_batch, contextual_staging, cycle=0)
    contextual_packet = contextual_first.packets[0]
    state.reward_accum[contextual_batch.entity_indices] += np.float32(0.25)
    contextual_staging_2 = transfer_planner.build_staging_buffer(state, contextual_batch)
    contextual_second = action_bridge.build_packets_for_batch(contextual_plan, contextual_batch, contextual_staging_2, cycle=1)
    contextual_refresh = contextual_second.packets[-1]
    checks.append(
        _require(
            name="packet.delta.baseline",
            passed=(
                contextual_refresh.apply_mode == "delta"
                and contextual_refresh.baseline_generation_id == contextual_packet.generation_id
                and contextual_refresh.supersedes_generation_id is None
                and contextual_refresh.baseline_ownership_key == contextual_packet.ownership_key
                and contextual_refresh.ownership_scope == contextual_packet.ownership_scope
            ),
            details=_packet_lines(contextual_second.packets)[-1],
        )
    )

    hold_plan = family_by_name["agent_hold_v1"]
    hold_batch = hold_plan.batches[0]
    hold_staging = transfer_planner.build_staging_buffer(state, hold_batch)
    hold_first = action_bridge.build_packets_for_batch(hold_plan, hold_batch, hold_staging, cycle=0)
    hold_initial = hold_first.packets[0]
    hold_second = action_bridge.build_packets_for_batch(hold_plan, hold_batch, hold_staging, cycle=1)
    hold_hit = hold_second.packets[-1]
    hold_third = action_bridge.build_packets_for_batch(hold_plan, hold_batch, hold_staging, cycle=8)
    hold_stale_refresh = hold_third.packets[-1]
    checks.extend(
        [
            _require(
                name="packet.no_change.cache_hit",
                passed=(
                    hold_hit.apply_mode == "no_change"
                    and hold_hit.payload == tuple()
                    and hold_hit.baseline_generation_id == hold_initial.generation_id
                    and hold_hit.supersedes_generation_id == hold_initial.generation_id
                ),
                details=_packet_lines(hold_second.packets)[-1],
            ),
            _require(
                name="scheduler.freshness.output_staleness",
                passed=(
                    hold_stale_refresh.apply_mode == "replace"
                    and hold_stale_refresh.generation_id != hold_initial.generation_id
                    and hold_stale_refresh.baseline_generation_id == hold_initial.generation_id
                ),
                details=_packet_lines(hold_third.packets)[-1],
            ),
        ]
    )

    cleanup_plan = family_by_name["agent_cleanup_v1"]
    cleanup_batch = cleanup_plan.batches[0]
    cleanup_staging = transfer_planner.build_staging_buffer(state, cleanup_batch)
    cleanup_first = action_bridge.build_packets_for_batch(cleanup_plan, cleanup_batch, cleanup_staging, cycle=0)
    cleanup_packet = cleanup_first.packets[0]
    state.mesh_id[cleanup_batch.entity_indices] += np.int32(1)
    cleanup_staging_2 = transfer_planner.build_staging_buffer(state, cleanup_batch)
    cleanup_second = action_bridge.build_packets_for_batch(cleanup_plan, cleanup_batch, cleanup_staging_2, cycle=1)
    cleanup_refresh = cleanup_second.packets[-1]
    checks.append(
        _require(
            name="packet.delete.supersede",
            passed=(
                cleanup_refresh.apply_mode == "delete"
                and cleanup_refresh.baseline_generation_id == cleanup_packet.generation_id
                and cleanup_refresh.supersedes_generation_id == cleanup_packet.generation_id
                and cleanup_refresh.baseline_ownership_key == cleanup_packet.ownership_key
                and cleanup_refresh.supersedes_ownership_key == cleanup_packet.ownership_key
            ),
            details=_packet_lines(cleanup_second.packets)[-1],
        )
    )

    checks.extend(
        [
            _require(
                name="configurable_interface.handshake",
                passed=(
                    interface_summary.get("compatibility_handshake", {}).get("status") == "pass"
                    and interface_summary.get("runtime_binding") == "compiled_startup_plan_v1"
                ),
                details=(
                    f"status={interface_summary.get('compatibility_handshake', {}).get('status')} "
                    f"runtime_binding={interface_summary.get('runtime_binding')}"
                ),
            ),
            _require(
                name="configurable_interface.observation_width",
                passed=(interface_summary.get("compiled_channels", [{}])[0].get("width") == 19),
                details=str(interface_summary.get("compiled_channels", [{}])[0]),
            ),
        ]
    )

    summary = {
        "gate_name": "Phase 3 Gate D — Scheduler and Packet Acceptance Gate",
        "schedule_counts": schedule_counts,
        "expected_schedule_counts": expected_counts,
        "synthetic_batch_sizes": batch_sizes,
        "replace_generation_chain": [reflex_packet.generation_id, reflex_refresh.generation_id],
        "delta_generation_chain": [contextual_packet.generation_id, contextual_refresh.generation_id],
        "hold_generation_chain": [hold_initial.generation_id, hold_hit.generation_id, hold_stale_refresh.generation_id],
        "delete_generation_chain": [cleanup_packet.generation_id, cleanup_refresh.generation_id],
        "configurable_interface": interface_summary,
    }

    gate_status = "cleared" if all(check.passed for check in checks) else "blocked"
    return AcceptanceRunResult(gate_status=gate_status, checks=tuple(checks), summary=summary)
