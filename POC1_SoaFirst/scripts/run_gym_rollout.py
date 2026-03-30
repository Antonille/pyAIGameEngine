from __future__ import annotations

import argparse

from poc1_engine.testing.capture import capture_gym_rollout


def main() -> int:
    parser = argparse.ArgumentParser(description="POC1 Gym rollout")
    parser.add_argument("--steps", type=int, default=256)
    parser.add_argument("--backend-mode", choices=["numpy", "numba"], default="numpy")
    args = parser.parse_args()

    payload = capture_gym_rollout(steps=args.steps, backend_mode=args.backend_mode)
    print(f"backend={payload['backend']}")
    print(f"total_reward={payload['total_reward']:.6f}")
    print(f"last_event_summary={payload['last_event_summary']}")
    print(f"resets={payload['resets']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
