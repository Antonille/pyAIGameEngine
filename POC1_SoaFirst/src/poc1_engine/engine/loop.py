from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from poc1_engine.ai.action_bridge import ActionBridge, summarize_action_packets
from poc1_engine.ai.scheduler import AIScheduler
from poc1_engine.ai.transfer_planner import TransferPlanner
from poc1_engine.engine.stages import STAGE_ORDER, StageName
from poc1_engine.profiling.stage_timing import StageProfiler
from poc1_engine.render.render_subset import RenderSubsetBuilder
from poc1_engine.state.event_buffer import EventBuffer


@dataclass
class EngineConfig:
    dt: float = 1.0 / 120.0
    action_gain: float = 14.0
    observation_dim: int = 24
    event_capacity: int = 4096
    reward_interval: int = 8
    view_x: tuple[float, float] = (-10.0, 10.0)
    view_y: tuple[float, float] = (-1.0, 10.0)


class EngineLoop:
    def __init__(
        self,
        state,
        backend,
        config: EngineConfig | None = None,
        ai_scheduler: AIScheduler | None = None,
        transfer_planner: TransferPlanner | None = None,
        action_bridge: ActionBridge | None = None,
    ):
        self.state = state
        self.backend = backend
        self.config = config or EngineConfig()
        self.profiler = StageProfiler()
        self.step_index = 0
        self.event_buffer = EventBuffer.create(self.config.event_capacity)
        self.last_event_summary = {"total": 0, "hit_ground": 0, "hit_wall": 0, "out_of_bounds": 0, "agent_reward": 0}
        self.last_agent_obs = np.zeros((0, self.state.obs_dim), dtype=np.float32)
        self.last_visible_indices = np.zeros(0, dtype=np.int32)
        self.render_subset_builder = RenderSubsetBuilder(self.config.view_x, self.config.view_y)
        self.ai_scheduler = ai_scheduler
        self.transfer_planner = transfer_planner
        self.action_bridge = action_bridge
        self.last_ai_schedule = []
        self.last_ai_transfer_plans = []
        self.last_ai_transfer_summary = {
            "family_count": 0,
            "batch_count": 0,
            "entity_count": 0,
            "feature_width_total": 0,
            "float32_values_total": 0,
            "bytes_total": 0,
        }
        self.cumulative_ai_transfer_summary = {
            "family_count": 0,
            "batch_count": 0,
            "entity_count": 0,
            "feature_width_total": 0,
            "float32_values_total": 0,
            "bytes_total": 0,
        }
        self.ai_schedule_counts: dict[str, int] = {}
        self.pending_action_packets = []
        self.last_action_packet_lines = []
        self.last_action_packet_summary = {
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
        self.cumulative_action_packet_summary = dict(self.last_action_packet_summary)
        self.last_action_application_summary = {
            "packet_count": 0,
            "entity_count": 0,
            "bytes_total": 0,
            "no_change_count": 0,
            "delete_count": 0,
            "invalidate_count": 0,
        }
        self.cumulative_action_application_summary = dict(self.last_action_application_summary)

    def run_steps(self, steps: int) -> None:
        for _ in range(steps):
            self.step()

    def query_events(self, event_type: int | None = None, entity_a: int | None = None) -> np.ndarray:
        return self.event_buffer.query(event_type=event_type, entity_a=entity_a)

    def step(self) -> None:
        for stage in STAGE_ORDER:
            with self.profiler.measure(stage.value):
                self._run_stage(stage)
        self.step_index += 1

    def _run_stage(self, stage: StageName) -> None:
        if stage == StageName.INPUT:
            return
        elif stage == StageName.AI:
            self._ai_stage()
        elif stage == StageName.ACTION_APPLICATION:
            self._action_application_stage()
        elif stage == StageName.PHYSICS:
            self.backend.step(self.state, self.config.dt)
        elif stage == StageName.EVENT_PROCESSING:
            self._event_processing_stage()
        elif stage == StageName.OBSERVATION_BUILD:
            agent_indices = self.state.agent_indices()
            self.last_agent_obs = self.state.build_observations_for(agent_indices)
            self.state.obs_index[: agent_indices.size] = agent_indices
        elif stage == StageName.RENDER_SNAPSHOT:
            self.last_visible_indices = self.render_subset_builder.select_visible_indices(self.state)
            self.render_subset_builder.build_snapshot(self.state, self.last_visible_indices)

    def _ai_stage(self) -> None:
        agent_indices = self.state.agent_indices()
        if self.ai_scheduler is not None:
            self.last_ai_schedule = self.ai_scheduler.plan_cycle(self.step_index, {"agent_family": agent_indices})
        else:
            self.last_ai_schedule = []

        self.pending_action_packets = []
        self.last_action_packet_lines = []
        self.last_action_packet_summary = {
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
        self.last_action_application_summary = {
            "packet_count": 0,
            "entity_count": 0,
            "bytes_total": 0,
            "no_change_count": 0,
            "delete_count": 0,
            "invalidate_count": 0,
        }

        if self.transfer_planner is not None and self.last_ai_schedule:
            self.last_ai_transfer_plans = self.transfer_planner.plan_cycle(self.last_ai_schedule)
            self.last_ai_transfer_summary = self.transfer_planner.materialize_cycle(self.state, self.last_ai_transfer_plans)
            if self.action_bridge is not None:
                for family_plan in self.last_ai_transfer_plans:
                    for batch in family_plan.batches:
                        staging = self.transfer_planner.build_staging_buffer(self.state, batch)
                        build_result = self.action_bridge.build_packets_for_batch(
                            family_plan=family_plan,
                            batch=batch,
                            staging=staging,
                            cycle=self.step_index,
                        )
                        self.pending_action_packets.extend(build_result.packets)
                        for key, value in build_result.summary.items():
                            self.last_action_packet_summary[key] += int(value)
                self.last_action_packet_lines = summarize_action_packets(self.pending_action_packets)
        else:
            self.last_ai_transfer_plans = []
            self.last_ai_transfer_summary = {
                "family_count": 0,
                "batch_count": 0,
                "entity_count": int(agent_indices.size),
                "feature_width_total": 0,
                "float32_values_total": 0,
                "bytes_total": 0,
            }

        if self.ai_scheduler is not None:
            for decision in self.last_ai_schedule:
                self.ai_scheduler.mark_family_started(decision.family_name, self.step_index)
                self.ai_scheduler.mark_family_completed(decision.family_name, self.step_index)
                self.ai_schedule_counts[decision.family_name] = self.ai_schedule_counts.get(decision.family_name, 0) + 1

        for key, value in self.last_ai_transfer_summary.items():
            self.cumulative_ai_transfer_summary[key] += int(value)
        for key, value in self.last_action_packet_summary.items():
            self.cumulative_action_packet_summary[key] += int(value)

    def _action_application_stage(self) -> None:
        sl = self.state.live_slice()
        if self.state.body_count == 0:
            return
        if self.action_bridge is not None and self.pending_action_packets:
            self.last_action_application_summary = self.action_bridge.apply_packets(self.state, self.pending_action_packets)
            for key, value in self.last_action_application_summary.items():
                self.cumulative_action_application_summary[key] += int(value)
        self.state.force[sl, 0] += self.state.action[sl, 0] * self.config.action_gain
        self.state.force[sl, 1] += self.state.action[sl, 1] * self.config.action_gain

    def _event_processing_stage(self) -> None:
        sl = self.state.live_slice()
        self.event_buffer.reset()
        if self.state.body_count == 0:
            self.last_event_summary = self.event_buffer.summary()
            return

        hit_ground = self.state.pos[sl, 1] <= 0.0001
        self.event_buffer.extend_mask(EventBuffer.EVENT_HIT_GROUND, np.flatnonzero(hit_ground).astype(np.int32))

        hit_wall = getattr(self.backend, "last_hit_wall", None)
        if hit_wall is not None:
            self.event_buffer.extend_mask(EventBuffer.EVENT_HIT_WALL, np.flatnonzero(hit_wall).astype(np.int32))

        out_of_bounds = (
            (self.state.pos[sl, 0] < self.config.view_x[0] - 2.0)
            | (self.state.pos[sl, 0] > self.config.view_x[1] + 2.0)
            | (self.state.pos[sl, 1] < self.config.view_y[0] - 2.0)
            | (self.state.pos[sl, 1] > self.config.view_y[1] + 2.0)
        )
        self.event_buffer.extend_mask(EventBuffer.EVENT_OUT_OF_BOUNDS, np.flatnonzero(out_of_bounds).astype(np.int32))

        if (self.step_index % self.config.reward_interval) == 0:
            agent_indices = self.state.agent_indices()
            if agent_indices.size > 0:
                self.event_buffer.extend_mask(EventBuffer.EVENT_AGENT_REWARD, agent_indices)
                self.state.reward_accum[agent_indices] += 0.001

        if np.any(hit_ground):
            self.state.reward_accum[: self.state.body_count] += np.where(hit_ground, -0.01, 0.0).astype(np.float32)

        self.last_event_summary = self.event_buffer.summary()

    def stage_summary_lines(self) -> list[str]:
        return self.profiler.summary_lines()
