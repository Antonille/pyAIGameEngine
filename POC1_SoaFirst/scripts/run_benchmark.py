from __future__ import annotations

import argparse
import json

from poc1_engine.testing.capture import capture_headless_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="POC1 headless benchmark")
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--bodies", type=int, default=1024)
    parser.add_argument("--backend-mode", choices=["numpy", "numba"], default="numpy")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--warmup-numba", action="store_true")
    args = parser.parse_args()

    payload, _state = capture_headless_benchmark(
        steps=args.steps,
        bodies=args.bodies,
        backend_mode=args.backend_mode,
        warmup_numba=args.warmup_numba,
    )

    if args.json:
        print(json.dumps(payload))
        return 0

    print(f"backend={payload['backend']}")
    print(f"steps={payload['steps']}")
    print(f"bodies={payload['bodies']}")
    print(f"elapsed_s={payload['elapsed_s']:.6f}")
    print(f"ms_per_step={payload['ms_per_step']:.6f}")
    print(f"events={payload['events']}")
    print(f"agent_obs_shape={tuple(payload['agent_obs_shape'])}")
    print(f"visible_count={payload['visible_count']}")
    print(f"hit_ground_query_count={payload['hit_ground_query_count']}")
    print(f"scheduled_families={payload['scheduled_families']}")
    print(f"schedule_counts={payload['schedule_counts']}")
    print(f"transfer_batches={payload['transfer_batches']}")
    print(f"transfer_entities={payload['transfer_entities']}")
    print(f"transfer_bytes={payload['transfer_bytes']}")
    print(f"action_packets={payload['action_packets']}")
    print(f"action_packet_entities={payload['action_packet_entities']}")
    print(f"action_packet_bytes={payload['action_packet_bytes']}")
    print(f"cache_hits={payload['cache_hits']}")
    print(f"cache_misses={payload['cache_misses']}")
    print(f"cache_invalidations={payload['cache_invalidations']}")
    print(f"reuse_ratio={payload['reuse_ratio']:.3f}")
    print(f"no_change_count={payload['no_change_count']}")
    print(f"delete_count={payload['delete_count']}")
    print(f"invalidate_count={payload['invalidate_count']}")
    print(f"applied_packets={payload['applied_packets']}")
    print(f"applied_packet_bytes={payload['applied_packet_bytes']}")
    print(f"applied_no_change_count={payload['applied_no_change_count']}")
    print(f"applied_delete_count={payload['applied_delete_count']}")
    print(f"applied_invalidate_count={payload['applied_invalidate_count']}")
    for line in payload['last_transfer_plan_lines']:
        print(f"transfer::{line}")
    for line in payload['last_action_packet_lines']:
        print(f"action_packet::{line}")
    for name, avg_ms in payload['stage_avg_ms'].items():
        print(f"stage::{name}: avg_ms={avg_ms:.6f} total_ms={avg_ms * payload['steps']:.6f} count={payload['steps']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
