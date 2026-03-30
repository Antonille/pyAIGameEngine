from __future__ import annotations

import json
import platform
import socket
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .comparison import ComparisonEngine
from .projection import ProjectionEngine
from .records import TestRunRecord
from .reporting import CurrentTestReportBuilder
from .suites import SuiteRunContext, TestSuiteRegistry, build_default_registry

SCHEMA_VERSION = "1.0"
HARNESS_VERSION = "0.1.1"


@dataclass
class HarnessConfig:
    poc_root: Path
    suite_ids: list[str]
    benchmark_steps: int = 500
    benchmark_bodies: int = 1024
    backend_mode: str = "numpy"
    warmup_numba: bool = False
    execution_mode: str = "benchmark"
    note: str | None = None
    snapshot_id: str = "candidate_snapshot"
    project_phase: str = "Post-Gate-D, testing/reporting plus AI-boundary hardening"
    gate_context: str = "Pre-Gate-A, deterministic reset/replay and adapter refit"


class IntegratedTestHarness:
    def __init__(self, config: HarnessConfig, registry: TestSuiteRegistry | None = None) -> None:
        self.config = config
        self.registry = registry or build_default_registry()
        self.archive_dir = config.poc_root / "artifacts" / "test" / "archive"
        self.generated_runs_dir = config.poc_root / "artifacts" / "test" / "generated" / "runs"
        self.baselines_dir = config.poc_root / "artifacts" / "test" / "baselines"
        self.archive_path = self.archive_dir / "test_run_archive.jsonl"
        self.comparison_engine = ComparisonEngine()
        self.report_builder = CurrentTestReportBuilder(config.poc_root)
        self.projection_engine = ProjectionEngine(self.baselines_dir / "projection_baseline_v1.json")

    def _load_versions(self) -> tuple[str, str]:
        import tomllib

        workspace_payload = tomllib.loads((self.config.poc_root.parent / "pyproject.toml").read_text(encoding="utf-8"))
        poc_payload = tomllib.loads((self.config.poc_root / "pyproject.toml").read_text(encoding="utf-8"))
        return str(workspace_payload["project"]["version"]), str(poc_payload["project"]["version"])

    def _host_metadata(self) -> dict[str, Any]:
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_executable": sys.executable,
            "python_version": sys.version.replace("\n", " "),
        }

    def _environment_metadata(self) -> dict[str, Any]:
        return {
            "backend_mode": self.config.backend_mode,
            "benchmark_steps": self.config.benchmark_steps,
            "benchmark_bodies": self.config.benchmark_bodies,
            "warmup_numba": self.config.warmup_numba,
            "cwd": str(self.config.poc_root).replace("\\", "/"),
        }

    def _parameter_bundle(self) -> dict[str, Any]:
        return {
            "benchmark_steps": self.config.benchmark_steps,
            "benchmark_bodies": self.config.benchmark_bodies,
            "backend_mode": self.config.backend_mode,
            "warmup_numba": self.config.warmup_numba,
            "execution_mode": self.config.execution_mode,
            "suite_ids": list(self.config.suite_ids),
        }

    def _development_state_summary(self) -> dict[str, Any]:
        return {
            "implemented_components": [
                "integrated_test_harness_v1",
                "append_only_test_run_archive_v1",
                "benchmark_history_loader_v1",
                "comparison_rules_v1",
                "projection_method_v1",
                "regenerable_current_report_builder_v1",
                "deterministic_reset_replay_validation_v1",
                "packet_oriented_minimal_env_adapter_v1",
            ],
            "unimplemented_components": [
                "full_regression_suite_matrix",
                "simulation_credibility_suite_implementation",
                "rich_adapter_rl_benchmark_matrix",
                "binary_or_columnar_archive_mirror",
                "pdf_report_generation",
            ],
            "current_gate_status": "testing_reporting_slice_plus_adapter_boundary_refinement",
            "current_limitations": [
                "comparison history is exact-key and file-based only",
                "projection method is provisional and assumption-heavy",
                "current report visuals are lightweight SVG scaffolds",
                "adapter_rl suite remains thin and not a public RL API commitment",
            ],
            "assumptions": [
                "archival JSONL remains the durable truth for this phase",
                "current reports are replaceable derivatives of archival history",
                "current benchmark family stays conservative for apples-to-apples tracking",
            ],
        }

    def _design_state_summary(self) -> dict[str, Any]:
        return {
            "adopted_design_choices": [
                "append_only_jsonl_archive",
                "current_report_regenerated_from_archive",
                "exact_compatibility_key_matching_for_apples_to_apples",
                "frozen_projection_weight_baseline_with_per_run_realization_fractions",
                "per_run_generated_artifacts_under_artifacts/test/generated/runs",
                "minimal_env_adapter_uses_packet_boundary",
            ],
            "deferred_design_choices": [
                "parquet_or_sql_mirror",
                "richer_plotting_stack",
                "distributed_or_remote_test_execution",
                "full_rl_training_result_integration",
            ],
            "currently_evaluated_choices": [
                "how broad the first stable benchmark family should remain",
                "when to add simulation-credibility and regression suites",
                "how to evolve projection assumptions without breaking trend readability",
            ],
        }

    def _aggregate_validation_summary(self, suite_results: list[Any]) -> dict[str, Any]:
        checks_passed = sum(item.checks_passed for item in suite_results)
        checks_failed = sum(item.checks_failed for item in suite_results)
        checks_skipped = sum(item.checks_skipped for item in suite_results)
        if checks_failed:
            overall_status = "fail"
        elif checks_passed:
            overall_status = "pass"
        else:
            overall_status = "inconclusive"
        return {
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "checks_skipped": checks_skipped,
            "overall_status": overall_status,
            "suite_statuses": {suite.suite_id: suite.status for suite in suite_results},
        }

    def _build_performance_summary(self, suite_results: list[Any]) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        for suite in suite_results:
            if suite.suite_id != "benchmark_headless_v1":
                continue
            for metric in suite.metrics:
                if metric.metric_name == "ms_per_step":
                    summary["primary_metric_ms_per_step"] = float(metric.metric_value)
                    summary["comparison_key"] = metric.comparison_key or {}
            summary["backend_label"] = suite.summary.get("backend")
            summary["benchmark_suite_id"] = suite.suite_id
            summary["benchmark_summary"] = suite.summary
        return summary

    def _append_archive_record(self, record: TestRunRecord) -> None:
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        with self.archive_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")

    def run(self) -> TestRunRecord:
        workspace_version, poc_version = self._load_versions()
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        run_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
        run_output_dir = self.generated_runs_dir / run_id
        run_output_dir.mkdir(parents=True, exist_ok=True)

        context = SuiteRunContext(
            poc_root=self.config.poc_root,
            run_output_dir=run_output_dir,
            benchmark_steps=self.config.benchmark_steps,
            benchmark_bodies=self.config.benchmark_bodies,
            backend_mode=self.config.backend_mode,
            warmup_numba=self.config.warmup_numba,
            execution_mode=self.config.execution_mode,
            note=self.config.note,
        )

        suite_results = []
        for suite_id in self.config.suite_ids:
            suite = self.registry.get(suite_id)
            suite_results.append(suite.run(context))

        validation_summary = self._aggregate_validation_summary(suite_results)
        performance_summary = self._build_performance_summary(suite_results)
        projection_summary = self.projection_engine.build_summary(
            primary_ms_per_step=performance_summary.get("primary_metric_ms_per_step"),
            suite_ids=[suite.suite_id for suite in suite_results],
            suite_status=validation_summary["suite_statuses"],
        )

        record = TestRunRecord(
            schema_version=SCHEMA_VERSION,
            test_harness_version=HARNESS_VERSION,
            run_id=run_id,
            timestamp_utc=timestamp,
            snapshot_id=self.config.snapshot_id,
            workspace_version=workspace_version,
            poc_version=poc_version,
            project_phase=self.config.project_phase,
            gate_context=self.config.gate_context,
            execution_mode=self.config.execution_mode,
            host_metadata=self._host_metadata(),
            environment_metadata=self._environment_metadata(),
            git_or_snapshot_notes={"snapshot_id": self.config.snapshot_id, "note": self.config.note},
            suite_selection=list(self.config.suite_ids),
            parameter_bundle=self._parameter_bundle(),
            validation_summary=validation_summary,
            performance_summary=performance_summary,
            comparison_summary={},
            projection_summary=projection_summary,
            development_state_summary=self._development_state_summary(),
            design_state_summary=self._design_state_summary(),
            artifact_references=[artifact for suite in suite_results for artifact in suite.artifacts],
            suite_results=suite_results,
            notes=[note for note in [self.config.note] if note],
        )

        history = self.comparison_engine.load_archive(self.archive_path)
        record.comparison_summary = self.comparison_engine.build_summary(record, history)
        self._append_archive_record(record)
        record.artifact_references.extend(self.report_builder.build(current_record=record, history=history))
        return record

    def regenerate_current_report(self) -> tuple[TestRunRecord, list[TestRunRecord]]:
        history = self.comparison_engine.load_archive(self.archive_path)
        if not history:
            raise RuntimeError(f"No archival test history found at {self.archive_path}")
        current_record = history[-1]
        self.report_builder.build(current_record=current_record, history=history[:-1])
        return current_record, history
