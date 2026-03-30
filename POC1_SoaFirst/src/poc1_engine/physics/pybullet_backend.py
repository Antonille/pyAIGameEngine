from __future__ import annotations


class PyBulletBackend:
    def __init__(self):
        self._p = None
        self._client = None

    def connect(self) -> None:
        try:
            import pybullet as p  # type: ignore
        except Exception as e:
            raise RuntimeError(
                'PyBullet is not installed or failed to import in the current .venv. '
                'Run scripts/windows/check_msvc_env.ps1, then rerun scripts/windows/install_project.ps1 '
                'from a Visual Studio Developer shell if you want the native PyBullet backend.'
            ) from e
        self._p = p
        self._client = p.connect(p.DIRECT)

    def disconnect(self) -> None:
        if self._p is not None and self._client is not None:
            try:
                self._p.disconnect(self._client)
            except Exception:
                pass
            self._client = None

    def reset(self, state) -> None:
        if hasattr(state, 'force_accum'):
            state.force_accum.fill(0.0)

    def step(self, state, dt: float) -> None:
        if self._p is None:
            self.connect()
        # Minimal placeholder until full body sync is restored.
        # Keeps interface compatibility without pretending the backend is production-ready.
        if hasattr(state, 'force_accum'):
            state.force_accum.fill(0.0)
        self._p.stepSimulation(physicsClientId=self._client)
