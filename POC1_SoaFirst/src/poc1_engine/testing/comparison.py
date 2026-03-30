from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .records import TestRunRecord


REQUIRED_COMPARISON_FIELDS = (
    "benchmark_family_id",
    "backend_mode",
    "scenario_bundle_id",
    "adapter_version",
    "baseline_policy_id",
    "mode",
    "bodies",
    "steps",
    "feature_family_set",
    "packet_mode_set",
    "seed_policy",
)


class CompatibilityRuleSet:
    required_fields = REQUIRED_COMPARISON_FIELDS

    def normalize_key(self, comparison_key: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for field in self.required_fields:
            value = comparison_key.get(field)
            if isinstance(value, list):
                normalized[field] = tuple(value)
            else:
                normalized[field] = value
        return normalized

    def are_compatible(self, left: dict[str, Any], right: dict[str, Any]) -> bool:
        return self.normalize_key(left) == self.normalize_key(right)


class ComparisonEngine:
    def __init__(self, rules: CompatibilityRuleSet | None = None) -> None:
        self.rules = rules or CompatibilityRuleSet()

    def load_archive(self, archive_path: Path) -> list[TestRunRecord]:
        if not archive_path.exists():
            return []
        records: list[TestRunRecord] = []
        with archive_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                records.append(TestRunRecord.from_dict(json.loads(line)))
        return records

    def find_compatible_runs(self, current_record: TestRunRecord, history: list[TestRunRecord]) -> list[TestRunRecord]:
        current_key = current_record.performance_summary.get("comparison_key")
        if not current_key:
            return []
        compatible: list[TestRunRecord] = []
        for record in history:
            record_key = record.performance_summary.get("comparison_key")
            if record_key and self.rules.are_compatible(current_key, record_key):
                compatible.append(record)
        return compatible

    def build_summary(self, current_record: TestRunRecord, history: list[TestRunRecord]) -> dict[str, Any]:
        compatible = self.find_compatible_runs(current_record, history)
        all_benchmark_runs = [record for record in history if record.performance_summary.get("primary_metric_ms_per_step") is not None]
        summary: dict[str, Any] = {
            "compatible_run_ids": [record.run_id for record in compatible],
            "compatible_count": len(compatible),
            "all_benchmark_run_count": len(all_benchmark_runs),
            "comparison_key": current_record.performance_summary.get("comparison_key", {}),
        }
        if compatible:
            previous = compatible[-1]
            current_ms = current_record.performance_summary.get("primary_metric_ms_per_step")
            previous_ms = previous.performance_summary.get("primary_metric_ms_per_step")
            if current_ms is not None and previous_ms is not None:
                delta_ms = float(current_ms) - float(previous_ms)
                delta_pct = (delta_ms / float(previous_ms) * 100.0) if previous_ms else None
            else:
                delta_ms = None
                delta_pct = None
            summary.update(
                {
                    "latest_compatible_run_id": previous.run_id,
                    "latest_compatible_timestamp_utc": previous.timestamp_utc,
                    "latest_compatible_ms_per_step": previous_ms,
                    "delta_ms_per_step_vs_latest_compatible": delta_ms,
                    "delta_percent_vs_latest_compatible": delta_pct,
                }
            )
        return summary
