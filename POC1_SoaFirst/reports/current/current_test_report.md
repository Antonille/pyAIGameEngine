# pyAIGameEngine Current Test Report
Generated from archival test data and uploaded artifacts on 2026-03-30.

## 1. Executive summary
Current accepted testing truth now includes:
- fallback-first CPU path remains validated
- smoke rigid-body / gravity / field prototype remains sane
- Phase 3 Gate D scheduler and packet acceptance gate is cleared
- the first integrated long-lifecycle testing/reporting slice is working
- an adapter-facing rollout path is exercised end-to-end
- the repository is now the primary shared workflow surface, with archival test data as durable test truth

Main accepted limitations:
- representative benchmark history is still short
- simulation-credibility suites remain not yet implemented
- the adapter boundary is exercised, but not yet hardened as the long-term canonical RL contract
- the complexity-normalized projection remains an early heuristic, not a final forecasting model

## 2. Re-validation summary
### Previously validated capabilities revalidated
- fallback-first execution remains authoritative and passing
- rigid-body / gravity / field prototype remains physically sane
- scheduler cadence / freshness / fallback / batchability logic remains passing
- packet replace / delta / no-change / delete behavior remains passing

### Newly accepted capabilities
- integrated test harness archival append-only workflow is now accepted as working practice
- report regeneration from archival truth is now accepted as a working subsystem behavior
- adapter-facing rollout evidence is now part of accepted project truth

### Gate status
- Gate D status: **cleared**
- Expected schedule counts matched observed counts for:
  - agent_reflex_v1 = 10
  - agent_contextual_v1 = 5
  - agent_hold_v1 = 20
  - agent_cleanup_v1 = 20

## 3. Performance summary
### Accepted benchmark runs from archive
| Run ID | Backend | Steps | Bodies | Suites | Checks Passed | ms/step | Normalized ms/full complexity | Projected steps/s at full complexity |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| 20260330T212833Z_65de9cef | numpy | 500 | 1024 | smoke_rigidbody_field_v1, acceptance_gate_d_v1, benchmark_headless_v1 | 260 | 0.683961 | 0.959946 | 1041.73 |
| 20260330T213014Z_837c1c2e | numpy | 500 | 1024 | smoke_rigidbody_field_v1, acceptance_gate_d_v1, benchmark_headless_v1 | 260 | 0.772331 | 1.083974 | 922.53 |
| 20260330T223549Z_e477839b | numba | 500 | 1024 | smoke_rigidbody_field_v1, acceptance_gate_d_v1, benchmark_headless_v1 | 260 | 0.685022 | 0.961435 | 1040.11 |
| 20260330T223601Z_2f24359a | numpy | 300 | 512 | smoke_rigidbody_field_v1, acceptance_gate_d_v1, benchmark_headless_v1, adapter_rl_rollout_v1 | 261 | 0.583748 | 0.759594 | 1316.49 |

### Current accepted latest run
- Run ID: `20260330T223601Z_2f24359a`
- Backend: `numpy`
- Benchmark shape: `300 steps / 512 bodies`
- Overall status: `pass`
- Checks: `261 passed / 0 failed / 0 skipped`
- Primary performance: `0.583748 ms/step`
- Complexity-normalized projection: `0.759594 ms/step`
- Projected throughput at full modeled complexity: `1316.49 steps/s`

### Apples-to-apples comparison notes
- The 500-step / 1024-body benchmark family now has accepted results for both numpy and numba.
- Best accepted numpy at 500 / 1024: `0.683961 ms/step` from `20260330T212833Z_65de9cef`.
- Accepted numba at 500 / 1024: `0.685022 ms/step` from `20260330T223549Z_e477839b`.
- Interpretation: best current numpy is faster than current numba by 0.001061 ms/step (0.16%).

This means the current accepted evidence no longer supports the stronger earlier shorthand claim that “warmed numba wins” without qualification. The accepted integrated evidence now says numpy and numba are currently **close enough that no decisive benchmark-runtime winner should be locked in yet** for this benchmark shape.

### Adapter-facing benchmark summary
Accepted uploaded adapter/headless benchmark evidence:
- `ms_per_step = 0.583748`
- `reuse_ratio = 0.623030`
- `action_packets = 825`
- `cache_hits = 514`
- `cache_misses = 311`
- `events.total = 92`

Stage-average timing from the uploaded benchmark:
- `ai = 0.304423 ms`
- `render_snapshot = 0.066478 ms`
- `action_application = 0.055089 ms`
- `physics = 0.052748 ms`
- `observation_build = 0.045316 ms`
- `event_processing = 0.042173 ms`

Interpretation: on the current accepted adapter-facing benchmark, AI/scheduling/packet-side orchestration remains the largest average stage cost, not raw fallback physics.

## 4. Visualization section
Generated plots:
- `generated/performance_history.svg`
- `generated/apples_to_apples_500_1024.svg`

Uploaded simulation snapshot artifact:
- `generated/benchmark_body_snapshot.svg`

### Snapshot significance note
`benchmark_body_snapshot.svg` is retained as a key render-facing artifact because it ties the current integrated benchmark/reporting flow back to visible simulation geometry rather than purely scalar timing output. It is useful as the first accepted visual anchor for later report evolution.

## 5. Projection section
Current accepted projection model remains provisional.

Latest run projection:
- measured ms/step: `0.583748`
- current complexity fraction: `0.768500`
- normalized ms/full complexity: `0.759594`
- projected steps/s at full complexity: `1316.49`

Projection assumptions reflected in the accepted archive:
- physics simulation core is treated as fully realized in the current benchmark path
- scheduler_packet_system is treated as fully realized in the current benchmark path
- adapter_baseline_policy_layer is only partially realized
- reporting_instrumentation_overhead is only partially realized
- future baseline RL agent inference allowance is still lightly represented

Interpretation:
- use the projection as a continuity metric, not a final forecast
- large movements should be interpreted alongside benchmark shape changes and architecture maturity
- the current latest run is useful, but still not a stable long-horizon trend anchor

## 6. Appendix
### Implemented vs unimplemented
Implemented now:
- IntegratedTestHarness
- append-only archival JSONL writer
- smoke, acceptance, benchmark, and optional adapter rollout suites
- first compatibility-key comparison path
- first complexity-normalized projection path
- current report markdown/html regeneration scaffold

Not yet implemented:
- rich regression matrix
- simulation-credibility suite implementations
- stable long-horizon benchmark history
- richer export/render stack

### Test parameter table
| Accepted Run | Backend | Steps | Bodies | Snapshot ID | Suite Selection |
|---|---|---:|---:|---|---|
| 20260330T212833Z_65de9cef | numpy | 500 | 1024 | local_candidate | smoke_rigidbody_field_v1, acceptance_gate_d_v1, benchmark_headless_v1 |
| 20260330T213014Z_837c1c2e | numpy | 500 | 1024 | local_candidate | smoke_rigidbody_field_v1, acceptance_gate_d_v1, benchmark_headless_v1 |
| 20260330T223549Z_e477839b | numba | 500 | 1024 | local_candidate_numba | smoke_rigidbody_field_v1, acceptance_gate_d_v1, benchmark_headless_v1 |
| 20260330T223601Z_2f24359a | numpy | 300 | 512 | local_candidate_adapter | smoke_rigidbody_field_v1, acceptance_gate_d_v1, benchmark_headless_v1, adapter_rl_rollout_v1 |

### Uploaded artifact appendix
- acceptance gate summary: `acceptance_gate_d_summary.json`
- adapter rollout summary: `adapter_rl_rollout_summary.json`
- benchmark headless summary: `benchmark_headless_summary.json`
- smoke rigidbody field summary: `smoke_rigidbody_field_summary.json`
- benchmark body snapshot: `benchmark_body_snapshot.svg`

### Brief justification of assumptions
- Gate D clearance is accepted because the uploaded gate summary reports `gate_status = cleared` and the packet-chain semantics are consistent with prior accepted interface direction.
- The adapter rollout is accepted as evidence of exercised adapter readiness, but not yet as proof of a final canonical RL boundary.
- The latest 512-body adapter benchmark is accepted as useful current evidence, but not directly apples-to-apples with the 500 / 1024 benchmark family.
