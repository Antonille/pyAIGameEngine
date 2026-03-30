from __future__ import annotations

from pathlib import Path

from poc1_engine.testing.harness import HarnessConfig, IntegratedTestHarness


def main() -> int:
    poc_root = Path(__file__).resolve().parents[1]
    harness = IntegratedTestHarness(HarnessConfig(poc_root=poc_root, suite_ids=[]))
    current_record, history = harness.regenerate_current_report()
    print(f"report_regenerated_for_run_id={current_record.run_id}")
    print(f"archive_entries={len(history)}")
    print(f"current_report_markdown={poc_root / 'reports' / 'current' / 'current_test_report.md'}")
    print(f"current_report_html={poc_root / 'reports' / 'current' / 'current_test_report.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
