# POC1 test artifacts

## Durable conventions
- `archive/` = append-only archival test history (`test_run_archive.jsonl`)
- `generated/runs/<run_id>/` = durable per-run generated artifacts referenced by archival records
- `baselines/` = frozen comparison-family and projection-assumption baselines

## Replaceable conventions
- `../../reports/current/` = latest regenerable human-readable report outputs
- `../../reports/current/generated/` = latest regenerable plots/images derived from archival data
