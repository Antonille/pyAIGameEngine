from __future__ import annotations

import argparse
import json

from poc1_engine.testing.capture import capture_fixed_action_replay_validation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fallback-first fixed-seed fixed-action determinism validation.")
    parser.add_argument("--steps", type=int, default=128)
    parser.add_argument("--backend-mode", choices=["numpy", "numba"], default="numpy")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--action-seed", type=int, default=99)
    args = parser.parse_args()

    payload = capture_fixed_action_replay_validation(
        steps=args.steps,
        backend_mode=args.backend_mode,
        seed=args.seed,
        action_seed=args.action_seed,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["state_equal"] and payload["reward_equal"] and payload["final_observation_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
