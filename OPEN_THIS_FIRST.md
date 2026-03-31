# pyAIGameEngine REV4.4 workflow-hardening sparse refresh

This package is a **docs-first retrospective/process-improvement pass** prepared against the public `main` branch of `Antonille/pyAIGameEngine`.

## What this package contains
- A new lightweight lesson-action register
- REV4.4 updates for:
  - Project Resource Guide
  - Current Workflow
  - Lessons Learned
  - Optimized Prompts and Templates
  - Current Next-Step Prompts
- Updated `CURRENT_*` pointer files for the docs touched in this pass

## Intended local destination
Copy these files into:

`C:\PythonDev\Dev1\pyGames\pyAIGameEngine\`

preserving the included `docs/` paths.

## Suggested copy/check sequence
1. Extract this package somewhere temporary.
2. Review the files under `docs/`.
3. Copy the included files into the local repo root, preserving paths.
4. Run the validation commands listed in `LOCAL_VALIDATION_COMMANDS.md`.
5. Review `git status`.
6. Commit with a message like:

```powershell
git add docs
git commit -m "Harden workflow with lesson-action register and retrieval gates"
```

7. Push when satisfied:

```powershell
git push
```

## Scope boundary for this pass
This package does **not** rewrite snapshot scripts or refresh the stale root README.
Those are left as the next bounded implementation/maintenance pass.

## Main outcomes
- Converts lessons from narrative-only into tracked actions with evidence and status
- Requires pre-pass retrieval of relevant lessons
- Requires flash-capture after failures/breakdowns/clarifications
- Adds current-pointer freshness audit and full+sparse reconciliation audit before authoritative relay/full snapshot publication
- Distinguishes:
  - repo-truth
  - snapshot-truth
  - supporting local evidence

## Recommended next pass
Use `docs/CURRENT_NEXT_STEP_PROMPTS.md` after this package is applied.
