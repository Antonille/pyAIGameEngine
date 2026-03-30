from __future__ import annotations

import json

from poc1_engine.ai.gate_d_acceptance import run_gate_d_acceptance


def main() -> int:
    result = run_gate_d_acceptance()
    print(f"gate={result.summary['gate_name']}")
    print(f"gate_status={result.gate_status}")
    print(f"schedule_counts={result.summary['schedule_counts']}")
    print(f"expected_schedule_counts={result.summary['expected_schedule_counts']}")
    print(f"synthetic_batch_sizes={result.summary['synthetic_batch_sizes']}")
    for check in result.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"check::{status}::{check.name}::{check.details}")
    print("summary_json=" + json.dumps(result.summary, sort_keys=True))
    return 0 if result.gate_status == "cleared" else 1


if __name__ == "__main__":
    raise SystemExit(main())
