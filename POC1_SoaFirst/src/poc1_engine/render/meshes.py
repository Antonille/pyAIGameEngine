from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass(frozen=True)
class MeshData:
    vertices: np.ndarray  # (V, 3) float32
    indices: np.ndarray   # (I,) uint32


def make_unit_cube() -> MeshData:
    # 8 vertices, 12 triangles. (No normals/uvs yet.)
    v = np.array(
        [
            (-1, -1, -1),
            ( 1, -1, -1),
            ( 1,  1, -1),
            (-1,  1, -1),
            (-1, -1,  1),
            ( 1, -1,  1),
            ( 1,  1,  1),
            (-1,  1,  1),
        ],
        dtype=np.float32,
    )
    i = np.array(
        [
            0,1,2,  2,3,0,  # -Z
            4,5,6,  6,7,4,  # +Z
            0,4,7,  7,3,0,  # -X
            1,5,6,  6,2,1,  # +X
            3,2,6,  6,7,3,  # +Y
            0,1,5,  5,4,0,  # -Y
        ],
        dtype=np.uint32,
    )
    return MeshData(vertices=v, indices=i)


def make_uv_sphere(segments: int = 16, rings: int = 12) -> MeshData:
    # Minimal lat-long sphere for POC1.
    vertices = []
    indices = []

    for r in range(rings + 1):
        v = r / rings
        phi = v * np.pi
        for s in range(segments + 1):
            u = s / segments
            theta = u * 2 * np.pi
            x = np.sin(phi) * np.cos(theta)
            y = np.cos(phi)
            z = np.sin(phi) * np.sin(theta)
            vertices.append((x, y, z))

    def vid(r, s):
        return r * (segments + 1) + s

    for r in range(rings):
        for s in range(segments):
            i0 = vid(r, s)
            i1 = vid(r + 1, s)
            i2 = vid(r + 1, s + 1)
            i3 = vid(r, s + 1)
            indices += [i0, i1, i2, i2, i3, i0]

    return MeshData(
        vertices=np.asarray(vertices, dtype=np.float32),
        indices=np.asarray(indices, dtype=np.uint32),
    )
