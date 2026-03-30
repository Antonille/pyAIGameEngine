from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def make_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(v) for v in value]
    if hasattr(value, "tolist"):
        return make_json_safe(value.tolist())
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


@dataclass
class ArtifactReference:
    artifact_type: str
    relative_path: str
    description: str
    producer: str
    content_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return make_json_safe(asdict(self))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ArtifactReference":
        return cls(**payload)


@dataclass
class MetricRecord:
    metric_name: str
    metric_value: Any
    metric_unit: str
    metric_kind: str
    comparison_key: dict[str, Any] | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return make_json_safe(asdict(self))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MetricRecord":
        return cls(**payload)


@dataclass
class SuiteResultRecord:
    suite_id: str
    suite_category: str
    suite_version: str
    status: str
    checks_passed: int
    checks_failed: int
    checks_skipped: int
    metrics: list[MetricRecord] = field(default_factory=list)
    parameters_used: dict[str, Any] = field(default_factory=dict)
    artifacts: list[ArtifactReference] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metrics"] = [metric.to_dict() for metric in self.metrics]
        payload["artifacts"] = [artifact.to_dict() for artifact in self.artifacts]
        return make_json_safe(payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SuiteResultRecord":
        return cls(
            suite_id=payload["suite_id"],
            suite_category=payload["suite_category"],
            suite_version=payload["suite_version"],
            status=payload["status"],
            checks_passed=int(payload.get("checks_passed", 0)),
            checks_failed=int(payload.get("checks_failed", 0)),
            checks_skipped=int(payload.get("checks_skipped", 0)),
            metrics=[MetricRecord.from_dict(item) for item in payload.get("metrics", [])],
            parameters_used=payload.get("parameters_used", {}),
            artifacts=[ArtifactReference.from_dict(item) for item in payload.get("artifacts", [])],
            summary=payload.get("summary", {}),
        )


@dataclass
class TestRunRecord:
    schema_version: str
    test_harness_version: str
    run_id: str
    timestamp_utc: str
    snapshot_id: str
    workspace_version: str
    poc_version: str
    project_phase: str
    gate_context: str
    execution_mode: str
    host_metadata: dict[str, Any]
    environment_metadata: dict[str, Any]
    git_or_snapshot_notes: dict[str, Any]
    suite_selection: list[str]
    parameter_bundle: dict[str, Any]
    validation_summary: dict[str, Any]
    performance_summary: dict[str, Any]
    comparison_summary: dict[str, Any]
    projection_summary: dict[str, Any]
    development_state_summary: dict[str, Any]
    design_state_summary: dict[str, Any]
    artifact_references: list[ArtifactReference]
    suite_results: list[SuiteResultRecord]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifact_references"] = [artifact.to_dict() for artifact in self.artifact_references]
        payload["suite_results"] = [suite_result.to_dict() for suite_result in self.suite_results]
        return make_json_safe(payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TestRunRecord":
        return cls(
            schema_version=payload["schema_version"],
            test_harness_version=payload["test_harness_version"],
            run_id=payload["run_id"],
            timestamp_utc=payload["timestamp_utc"],
            snapshot_id=payload["snapshot_id"],
            workspace_version=payload["workspace_version"],
            poc_version=payload["poc_version"],
            project_phase=payload["project_phase"],
            gate_context=payload["gate_context"],
            execution_mode=payload["execution_mode"],
            host_metadata=payload.get("host_metadata", {}),
            environment_metadata=payload.get("environment_metadata", {}),
            git_or_snapshot_notes=payload.get("git_or_snapshot_notes", {}),
            suite_selection=list(payload.get("suite_selection", [])),
            parameter_bundle=payload.get("parameter_bundle", {}),
            validation_summary=payload.get("validation_summary", {}),
            performance_summary=payload.get("performance_summary", {}),
            comparison_summary=payload.get("comparison_summary", {}),
            projection_summary=payload.get("projection_summary", {}),
            development_state_summary=payload.get("development_state_summary", {}),
            design_state_summary=payload.get("design_state_summary", {}),
            artifact_references=[ArtifactReference.from_dict(item) for item in payload.get("artifact_references", [])],
            suite_results=[SuiteResultRecord.from_dict(item) for item in payload.get("suite_results", [])],
            notes=list(payload.get("notes", [])),
        )
