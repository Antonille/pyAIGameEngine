from __future__ import annotations

import argparse
from pathlib import Path

from poc1_engine.testing.harness import HarnessConfig, IntegratedTestHarness
from poc1_engine.testing.suites import build_default_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the integrated pyAIGameEngine archival test harness.")
    parser.add_argument("--backend-mode", choices=["numpy", "numba"], default="numpy")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--bodies", type=int, default=1024)
    parser.add_argument("--warmup-numba", action="store_true")
    parser.add_argument("--execution-mode", default="benchmark")
    parser.add_argument("--suite-group", choices=["core", "with_adapter", "all"], default="core")
    parser.add_argument("--suite-id", action="append", default=[])
    parser.add_argument("--snapshot-id", default="candidate_snapshot")
    parser.add_argument("--note", default=None)
    args = parser.parse_args()

    poc_root = Path(__file__).resolve().parents[1]
    registry = build_default_registry()
    if args.suite_id:
        suite_ids = args.suite_id
    elif args.suite_group == "core":
        suite_ids = ["smoke_rigidbody_field_v1", "acceptance_gate_d_v1", "benchmark_headless_v1"]
    elif args.suite_group == "with_adapter":
        suite_ids = [
            "smoke_rigidbody_field_v1",
            "acceptance_gate_d_v1",
            "benchmark_headless_v1",
            "adapter_rl_rollout_v1",
            "determinism_replay_v1",
        ]
    else:
        suite_ids = registry.all_suite_ids()

    config = HarnessConfig(
        poc_root=poc_root,
        suite_ids=suite_ids,
        benchmark_steps=args.steps,
        benchmark_bodies=args.bodies,
        backend_mode=args.backend_mode,
        warmup_numba=args.warmup_numba,
        execution_mode=args.execution_mode,
        snapshot_id=args.snapshot_id,
        note=args.note,
    )
    harness = IntegratedTestHarness(config=config, registry=registry)
    record = harness.run()

    print(f"run_id={record.run_id}")
    print(f"archive_path={harness.archive_path}")
    print(f"current_report_markdown={poc_root / 'reports' / 'current' / 'current_test_report.md'}")
    print(f"current_report_html={poc_root / 'reports' / 'current' / 'current_test_report.html'}")
    print(f"overall_status={record.validation_summary.get('overall_status')}")
    print(f"checks_passed={record.validation_summary.get('checks_passed')}")
    print(f"checks_failed={record.validation_summary.get('checks_failed')}")
    print(f"checks_skipped={record.validation_summary.get('checks_skipped')}")
    if record.performance_summary.get('primary_metric_ms_per_step') is not None:
        print(f"primary_ms_per_step={record.performance_summary['primary_metric_ms_per_step']:.6f}")
        print(f"normalized_ms_per_full_complexity={record.projection_summary.get('normalized_ms_per_full_complexity')}")
    return 0 if record.validation_summary.get("checks_failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
