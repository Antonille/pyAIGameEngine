from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_mode(python_exe: str, script: str, mode: str, steps: int, bodies: int, warmup_numba: bool) -> dict:
    cmd = [python_exe, script, "--steps", str(steps), "--bodies", str(bodies), "--backend-mode", mode, "--json"]
    if warmup_numba and mode == "numba":
        cmd.append("--warmup-numba")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare numpy vs numba benchmark modes")
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--benchmark-script", default=str(Path(__file__).with_name("run_benchmark.py")))
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--bodies", type=int, default=1024)
    parser.add_argument("--warmup-numba", action="store_true")
    args = parser.parse_args()

    numpy_result = run_mode(args.python_exe, args.benchmark_script, "numpy", args.steps, args.bodies, args.warmup_numba)
    numba_result = run_mode(args.python_exe, args.benchmark_script, "numba", args.steps, args.bodies, args.warmup_numba)

    numpy_ms = numpy_result["ms_per_step"]
    numba_ms = numba_result["ms_per_step"]
    ratio = (numpy_ms / numba_ms) if numba_ms else None

    print(f"numpy_ms_per_step={numpy_ms:.6f}")
    print(f"numba_ms_per_step={numba_ms:.6f}")
    if ratio is not None:
        print(f"numpy_over_numba_ratio={ratio:.3f}")
        if ratio > 1.0:
            print("winner=numba")
        else:
            print("winner=numpy")

    print("numpy_stage_ai_ms={:.6f}".format(numpy_result["stage_avg_ms"].get("ai", 0.0)))
    print("numba_stage_ai_ms={:.6f}".format(numba_result["stage_avg_ms"].get("ai", 0.0)))
    print("numpy_stage_physics_ms={:.6f}".format(numpy_result["stage_avg_ms"].get("physics", 0.0)))
    print("numba_stage_physics_ms={:.6f}".format(numba_result["stage_avg_ms"].get("physics", 0.0)))
    print("numpy_stage_render_snapshot_ms={:.6f}".format(numpy_result["stage_avg_ms"].get("render_snapshot", 0.0)))
    print("numba_stage_render_snapshot_ms={:.6f}".format(numba_result["stage_avg_ms"].get("render_snapshot", 0.0)))
    print(f"numpy_transfer_batches={numpy_result['transfer_batches']}")
    print(f"numba_transfer_batches={numba_result['transfer_batches']}")
    print(f"numpy_transfer_bytes={numpy_result['transfer_bytes']}")
    print(f"numba_transfer_bytes={numba_result['transfer_bytes']}")
    print(f"numpy_action_packets={numpy_result['action_packets']}")
    print(f"numba_action_packets={numba_result['action_packets']}")
    print(f"numpy_action_packet_bytes={numpy_result['action_packet_bytes']}")
    print(f"numba_action_packet_bytes={numba_result['action_packet_bytes']}")
    print(f"numpy_cache_hits={numpy_result['cache_hits']}")
    print(f"numba_cache_hits={numba_result['cache_hits']}")
    print(f"numpy_cache_misses={numpy_result['cache_misses']}")
    print(f"numba_cache_misses={numba_result['cache_misses']}")
    print(f"numpy_cache_invalidations={numpy_result['cache_invalidations']}")
    print(f"numba_cache_invalidations={numba_result['cache_invalidations']}")
    print(f"numpy_reuse_ratio={numpy_result['reuse_ratio']:.3f}")
    print(f"numba_reuse_ratio={numba_result['reuse_ratio']:.3f}")
    print(f"numpy_no_change_count={numpy_result['no_change_count']}")
    print(f"numba_no_change_count={numba_result['no_change_count']}")
    print(f"numpy_delete_count={numpy_result['delete_count']}")
    print(f"numba_delete_count={numba_result['delete_count']}")
    print(f"numpy_invalidate_count={numpy_result['invalidate_count']}")
    print(f"numba_invalidate_count={numba_result['invalidate_count']}")
    print(f"warmup_numba={args.warmup_numba}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
