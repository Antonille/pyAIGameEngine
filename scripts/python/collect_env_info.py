from __future__ import annotations
import os
import platform
import sys

print('python_executable=', sys.executable)
print('python_version=', sys.version.replace("\n", ' '))
print('platform=', platform.platform())
print('cwd=', os.getcwd())
for mod in ['numpy', 'pybullet', 'pyglet', 'moderngl', 'gymnasium', 'numba', 'torch']:
    try:
        m = __import__(mod)
        print(f'{mod}=', getattr(m, '__version__', 'unknown'))
    except Exception as exc:
        print(f'{mod}=NOT_AVAILABLE ({exc})')
