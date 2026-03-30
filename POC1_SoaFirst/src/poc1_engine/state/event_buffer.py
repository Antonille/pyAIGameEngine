from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class EventBuffer:
    capacity: int
    event_type: np.ndarray | None = None
    entity_a: np.ndarray | None = None
    entity_b: np.ndarray | None = None
    scalar: np.ndarray | None = None
    count: int = 0

    EVENT_NONE = 0
    EVENT_HIT_GROUND = 1
    EVENT_HIT_WALL = 2
    EVENT_OUT_OF_BOUNDS = 3
    EVENT_AGENT_REWARD = 4

    @classmethod
    def create(cls, capacity: int) -> "EventBuffer":
        buf = cls(capacity=capacity)
        buf.event_type = np.zeros(capacity, dtype=np.uint8)
        buf.entity_a = np.full(capacity, -1, dtype=np.int32)
        buf.entity_b = np.full(capacity, -1, dtype=np.int32)
        buf.scalar = np.zeros(capacity, dtype=np.float32)
        return buf

    def reset(self) -> None:
        self.count = 0

    def push(self, event_type: int, entity_a: int, entity_b: int = -1, scalar: float = 0.0) -> None:
        if self.count >= self.capacity:
            return
        i = self.count
        self.event_type[i] = np.uint8(event_type)
        self.entity_a[i] = int(entity_a)
        self.entity_b[i] = int(entity_b)
        self.scalar[i] = float(scalar)
        self.count += 1

    def extend_mask(self, event_type: int, entity_indices: np.ndarray, scalar_value: float = 0.0) -> None:
        if entity_indices.size == 0 or self.count >= self.capacity:
            return
        remaining = self.capacity - self.count
        idx = entity_indices[:remaining].astype(np.int32, copy=False)
        n = idx.size
        start = self.count
        end = start + n
        self.event_type[start:end] = np.uint8(event_type)
        self.entity_a[start:end] = idx
        self.entity_b[start:end] = -1
        self.scalar[start:end] = scalar_value
        self.count = end

    def query(self, event_type: int | None = None, entity_a: int | None = None) -> np.ndarray:
        if self.count == 0:
            return np.zeros(0, dtype=np.int32)
        mask = np.ones(self.count, dtype=np.bool_)
        if event_type is not None:
            mask &= self.event_type[: self.count] == event_type
        if entity_a is not None:
            mask &= self.entity_a[: self.count] == entity_a
        return np.flatnonzero(mask).astype(np.int32)

    def summary(self) -> dict[str, int]:
        if self.count == 0:
            return {
                "total": 0,
                "hit_ground": 0,
                "hit_wall": 0,
                "out_of_bounds": 0,
                "agent_reward": 0,
            }
        ev = self.event_type[: self.count]
        return {
            "total": int(self.count),
            "hit_ground": int(np.count_nonzero(ev == self.EVENT_HIT_GROUND)),
            "hit_wall": int(np.count_nonzero(ev == self.EVENT_HIT_WALL)),
            "out_of_bounds": int(np.count_nonzero(ev == self.EVENT_OUT_OF_BOUNDS)),
            "agent_reward": int(np.count_nonzero(ev == self.EVENT_AGENT_REWARD)),
        }
