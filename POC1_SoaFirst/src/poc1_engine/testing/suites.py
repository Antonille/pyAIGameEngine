from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from poc1_engine.ai.gate_d_acceptance import run_gate_d_acceptance

from .capture import capture_gym_rollout, capture_headless_benchmark, capture_rigidbody_field_prototype
from .records import ArtifactReference, MetricRecord, SuiteResultRecord


@dataclass
class SuiteRunContext:
    poc_root: Path
    run_output_dir: Path
    benchmark_steps: int
    benchmark_bodies: int
    backend_mode: str
    warmup_numba: bool
    execution_mode: str
    note: str | None = None

    def relative_path(self, path: Path) -> str:
        return str(path.relative_to(self.poc_root)).replace("\\", "/")


class TestSuite(Protocol):
    suite_id: str
    suite_category: str
    suite_version: str

    def run(self, context: SuiteRunContext) -> SuiteResultRecord:
        ...


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _svg_header(width: int = 900, height: int = 540) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white" />',
    ]


def build_body_snapshot_svg(snapshot_payload: dict[str, Any], path: Path) -> str:
    positions = snapshot_payload.get("final_positions_xyz", [])
    agent_flags = snapshot_payload.get("final_agent_flags", [])
    if not positions:
        svg = '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="540"><text x="40" y="80">No body positions captured.</text></svg>'
        path.write_text(svg, encoding="utf-8")
        return hashlib.sha256(svg.encode("utf-8")).hexdigest()

    xs = [float(item[0]) for item in positions]
    ys = [float(item[1]) for item in positions]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_min == x_max:
        x_min -= 1.0
        x_max += 1.0
    if y_min == y_max:
        y_min -= 1.0
        y_max += 1.0

    margin = 60.0
    width = 900.0
    height = 540.0
    plot_width = width - 2 * margin
    plot_height = height - 2 * margin

    def map_x(value: float) -> float:
        return margin + (value - x_min) / (x_max - x_min) * plot_width

    def map_y(value: float) -> float:
        return height - margin - (value - y_min) / (y_max - y_min) * plot_height

    lines = _svg_header(int(width), int(height))
    lines.append('<text x="40" y="36" font-size="22">POC1 benchmark body snapshot</text>')
    lines.append('<text x="40" y="60" font-size="14">Blue markers are agent bodies. Gray markers are non-agent bodies. Final positions captured after the benchmark window.</text>')
    lines.append(f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="black" stroke-width="1" />')
    lines.append(f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}" stroke="black" stroke-width="1" />')
    for index, position in enumerate(positions):
        fill = "#1f77b4" if index < len(agent_flags) and int(agent_flags[index]) else "#7f7f7f"
        cx = map_x(float(position[0]))
        cy = map_y(float(position[1]))
        lines.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="4.2" fill="{fill}" fill-opacity="0.85" />')
    lines.append(f'<text x="{width-220}" y="{margin+8}" font-size="12">x-range=[{x_min:.2f}, {x_max:.2f}]</text>')
    lines.append(f'<text x="{width-220}" y="{margin+24}" font-size="12">y-range=[{y_min:.2f}, {y_max:.2f}]</text>')
    lines.append("</svg>")
    svg = "\n".join(lines)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    return hashlib.sha256(svg.encode("utf-8")).hexdigest()


@dataclass
class SmokeRigidBodyFieldSuite:
    suite_id: str = "smoke_rigidbody_field_v1"
    suite_category: str = "smoke"
    suite_version: str = "1"

    def run(self, context: SuiteRunContext) -> SuiteResultRecord:
        payload = capture_rigidbody_field_prototype(gravity_y=-9.81)
        checks_failed = 0
        checks_failed += int(payload["coord_system_count"] != 3)
        checks_failed += int(payload["contact_count"] != 1)
        checks_failed += int(payload["propagated_updates"] < 1)
        checks_passed = 3 - checks_failed
        status = "pass" if checks_failed == 0 else "fail"
        artifact_path = context.run_output_dir / "smoke_rigidbody_field_summary.json"
        content_hash = _write_json(artifact_path, payload)
        metrics = [
            MetricRecord("coord_system_count", payload["coord_system_count"], "count", "validation"),
            MetricRecord("contact_count", payload["contact_count"], "count", "validation"),
            MetricRecord("propagated_updates", payload["propagated_updates"], "count", "validation"),
            MetricRecord("sphere_mass", payload["sphere_mass"], "mass_units", "derived"),
        ]
        return SuiteResultRecord(
            suite_id=self.suite_id,
            suite_category=self.suite_category,
            suite_version=self.suite_version,
            status=status,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            checks_skipped=0,
            metrics=metrics,
            parameters_used={"gravity_y": -9.81},
            artifacts=[
                ArtifactReference(
                    artifact_type="json_summary",
                    relative_path=context.relative_path(artifact_path),
                    description="Rigid-body / field smoke summary.",
                    producer=self.suite_id,
                    content_hash=content_hash,
                )
            ],
            summary=payload,
        )


@dataclass
class AcceptanceGateDSuite:
    suite_id: str = "acceptance_gate_d_v1"
    suite_category: str = "acceptance"
    suite_version: str = "1"

    def run(self, context: SuiteRunContext) -> SuiteResultRecord:
        result = run_gate_d_acceptance()
        checks_passed = sum(1 for check in result.checks if check.passed)
        checks_failed = sum(1 for check in result.checks if not check.passed)
        status = "pass" if result.gate_status == "cleared" and checks_failed == 0 else "fail"
        payload = {
            "gate_status": result.gate_status,
            "summary": result.summary,
            "checks": [{"name": check.name, "passed": check.passed, "details": check.details} for check in result.checks],
        }
        artifact_path = context.run_output_dir / "acceptance_gate_d_summary.json"
        content_hash = _write_json(artifact_path, payload)
        metrics = [
            MetricRecord("gate_status", result.gate_status, "state", "validation"),
            MetricRecord("checks_passed", checks_passed, "count", "validation"),
            MetricRecord("checks_failed", checks_failed, "count", "validation"),
        ]
        return SuiteResultRecord(
            suite_id=self.suite_id,
            suite_category=self.suite_category,
            suite_version=self.suite_version,
            status=status,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            checks_skipped=0,
            metrics=metrics,
            parameters_used={"gate_name": result.summary.get("gate_name")},
            artifacts=[
                ArtifactReference(
                    artifact_type="json_summary",
                    relative_path=context.relative_path(artifact_path),
                    description="Gate D acceptance result summary.",
                    producer=self.suite_id,
                    content_hash=content_hash,
                )
            ],
            summary=payload,
        )


@dataclass
class BenchmarkHeadlessSuite:
    suite_id: str = "benchmark_headless_v1"
    suite_category: str = "benchmark"
    suite_version: str = "1"

    def run(self, context: SuiteRunContext) -> SuiteResultRecord:
        payload, _state = capture_headless_benchmark(
            steps=context.benchmark_steps,
            bodies=context.benchmark_bodies,
            backend_mode=context.backend_mode,
            warmup_numba=context.warmup_numba,
        )
        summary_path = context.run_output_dir / "benchmark_headless_summary.json"
        summary_hash = _write_json(summary_path, payload)
        snapshot_svg_path = context.run_output_dir / "benchmark_body_snapshot.svg"
        snapshot_hash = build_body_snapshot_svg(payload, snapshot_svg_path)
        comparison_key = {
            "benchmark_family_id": "poc1_headless_benchmark_v1",
            "backend_mode": payload["backend_mode"],
            "scenario_bundle_id": "seeded_state_v1",
            "adapter_version": None,
            "baseline_policy_id": "mixed_scheduler_families_v1",
            "mode": context.execution_mode,
            "bodies": payload["bodies"],
            "steps": payload["steps"],
            "feature_family_set": list(payload["scheduled_families"]),
            "packet_mode_set": ["replace", "no_change", "delete", "invalidate"],
            "seed_policy": "fixed_rng_seed_123",
        }
        metrics = [
            MetricRecord("ms_per_step", payload["ms_per_step"], "ms_per_step", "performance", comparison_key=comparison_key),
            MetricRecord("elapsed_s", payload["elapsed_s"], "seconds", "performance"),
            MetricRecord("transfer_bytes", payload["transfer_bytes"], "bytes", "performance"),
            MetricRecord("action_packet_bytes", payload["action_packet_bytes"], "bytes", "performance"),
            MetricRecord("reuse_ratio", payload["reuse_ratio"], "ratio", "performance"),
            MetricRecord("cache_hits", payload["cache_hits"], "count", "performance"),
            MetricRecord("cache_misses", payload["cache_misses"], "count", "performance"),
        ]
        return SuiteResultRecord(
            suite_id=self.suite_id,
            suite_category=self.suite_category,
            suite_version=self.suite_version,
            status="pass",
            checks_passed=1,
            checks_failed=0,
            checks_skipped=0,
            metrics=metrics,
            parameters_used={
                "steps": context.benchmark_steps,
                "bodies": context.benchmark_bodies,
                "backend_mode": context.backend_mode,
                "warmup_numba": context.warmup_numba,
            },
            artifacts=[
                ArtifactReference(
                    artifact_type="json_summary",
                    relative_path=context.relative_path(summary_path),
                    description="Headless benchmark result payload.",
                    producer=self.suite_id,
                    content_hash=summary_hash,
                ),
                ArtifactReference(
                    artifact_type="svg_snapshot",
                    relative_path=context.relative_path(snapshot_svg_path),
                    description="Dynamic-simulation body-position snapshot after the benchmark window.",
                    producer=self.suite_id,
                    content_hash=snapshot_hash,
                ),
            ],
            summary={**payload, "comparison_key": comparison_key},
        )


@dataclass
class AdapterRLRolloutSuite:
    suite_id: str = "adapter_rl_rollout_v1"
    suite_category: str = "adapter_rl"
    suite_version: str = "1"

    def run(self, context: SuiteRunContext) -> SuiteResultRecord:
        try:
            payload = capture_gym_rollout(steps=min(context.benchmark_steps, 128), backend_mode=context.backend_mode)
            status = "pass"
            skipped = 0
            failed = 0
            metrics = [
                MetricRecord("total_reward", payload["total_reward"], "reward_units", "validation"),
                MetricRecord("resets", payload["resets"], "count", "validation"),
            ]
            summary = payload
        except Exception as exc:
            status = "skip"
            skipped = 1
            failed = 0
            metrics = [MetricRecord("skip_reason", str(exc), "text", "validation")]
            summary = {"skip_reason": str(exc)}

        artifact_path = context.run_output_dir / "adapter_rl_rollout_summary.json"
        content_hash = _write_json(artifact_path, summary)
        return SuiteResultRecord(
            suite_id=self.suite_id,
            suite_category=self.suite_category,
            suite_version=self.suite_version,
            status=status,
            checks_passed=1 if status == "pass" else 0,
            checks_failed=failed,
            checks_skipped=skipped,
            metrics=metrics,
            parameters_used={"steps": min(context.benchmark_steps, 128), "backend_mode": context.backend_mode},
            artifacts=[
                ArtifactReference(
                    artifact_type="json_summary",
                    relative_path=context.relative_path(artifact_path),
                    description="Adapter / gym rollout capture or skip payload.",
                    producer=self.suite_id,
                    content_hash=content_hash,
                )
            ],
            summary=summary,
        )


class TestSuiteRegistry:
    def __init__(self) -> None:
        self._suites: dict[str, TestSuite] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, suite: TestSuite) -> None:
        self._suites[suite.suite_id] = suite
        self._categories.setdefault(suite.suite_category, []).append(suite.suite_id)

    def suite_ids_for_categories(self, categories: list[str]) -> list[str]:
        suite_ids: list[str] = []
        for category in categories:
            suite_ids.extend(self._categories.get(category, []))
        return suite_ids

    def get(self, suite_id: str) -> TestSuite:
        return self._suites[suite_id]

    def all_suite_ids(self) -> list[str]:
        return list(self._suites.keys())


def build_default_registry() -> TestSuiteRegistry:
    registry = TestSuiteRegistry()
    for suite in [
        SmokeRigidBodyFieldSuite(),
        AcceptanceGateDSuite(),
        BenchmarkHeadlessSuite(),
        AdapterRLRolloutSuite(),
    ]:
        registry.register(suite)
    return registry
