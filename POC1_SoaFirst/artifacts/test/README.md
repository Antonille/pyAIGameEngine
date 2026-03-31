# POC1 test artifacts

## Durable truth
- `archive/test_run_archive.jsonl` = append-only archival test history
- `generated/runs/<run_id>/` = durable per-run generated artifacts referenced by archival records
- `baselines/` = frozen comparison-family and projection-assumption baselines

## Regenerable convenience surface
- `../../reports/current/` = latest human-readable current report package
- `../../reports/current/generated/` = latest plots/images derived from archival data

## Policy
Archival JSONL and run-linked generated artifacts are the durable source of truth.
The current report surface is intentionally replaceable and may be regenerated from archival data.
It may still be committed when it improves repo insight, but it should not be treated as the authoritative historical record.
