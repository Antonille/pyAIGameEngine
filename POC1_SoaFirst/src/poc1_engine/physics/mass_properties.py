from __future__ import annotations

import math
import numpy as np


def sphere_volume(radius: float) -> float:
    r = float(radius)
    return (4.0 / 3.0) * math.pi * r * r * r


def sphere_mass(radius: float, density: float) -> float:
    return sphere_volume(radius) * float(density)


def sphere_inertia_diag(mass: float, radius: float) -> np.ndarray:
    coeff = (2.0 / 5.0) * float(mass) * float(radius) * float(radius)
    return np.asarray((coeff, coeff, coeff), dtype=np.float32)


def box_volume(half_extents_xyz) -> float:
    hx, hy, hz = [float(v) for v in half_extents_xyz]
    return 8.0 * hx * hy * hz


def box_mass(half_extents_xyz, density: float) -> float:
    return box_volume(half_extents_xyz) * float(density)


def box_inertia_diag(mass: float, half_extents_xyz) -> np.ndarray:
    hx, hy, hz = [float(v) for v in half_extents_xyz]
    ax, by, cz = 2.0 * hx, 2.0 * hy, 2.0 * hz
    ixx = (1.0 / 12.0) * float(mass) * (by * by + cz * cz)
    iyy = (1.0 / 12.0) * float(mass) * (ax * ax + cz * cz)
    izz = (1.0 / 12.0) * float(mass) * (ax * ax + by * by)
    return np.asarray((ixx, iyy, izz), dtype=np.float32)
