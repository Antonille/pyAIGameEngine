from __future__ import annotations

import math
from typing import Tuple

import numpy as np


def normalize(v: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < eps:
        return v * 0.0
    return v / n


def mat4_identity() -> np.ndarray:
    return np.eye(4, dtype=np.float32)


def mat4_translate(t: Tuple[float, float, float]) -> np.ndarray:
    m = mat4_identity()
    m[0, 3], m[1, 3], m[2, 3] = float(t[0]), float(t[1]), float(t[2])
    return m


def mat4_scale(s: Tuple[float, float, float]) -> np.ndarray:
    m = mat4_identity()
    m[0, 0], m[1, 1], m[2, 2] = float(s[0]), float(s[1]), float(s[2])
    return m


def mat4_perspective(fovy_deg: float, aspect: float, znear: float, zfar: float) -> np.ndarray:
    fovy = math.radians(float(fovy_deg))
    f = 1.0 / math.tan(fovy / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / float(aspect)
    m[1, 1] = f
    m[2, 2] = (float(zfar) + float(znear)) / (float(znear) - float(zfar))
    m[2, 3] = (2.0 * float(zfar) * float(znear)) / (float(znear) - float(zfar))
    m[3, 2] = -1.0
    return m


def mat4_lookat(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    f = normalize(target - eye)
    s = normalize(np.cross(f, up))
    u = np.cross(s, f)

    m = mat4_identity()
    m[0, 0:3] = s
    m[1, 0:3] = u
    m[2, 0:3] = -f
    m[0, 3] = -float(np.dot(s, eye))
    m[1, 3] = -float(np.dot(u, eye))
    m[2, 3] = float(np.dot(f, eye))
    return m
