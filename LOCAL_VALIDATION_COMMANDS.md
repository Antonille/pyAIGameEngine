# Local validation commands for REV4.4 workflow-hardening pass

Run from:

`C:\PythonDev\Dev1\pyGames\pyAIGameEngine`

## Basic pointer checks
```powershell
Get-Content .\docs\CURRENT_PROJECT_RESOURCE_GUIDE.md
Get-Content .\docs\CURRENT_WORKFLOW.md
Get-Content .\docs\CURRENT_LESSONS_LEARNED.md
Get-Content .\docs\CURRENT_OPTIMIZED_PROMPTS_AND_TEMPLATES.md
Get-Content .\docs\CURRENT_NEXT_STEP_PROMPTS.md
Get-Content .\docs\CURRENT_LESSON_ACTION_REGISTER.md
```

Expected high-level result:
- the touched `CURRENT_*` files point to `2026 03 30 REV4.4 ...` files
- `CURRENT_LESSON_ACTION_REGISTER.md` points to the new REV4.4 lesson-action register

## Workflow hardening content checks
```powershell
Select-String -Path ".\docs\2026 03 30 REV4.4 Current Workflow.md" -Pattern "flash-capture|pre-pass retrieval|freshness audit|full\+sparse reconciliation"
Select-String -Path ".\docs\2026 03 30 REV4.4 Optimized Prompts and Templates.md" -Pattern "repo-truth|snapshot-truth|supporting local evidence|pre-pass retrieval"
Select-String -Path ".\docs\2026 03 30 REV4.4 Lessons Learned.md" -Pattern "strong capture|follow-through|best practice|open risk"
Select-String -Path ".\docs\2026 03 30 REV4.4 Lesson Action Register.md" -Pattern "LLA-20260330-001|LLA-20260330-002|LLA-20260330-003"
```

Expected high-level result:
- workflow doc contains the new required capture/retrieval/audit rules
- prompts doc distinguishes truth layers and requires lesson retrieval
- lessons doc records the new durable workflow lessons
- lesson-action register contains the seeded high-value open actions

## Repo state check
```powershell
git status
```

Expected high-level result:
- only the intended docs files for this pass are modified or newly added
