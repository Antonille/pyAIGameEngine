import argparse
import inspect
import sys
import time
from dataclasses import dataclass

import numpy as np
import pyglet
from pyglet import shapes


def _try_make_pybullet_backend(bullet_gui: bool):
    """
    Instantiate PyBulletBackend against the current constructor shape.

    Supported patterns:
    - PyBulletBackend(gui=...)
    - PyBulletBackend(use_gui=...)
    - PyBulletBackend() then connect(gui=...) / connect(use_gui=...)
    - PyBulletBackend() with connect()
    """
    try:
        from poc1_engine.physics.pybullet_backend import PyBulletBackend
    except Exception as exc:
        raise RuntimeError(f"PyBullet backend import failed: {exc}") from exc

    sig = inspect.signature(PyBulletBackend.__init__)
    params = sig.parameters

    if "gui" in params:
        backend = PyBulletBackend(gui=bullet_gui)
        connect_kwargs = None
    elif "use_gui" in params:
        backend = PyBulletBackend(use_gui=bullet_gui)
        connect_kwargs = None
    else:
        backend = PyBulletBackend()
        connect_sig = inspect.signature(backend.connect)
        if "gui" in connect_sig.parameters:
            connect_kwargs = {"gui": bullet_gui}
        elif "use_gui" in connect_sig.parameters:
            connect_kwargs = {"use_gui": bullet_gui}
        else:
            connect_kwargs = {}

    return backend, connect_kwargs


@dataclass
class SimpleViewerState:
    width: int
    height: int
    n: int
    radius: float = 8.0

    def __post_init__(self):
        rng = np.random.default_rng(7)
        self.pos = rng.uniform(
            low=[self.radius, self.radius],
            high=[self.width - self.radius, self.height - self.radius],
            size=(self.n, 2),
        ).astype(np.float32)
        self.vel = rng.uniform(low=-140.0, high=140.0, size=(self.n, 2)).astype(np.float32)
        self.colors = [
            (
                int(rng.integers(60, 255)),
                int(rng.integers(60, 255)),
                int(rng.integers(60, 255)),
            )
            for _ in range(self.n)
        ]

    def step(self, dt: float):
        self.pos += self.vel * dt

        for axis, limit in ((0, self.width), (1, self.height)):
            low_mask = self.pos[:, axis] < self.radius
            high_mask = self.pos[:, axis] > (limit - self.radius)

            if np.any(low_mask):
                self.pos[low_mask, axis] = self.radius
                self.vel[low_mask, axis] *= -1.0

            if np.any(high_mask):
                self.pos[high_mask, axis] = limit - self.radius
                self.vel[high_mask, axis] *= -1.0


def run_simple_viewer(args):
    window = pyglet.window.Window(
        width=args.width,
        height=args.height,
        caption="pyAIGameEngine POC1 Viewer (simple backend)",
        resizable=False,
    )
    batch = pyglet.graphics.Batch()
    state = SimpleViewerState(width=args.width, height=args.height, n=args.n, radius=args.radius)
    circles = [
        shapes.Circle(
            x=float(state.pos[i, 0]),
            y=float(state.pos[i, 1]),
            radius=args.radius,
            color=state.colors[i],
            batch=batch,
        )
        for i in range(args.n)
    ]
    pyglet.text.Label(
        "backend=simple_integrator",
        x=10,
        y=args.height - 20,
        anchor_x="left",
        anchor_y="center",
        batch=batch,
    )

    def update(dt):
        state.step(dt)
        for i, c in enumerate(circles):
            c.x = float(state.pos[i, 0])
            c.y = float(state.pos[i, 1])

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    pyglet.clock.schedule_interval(update, 1.0 / max(args.fps, 1))
    pyglet.app.run()


def run_pybullet_viewer(args):
    backend, connect_kwargs = _try_make_pybullet_backend(args.bullet_gui)
    if connect_kwargs is None:
        backend.connect()
    else:
        backend.connect(**connect_kwargs)

    print("backend=pybullet")
    print("PyBullet backend initialized.")
    print("If Bullet GUI is enabled, use that window. Close this process with Ctrl+C when done.")

    try:
        dt = 1.0 / max(args.fps, 1)
        for _ in range(args.steps):
            if hasattr(backend, "step"):
                try:
                    backend.step(dt)
                except TypeError:
                    backend.step()
            time.sleep(dt)
    finally:
        if hasattr(backend, "disconnect"):
            try:
                backend.disconnect()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="POC1 viewer")
    parser.add_argument("--backend", choices=["simple", "pybullet"], default="simple")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--n", type=int, default=64, help="body count for simple viewer")
    parser.add_argument("--radius", type=float, default=8.0)
    parser.add_argument("--steps", type=int, default=1800, help="steps for pybullet viewer loop")
    parser.add_argument("--bullet-gui", action="store_true", help="request Bullet GUI if pybullet backend supports it")
    args = parser.parse_args()

    if args.backend == "pybullet":
        try:
            run_pybullet_viewer(args)
            return 0
        except Exception as exc:
            print(f"[WARN] PyBullet viewer unavailable: {exc}", file=sys.stderr)
            print("[INFO] Falling back to simple viewer.", file=sys.stderr)

    run_simple_viewer(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
