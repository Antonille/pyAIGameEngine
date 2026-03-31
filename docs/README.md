# docs overview

## How to use this folder
1. Start with `CURRENT_*` pointer files.
2. Read the active revision docs those pointers resolve to.
3. Use `ARCHIVE_INDEX.md` when you need older history or superseded materials.

## Active-surface policy
The docs root is intentionally pruned.
It should contain the current pointers, the active revision targets, and only a few organizing docs.
Historical revision series belong under `docs/archive/`.

## Recommended starting sequence
- `CURRENT_PROJECT_RESOURCE_GUIDE.md`
- `CURRENT_WORKFLOW.md`
- `CURRENT_GITHUB_WORKFLOW.md`
- `CURRENT_LESSON_ACTION_REGISTER.md`
- `CURRENT_NEXT_STEP_PROMPTS.md`
- `CURRENT_ACTIVE_FILE_PATHS.md`
- `CURRENT_TEST_REPORT_PROCEDURE.md`

## Contamination-control note
The active docs now explicitly document:
- canonical environment-variable names
- repo-truth vs snapshot-truth usage
- line-ending policy expectations
- artifact-first file delivery for durable repo content

## Testing/reporting note
When a pass is primarily about validation analysis, report generation, or report-surface cleanup, treat
`CURRENT_TEST_REPORT_PROCEDURE.md` as an active named procedure rather than relying only on older prompt text or
memory.
