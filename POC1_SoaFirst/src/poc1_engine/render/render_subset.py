from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class RenderSubsetBuilder:
    view_x: tuple[float, float] = (-10.0, 10.0)
    view_y: tuple[float, float] = (-1.0, 10.0)

    def select_visible_indices(self, state) -> np.ndarray:
        sl = state.live_slice()
        state.render_visible[sl] = 0
        if state.body_count == 0:
            return np.zeros(0, dtype=np.int32)

        visible = (
            (state.render_enabled[sl] == 1)
            & (state.pos[sl, 0] >= self.view_x[0])
            & (state.pos[sl, 0] <= self.view_x[1])
            & (state.pos[sl, 1] >= self.view_y[0])
            & (state.pos[sl, 1] <= self.view_y[1])
        )
        state.render_visible[sl] = visible.astype(np.uint8)
        return np.flatnonzero(visible).astype(np.int32)

    def build_snapshot(self, state, visible_indices: np.ndarray) -> None:
        sl = state.live_slice()
        state.xform44_snapshot[sl].fill(0.0)
        if visible_indices.size == 0:
            return
        state.xform44_snapshot[visible_indices, 0] = state.scale[visible_indices, 0]
        state.xform44_snapshot[visible_indices, 5] = state.scale[visible_indices, 1]
        state.xform44_snapshot[visible_indices, 10] = state.scale[visible_indices, 2]
        state.xform44_snapshot[visible_indices, 12] = state.pos[visible_indices, 0]
        state.xform44_snapshot[visible_indices, 13] = state.pos[visible_indices, 1]
        state.xform44_snapshot[visible_indices, 14] = state.pos[visible_indices, 2]
        state.xform44_snapshot[visible_indices, 15] = 1.0
