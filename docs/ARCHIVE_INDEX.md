# docs archive index

## Purpose
This index explains where superseded material was moved during the REV4.5 cleanup/consolidation pass and why the active surface remains intentionally small.

## Archive layout
- `archive/legacy_current_folder/` — old duplicated `docs/current/` surface that conflicted with `CURRENT_*` pointers
- `archive/legacy_benchmarks/` — older benchmark helper materials moved out of the active surface
- `archive/revision_series/resource_guides/` — superseded resource guide revisions
- `archive/revision_series/current_workflows/` — superseded workflow revisions
- `archive/revision_series/next_step_prompts/` — superseded next-step prompt revisions
- `archive/revision_series/lessons_learned/` — superseded lessons revisions
- `archive/revision_series/optimized_prompts/` — superseded prompt-template revisions
- `archive/revision_series/bootstrap_prompts/` — superseded bootstrap prompt revisions
- `archive/revision_series/workflow_procedures/` — superseded relay/retrospective/workflow-procedure docs
- `archive/revision_series/project_instructions/` — superseded instruction revisions
- `archive/revision_series/specialized_specs/` — historical milestone/spec docs that are no longer part of the active top-level surface
- `archive/2026 03 30 REV4.5 Consolidated Modification History.md` — concatenated modification-history archive
- `archive/2026 03 30 REV4.5 Consolidated Project State Manifest History.md` — concatenated state-manifest archive

## Active-surface rule
The docs root should now hold only:
- `CURRENT_*` pointer files
- the currently targeted revision docs those pointers resolve to
- a small number of active organizing docs (`README.md`, this archive index, cleanup summary)

## Note
Archive placement is meant to reduce restart confusion, not to erase history.
It also reduces the chance that stale docs, stale path aliases, or stale process instructions contaminate the next pass.
