from __future__ import annotations

import argparse

from poc1_engine.testing.capture import capture_rigidbody_field_prototype


def main() -> int:
    parser = argparse.ArgumentParser(description="POC1 rigid-body/field prototype")
    parser.add_argument("--gravity-y", type=float, default=-9.81)
    args = parser.parse_args()

    payload = capture_rigidbody_field_prototype(gravity_y=args.gravity_y)
    for key, value in payload.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
