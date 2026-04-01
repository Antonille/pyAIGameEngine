# Current pyAIGameEngine Test Report

Generated from archival test data on 2026-04-01T00:16:06Z.

## 1. Human-oriented consumer summary of current test data

- Current run ID: `20260401T001605Z_1c431726`
- Timestamp (UTC): `2026-04-01T00:16:05Z`
- Workspace version: `0.0.25` | POC version: `0.1.15`
- Execution mode: `benchmark` | Gate context: `Pre-Gate-A, deterministic reset/replay and adapter refit`
- Suite selection: smoke_rigidbody_field_v1, acceptance_gate_d_v1, benchmark_headless_v1
- Summary of re-validation of previous success/failure metrics: smoke_rigidbody_field_v1, acceptance_gate_d_v1, benchmark_headless_v1
- Summary of new success/failure metrics: No newly introduced suite IDs in this run.
- Validation summary: passed=262 failed=0 skipped=0 overall_status=pass
- Configurable interface manifest: `agent_hot_control_manifest_v1` version `1.0.0`
- Configurable interface validation status: `pass`
- Configurable interface runtime binding: `compiled_startup_plan_v1`

### Performance Tests and Results

- Primary benchmark metric: `0.638939 ms/step`
- Backend: `simple_integrator:numba`
- Benchmark family: `poc1_headless_benchmark_v1`
- Bodies / steps: `1024 / 500`
- Compatible prior runs found: `1`
- Delta vs latest compatible run: `-0.04608279999229126` ms/step

### Visualization of Tests

- Raw performance plot: `reports/current/generated/raw_performance_over_time.svg`
- Apples-to-apples plot: `reports/current/generated/apples_to_apples_performance.svg`
- Projection plot: `reports/current/generated/complexity_normalized_projection.svg`
- Dynamic simulation snapshot: `artifacts/test/generated/runs/20260401T001605Z_1c431726/benchmark_body_snapshot.svg`
- Snapshot significance: this render captures the final benchmark-frame spatial distribution of bodies and distinguishes agent bodies from non-agent bodies so later regressions in geometry or broad motion can be visually spotted.

## 2. Numerical and visual comparison between current and previous performance and guidance toward future performance

- Raw performance vs time uses all archival benchmark runs found in `artifacts/test/archive/test_run_archive.jsonl`.
- Apples-to-apples comparison uses exact compatibility-key matches on benchmark family, backend, scenario bundle, mode, bodies, steps, feature families, packet modes, and seed policy.
- Current complexity fraction: `0.7125`
- Complexity-normalized projected full-complexity metric: `0.8967570526312971` ms/step
- Projected full-complexity steps/sec estimate: `1115.1292282182378`
- Guidance toward future performance: The current apples-to-apples point improved materially. Preserve the same comparison key on the next run to confirm the gain is stable.

## 3. Appendix

### Current state of development (implemented vs unimplemented)

- Implemented: integrated_test_harness_v1, append_only_test_run_archive_v1, benchmark_history_loader_v1, comparison_rules_v1, projection_method_v1, regenerable_current_report_builder_v1, deterministic_reset_replay_validation_v1, packet_oriented_minimal_env_adapter_v1, startup_compiled_configurable_interface_slice_v1
- Unimplemented: full_regression_suite_matrix, simulation_credibility_suite_implementation, rich_adapter_rl_benchmark_matrix, binary_or_columnar_archive_mirror, pdf_report_generation
- Current limitations: comparison history is exact-key and file-based only, projection method is provisional and assumption-heavy, current report visuals are lightweight SVG scaffolds, adapter_rl suite remains thin and not a public RL API commitment, configurable interface implementation remains limited to a hot control-plane subset

### Table of test parameters used

| Parameter | Value |
|---|---|
| backend_mode | numba |
| benchmark_bodies | 1024 |
| benchmark_steps | 500 |
| execution_mode | benchmark |
| suite_ids | ['smoke_rigidbody_field_v1', 'acceptance_gate_d_v1', 'benchmark_headless_v1'] |
| warmup_numba | True |

### Configurable interface validation metadata

- Manifest hash: `f8beb573d8738806636ef7fb931db5e5ef9d48d196c0e855c096a63568566d79`
- Validator version/hash: `configurable_interface_validator_v1` / `abbb0cd1e06cae7dd39f81afc19e5aed958834b67f7ff4a02f6b00191dae3ab8`
- Compiled channels: `['agent_hot_observation_v1', 'agent_hot_action_v1']`

### Brief justification of assumptions made

| Assumption | Justification |
|---|---|
| physics_simulation_core | weight=0.45, realization=1.0; Current benchmark directly exercises the fallback-first authoritative simulation loop. |
| scheduler_packet_system | weight=0.2, realization=1.0; Current benchmark and Gate D acceptance cover cadence, freshness, packet, and action-application behavior. |
| adapter_baseline_policy_layer | weight=0.1, realization=0.2; Adapter-facing execution exists only as an early gym rollout path and is not yet the primary benchmark boundary. |
| reporting_instrumentation_overhead | weight=0.05, realization=0.45; The integrated harness and report regeneration now exist, but remain an early first slice rather than the final long-lifecycle system. |
| future_baseline_rl_agent_inference_allowance | weight=0.2, realization=0.1; A learned or richer baseline RL agent is not yet part of the authoritative benchmark path. |

### Compatibility notes for trend comparison

- Comparison key: `{'benchmark_family_id': 'poc1_headless_benchmark_v1', 'backend_mode': 'numba', 'scenario_bundle_id': 'seeded_state_v1', 'adapter_version': None, 'baseline_policy_id': 'mixed_scheduler_families_v1', 'mode': 'benchmark', 'bodies': 1024, 'steps': 500, 'feature_family_set': ['agent_cleanup_v1', 'agent_contextual_v1', 'agent_hold_v1', 'agent_reflex_v1'], 'packet_mode_set': ['replace', 'no_change', 'delete', 'invalidate'], 'seed_policy': 'fixed_rng_seed_123'}`
- Compatible prior run IDs: ['20260330T223549Z_e477839b']

### Artifact list
- `artifacts/test/generated/runs/20260401T001605Z_1c431726/smoke_rigidbody_field_summary.json` — Rigid-body / field smoke summary.
- `artifacts/test/generated/runs/20260401T001605Z_1c431726/acceptance_gate_d_summary.json` — Gate D acceptance result summary.
- `artifacts/test/generated/runs/20260401T001605Z_1c431726/benchmark_headless_summary.json` — Headless benchmark result payload.
- `artifacts/test/generated/runs/20260401T001605Z_1c431726/benchmark_body_snapshot.svg` — Dynamic-simulation body-position snapshot after the benchmark window.
