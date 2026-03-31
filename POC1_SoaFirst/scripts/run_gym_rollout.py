from __future__ import annotations

import argparse

from poc1_engine.testing.capture import capture_gym_rollout
from poc1_engine.testing.cli_logging import configure_console_tee


def main() -> int:
    parser = argparse.ArgumentParser(description="POC1 Gym rollout")
    parser.add_argument("--steps", type=int, default=256)
    parser.add_argument("--backend-mode", choices=["numpy", "numba"], default="numpy")
    parser.add_argument("--console-log-path", default=None)
    args = parser.parse_args()

    configure_console_tee(args.console_log_path)

    payload = capture_gym_rollout(steps=args.steps, backend_mode=args.backend_mode)
    print(f"backend={payload['backend']}")
    print(f"control_path={payload.get('control_path')}")
    print(f"total_reward={payload['total_reward']:.6f}")
    print(f"last_event_summary={payload['last_event_summary']}")
    print(f"resets={payload['resets']}")
    print(f"last_packet_apply_summary={payload.get('last_packet_apply_summary')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
