from __future__ import annotations

import importlib.util
import os

from .simple_integrator_backend import SimpleIntegratorBackend


def pybullet_available() -> bool:
    return importlib.util.find_spec('pybullet') is not None


def choose_backend(prefer: str = 'auto'):
    prefer = (prefer or 'auto').lower()
    if prefer in {'simple', 'fallback', 'integrator'}:
        return SimpleIntegratorBackend(), 'simple_integrator'

    if prefer in {'pybullet', 'bullet'}:
        if not pybullet_available():
            raise RuntimeError('Requested PyBullet backend, but pybullet is not installed in this environment.')
        from .pybullet_backend import PyBulletBackend
        return PyBulletBackend(), 'pybullet'

    # auto
    env_prefer = os.environ.get('PYAIGAMEENGINE_BACKEND', '').lower().strip()
    if env_prefer in {'simple', 'fallback', 'integrator'}:
        return SimpleIntegratorBackend(), 'simple_integrator'
    if env_prefer in {'pybullet', 'bullet'} and pybullet_available():
        from .pybullet_backend import PyBulletBackend
        return PyBulletBackend(), 'pybullet'

    if pybullet_available():
        from .pybullet_backend import PyBulletBackend
        return PyBulletBackend(), 'pybullet'
    return SimpleIntegratorBackend(), 'simple_integrator'
