from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..state.soa_state import SoAState, ShapeType
from ..utils.math3d import mat4_identity, mat4_lookat, mat4_perspective, mat4_scale, mat4_translate
from .meshes import make_unit_cube, make_uv_sphere


VERTEX_SHADER = """#version 330
in vec3 in_pos;

uniform mat4 u_mvp;

void main() {
    gl_Position = u_mvp * vec4(in_pos, 1.0);
}
"""

FRAGMENT_SHADER = """#version 330
uniform vec4 u_color;
out vec4 fragColor;

void main() {
    fragColor = u_color;
}
"""


@dataclass
class MGLRenderer:
    """Minimal pyglet+ModernGL renderer for POC1.

    - Uses simple unlit shader.
    - Draws spheres and boxes using separate VAOs.
    - Uses per-body uniforms (no instancing yet).
    """

    width: int = 1280
    height: int = 720
    fovy_deg: float = 60.0

    def __post_init__(self) -> None:
        self._window = None
        self._ctx = None
        self._prog = None

    def create_window(self, caption: str = "POC1 — PlankTick SoA BulletGL") -> None:
        try:
            import pyglet  # type: ignore
            import moderngl  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "pyglet/moderngl not installed. Install extras: "

                "scripts/windows/install_project.ps1 from the repo root on Python 3.12"

            ) from e

        # Create pyglet window with GL 3.3 context if possible
        config = pyglet.gl.Config(double_buffer=True, major_version=3, minor_version=3, depth_size=24)
        self._window = pyglet.window.Window(width=self.width, height=self.height, caption=caption, config=config, vsync=False, resizable=True)
        self._ctx = moderngl.create_context()
        self._ctx.enable(moderngl.DEPTH_TEST)

        self._prog = self._ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)

        # Meshes
        cube = make_unit_cube()
        sphere = make_uv_sphere(segments=20, rings=14)

        self._vao_cube = self._make_vao(cube.vertices, cube.indices)
        self._vao_sphere = self._make_vao(sphere.vertices, sphere.indices)

        # Camera state
        self._cam_radius = 12.0
        self._cam_theta = 0.6
        self._cam_phi = 0.9

        @self._window.event
        def on_draw():
            self._window.clear()

        @self._window.event
        def on_resize(width, height):
            self.width, self.height = int(width), int(height)
            if self._ctx is not None:
                self._ctx.viewport = (0, 0, self.width, self.height)

        @self._window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            # orbit
            self._cam_theta += dx * 0.005
            self._cam_phi = float(np.clip(self._cam_phi - dy * 0.005, 0.1, 3.04))

        @self._window.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):
            self._cam_radius = float(np.clip(self._cam_radius * (0.92 ** scroll_y), 2.0, 80.0))

    def run(self, state: SoAState, step_fn, dt_seconds: float) -> None:
        """Run a simple render loop. step_fn will be called once per frame."""
        import pyglet  # type: ignore

        if self._window is None:
            self.create_window()

        def tick(_dt):
            step_fn(dt_seconds)
            self.draw(state)

        pyglet.clock.schedule_interval(tick, 0.0)
        pyglet.app.run()

    def draw(self, state: SoAState) -> None:
        if self._ctx is None or self._prog is None:
            return

        self._ctx.clear(0.08, 0.08, 0.10)
        self._ctx.enable_only(self._ctx.DEPTH_TEST)

        aspect = max(1e-6, float(self.width) / float(self.height))
        proj = mat4_perspective(self.fovy_deg, aspect, 0.05, 400.0)

        # Orbit camera
        eye = np.array([
            self._cam_radius * np.sin(self._cam_phi) * np.cos(self._cam_theta),
            self._cam_radius * np.cos(self._cam_phi),
            self._cam_radius * np.sin(self._cam_phi) * np.sin(self._cam_theta),
        ], dtype=np.float32)
        target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        view = mat4_lookat(eye, target, up)

        alive = state.alive_indices()
        for idx in alive.tolist():
            st = int(state.shape_type[idx])
            px, py, pz = state.pos[idx].tolist()
            color = state.color_rgba[idx].astype(np.float32)

            if st == int(ShapeType.SPHERE):
                r = float(state.shape_param[idx, 0])
                model = mat4_translate((px, py, pz)) @ mat4_scale((r, r, r))
                vao = self._vao_sphere
            else:
                hx, hy, hz = state.shape_param[idx, 0:3].tolist()
                model = mat4_translate((px, py, pz)) @ mat4_scale((hx, hy, hz))
                vao = self._vao_cube

            mvp = proj @ view @ model
            self._prog["u_mvp"].write(mvp.T.tobytes())  # column-major
            self._prog["u_color"].value = (float(color[0]), float(color[1]), float(color[2]), float(color[3]))
            vao.render()

        if self._window is not None:
            self._window.flip()

    # -------------------------
    # Internals
    # -------------------------
    def _make_vao(self, vertices: np.ndarray, indices: np.ndarray):
        vbo = self._ctx.buffer(vertices.astype("f4").tobytes())
        ibo = self._ctx.buffer(indices.astype("u4").tobytes())
        vao = self._ctx.vertex_array(self._prog, [(vbo, "3f", "in_pos")], index_buffer=ibo)
        return vao
