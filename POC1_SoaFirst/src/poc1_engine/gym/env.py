from __future__ import annotations

from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from poc1_engine.ai.action_bridge import build_default_action_bridge
from poc1_engine.ai.feature_blocks import build_default_feature_block_registry
from poc1_engine.interfaces.configurable_interface import load_and_compile_default_manifest
from poc1_engine.runtime.runtime_schema import build_default_runtime_schema_registry
from poc1_engine.engine.loop import EngineConfig, EngineLoop
from poc1_engine.gym.adapter import PacketEnvActionAdapter
from poc1_engine.physics.simple_integrator_backend import SimpleIntegratorBackend
from poc1_engine.state.soa_state import SoAState


class POC1GymEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, backend_mode: str = "numpy"):
        super().__init__()
        self.state = SoAState.create(capacity=16)
        self.agent_index = self.state.spawn_body(
            pos=(0.0, 5.0, 0.0),
            linvel=(0.0, 0.0, 0.0),
            shape_type=0,
            shape_param=(0.5, 0.0, 0.0, 0.0),
            render_enabled=True,
            is_agent=True,
            inv_mass=1.0,
        )
        self.backend = SimpleIntegratorBackend(mode=backend_mode)
        self.backend.connect()
        self.action_bridge = build_default_action_bridge()
        runtime_schemas = build_default_runtime_schema_registry()
        feature_blocks = build_default_feature_block_registry(runtime_schemas)
        self.configurable_interface = load_and_compile_default_manifest(runtime_schemas, feature_blocks, self.action_bridge)
        self.loop = EngineLoop(self.state, self.backend, EngineConfig(dt=1.0 / 60.0), action_bridge=self.action_bridge)
        self.adapter = PacketEnvActionAdapter(loop=self.loop, actor_indices=np.asarray([self.agent_index], dtype=np.int32))
        self.step_limit = 512
        self.step_count = 0
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(24,), dtype=np.float32)
        self._reset_snapshot = self._capture_reset_snapshot()
        self._last_packet = None

    def _obs(self):
        return self.state.build_observations_for(np.asarray([self.agent_index], dtype=np.int32))[0].copy()

    def _capture_reset_snapshot(self) -> dict[str, Any]:
        return self.loop.export_replay_snapshot()

    def timing_snapshot(self) -> dict[str, Any]:
        return self.adapter.timing_snapshot()

    def capture_replay_snapshot(self) -> dict[str, Any]:
        return self.adapter.capture_replay_snapshot()

    def restore_replay_snapshot(self, snapshot: dict[str, Any]) -> None:
        self.adapter.restore_replay_snapshot(snapshot)
        self.step_count = self.loop.step_index

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if self._reset_snapshot is not None:
            self.restore_replay_snapshot(self._reset_snapshot)
        else:
            self.state.reset_runtime_buffers()
            self.state.pos[self.agent_index] = (0.0, 5.0, 0.0)
            self.state.linvel[self.agent_index] = (0.0, 0.0, 0.0)
            self.step_count = 0
        if options and options.get("refresh_reset_snapshot"):
            self._reset_snapshot = self._capture_reset_snapshot()
        info = {
            "control_path": "action_packets",
            "action_path": [
                "action_packets",
                "action_bridge_application",
                "state.action",
                "physics_consumption",
            ],
            "timing_snapshot": self.timing_snapshot(),
            "configurable_interface": self.configurable_interface.summary(),
        }
        return self._obs(), info

    def step(self, action):
        self._last_packet = self.adapter.submit_action(action)
        self.loop.step()
        self.step_count += 1
        obs = self._obs()
        reward = float(self.state.reward_accum[self.agent_index])
        terminated = bool(self.state.pos[self.agent_index, 1] < -0.5)
        truncated = self.step_count >= self.step_limit
        info = {
            "event_summary": dict(self.loop.last_event_summary),
            "timing_snapshot": self.timing_snapshot(),
            "control_path": "action_packets",
            "last_external_action_packet_lines": list(self.loop.last_external_action_packet_lines),
            "last_packet_apply_summary": dict(self.loop.last_input_application_summary),
            "configurable_interface": self.configurable_interface.summary(),
        }
        self.state.reward_accum[self.agent_index] = 0.0
        return obs, reward, terminated, truncated, info
