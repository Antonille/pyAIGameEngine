from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_PROJECTION_BASELINE = {
    "baseline_id": "projection_baseline_v1",
    "frozen_on": "2026-03-30",
    "description": "First frozen weighting set for early complexity-normalized performance estimates.",
    "components": [
        {
            "component_id": "physics_simulation_core",
            "target_weight": 0.45,
            "default_realization_fraction": 1.0,
            "rationale": "Current benchmark directly exercises the fallback-first authoritative simulation loop.",
        },
        {
            "component_id": "scheduler_packet_system",
            "target_weight": 0.20,
            "default_realization_fraction": 1.0,
            "rationale": "Current benchmark and Gate D acceptance cover cadence, freshness, packet, and action-application behavior.",
        },
        {
            "component_id": "adapter_baseline_policy_layer",
            "target_weight": 0.10,
            "default_realization_fraction": 0.35,
            "rationale": "Adapter-facing execution exists only as an early gym rollout path and is not yet the primary benchmark boundary.",
        },
        {
            "component_id": "reporting_instrumentation_overhead",
            "target_weight": 0.05,
            "default_realization_fraction": 0.45,
            "rationale": "The integrated harness and report regeneration now exist, but remain an early first slice rather than the final long-lifecycle system.",
        },
        {
            "component_id": "future_baseline_rl_agent_inference_allowance",
            "target_weight": 0.20,
            "default_realization_fraction": 0.10,
            "rationale": "A learned or richer baseline RL agent is not yet part of the authoritative benchmark path.",
        },
    ],
}


class ProjectionEngine:
    def __init__(self, baseline_path: Path) -> None:
        self.baseline_path = baseline_path
        self.baseline = self._load_or_initialize_baseline()

    def _load_or_initialize_baseline(self) -> dict[str, Any]:
        if self.baseline_path.exists():
            return json.loads(self.baseline_path.read_text(encoding="utf-8"))
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        self.baseline_path.write_text(json.dumps(DEFAULT_PROJECTION_BASELINE, indent=2), encoding="utf-8")
        return DEFAULT_PROJECTION_BASELINE

    def _realization_fraction(self, component_id: str, suite_ids: set[str], suite_status: dict[str, str]) -> float:
        if component_id == "physics_simulation_core":
            return 1.0 if "benchmark_headless_v1" in suite_ids or "smoke_rigidbody_field_v1" in suite_ids else 0.0
        if component_id == "scheduler_packet_system":
            if "benchmark_headless_v1" in suite_ids and suite_status.get("benchmark_headless_v1") == "pass":
                return 1.0
            if "acceptance_gate_d_v1" in suite_ids and suite_status.get("acceptance_gate_d_v1") == "pass":
                return 0.9
            return 0.0
        if component_id == "adapter_baseline_policy_layer":
            if suite_status.get("adapter_rl_rollout_v1") == "pass":
                return 0.60
            if suite_status.get("adapter_rl_rollout_v1") == "skip":
                return 0.25
            return 0.20
        if component_id == "reporting_instrumentation_overhead":
            return 0.45
        if component_id == "future_baseline_rl_agent_inference_allowance":
            if suite_status.get("adapter_rl_rollout_v1") == "pass":
                return 0.18
            return 0.10
        return 0.0

    def build_summary(self, *, primary_ms_per_step: float | None, suite_ids: list[str], suite_status: dict[str, str]) -> dict[str, Any]:
        suite_id_set = set(suite_ids)
        components: list[dict[str, Any]] = []
        complexity_fraction = 0.0
        for item in self.baseline["components"]:
            realization_fraction = self._realization_fraction(item["component_id"], suite_id_set, suite_status)
            weighted_fraction = float(item["target_weight"]) * float(realization_fraction)
            complexity_fraction += weighted_fraction
            components.append(
                {
                    "component_id": item["component_id"],
                    "target_weight": item["target_weight"],
                    "current_realization_fraction": realization_fraction,
                    "weighted_fraction": weighted_fraction,
                    "rationale": item["rationale"],
                }
            )

        summary: dict[str, Any] = {
            "baseline_id": self.baseline["baseline_id"],
            "baseline_path": str(self.baseline_path).replace("\\", "/"),
            "components": components,
            "current_complexity_fraction": complexity_fraction,
        }
        if primary_ms_per_step is not None:
            epsilon = 1e-9
            normalized = float(primary_ms_per_step) / max(complexity_fraction, epsilon)
            projected_steps_per_second = 1000.0 / normalized if normalized else None
            summary.update(
                {
                    "current_measured_ms_per_step": float(primary_ms_per_step),
                    "normalized_ms_per_full_complexity": normalized,
                    "projected_steps_per_second_at_full_complexity": projected_steps_per_second,
                }
            )
        return summary
