from __future__ import annotations

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from poc1_engine.engine.loop import EngineConfig, EngineLoop
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
        self.loop = EngineLoop(self.state, self.backend, EngineConfig(dt=1.0 / 60.0))
        self.step_limit = 512
        self.step_count = 0
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(24,), dtype=np.float32)

    def _obs(self):
        return self.state.build_observations_for(np.asarray([self.agent_index], dtype=np.int32))[0].copy()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.state.reset_runtime_buffers()
        self.state.pos[self.agent_index] = (0.0, 5.0, 0.0)
        self.state.linvel[self.agent_index] = (0.0, 0.0, 0.0)
        self.step_count = 0
        return self._obs(), {}

    def step(self, action):
        self.state.action[self.agent_index, :4] = np.asarray(action, dtype=np.float32)
        self.loop.step()
        self.step_count += 1
        obs = self._obs()
        reward = float(self.state.reward_accum[self.agent_index])
        terminated = bool(self.state.pos[self.agent_index, 1] < -0.5)
        truncated = self.step_count >= self.step_limit
        info = {"event_summary": dict(self.loop.last_event_summary)}
        self.state.reward_accum[self.agent_index] = 0.0
        return obs, reward, terminated, truncated, info
