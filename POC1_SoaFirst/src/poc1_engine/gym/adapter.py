from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from poc1_engine.interfaces.ai_api import AIActionPacket


@dataclass
class PacketEnvActionAdapter:
    loop: object
    actor_indices: np.ndarray
    actor_family: str = "agent_family"
    action_block_name: str = "action4_env_v1"
    source_model_family: str = "external_env_v1"

    def submit_action(self, action: Sequence[float], *, generated_cycle: int | None = None) -> AIActionPacket:
        action_array = np.asarray(action, dtype=np.float32).reshape(1, -1)
        packet = AIActionPacket(
            protocol_version="action_packet_v4",
            actor_family=self.actor_family,
            actor_indices=tuple(int(i) for i in self.actor_indices.tolist()),
            action_block_name=self.action_block_name,
            payload=tuple(tuple(float(v) for v in row) for row in action_array.tolist()),
            source_model_family=self.source_model_family,
            generated_cycle=self.loop.step_index if generated_cycle is None else int(generated_cycle),
            apply_mode="replace",
            stage_deadline="input",
            metadata={
                "application_mode": "replace",
                "adapter_source": self.source_model_family,
                "control_tick": self.loop.step_index,
                "ownership_transition": "external_control_replace",
                "cache_outcome": "external_direct_packet",
            },
        )
        self.loop.submit_external_action_packets((packet,))
        return packet

    def timing_snapshot(self) -> dict:
        return self.loop.timing_contract_snapshot()

    def capture_replay_snapshot(self) -> dict:
        return self.loop.export_replay_snapshot()

    def restore_replay_snapshot(self, snapshot: dict) -> None:
        self.loop.restore_replay_snapshot(snapshot)
