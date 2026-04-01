# OPEN THIS REPO FIRST

This repository's `main` branch is the current authoritative repo-truth for pyAIGameEngine when GitHub connector access is available.

## Open first
1. `README.md`
2. `docs/README.md`
3. Current pointer docs in `docs/` beginning with `CURRENT_`
4. The active dated docs those pointers resolve to

## Operating truth
- Fallback-first CPU-authoritative runtime truth remains the default validated path.
- PyBullet remains optional and deferred unless later validated work explicitly changes that truth.
- On 2026-03-31, **repo-write relay** became the preferred working mode when GitHub connector access is available.
- In repo-write relay mode, treat GitHub `main` as the source of truth for documentation and handoff state, and write small surgical commits instead of generating detached side artifacts when a direct repo update is appropriate.

## Route by task
### Project status / handoff
Open:
- `docs/CURRENT_PROJECT_RESOURCE_GUIDE.md`
- `docs/CURRENT_WORKFLOW.md`
- `docs/CURRENT_LESSONS_LEARNED.md`
- `docs/CURRENT_NEXT_STEP_PROMPTS.md`
- `docs/CURRENT_OPTIMIZED_PROMPTS_AND_TEMPLATES.md`

### Implementation / architecture follow-on
Open the current pointer docs first, then the active dated docs they reference.
Preserve fallback-first CPU-authoritative truth and do not broaden into new engine features unless the prompt explicitly asks for it.

### Benchmark / validation follow-on
Search for:
- `benchmark compare`
- `POC1_SoaFirst`
- `fallback-first`
- `CPU-authoritative`
- `PyBullet optional`

### Documentation maintenance
When updating project truth:
- update the active dated doc first
- update the matching `CURRENT_*.md` pointer/reference surface
- keep handoff language compact and restartable
- prefer repo-write relay when direct GitHub connector write access is available

## Useful search seeds
- `repo-write relay`
- `CURRENT_WORKFLOW`
- `CURRENT_PROJECT_RESOURCE_GUIDE`
- `CURRENT_NEXT_STEP_PROMPTS`
- `REV4.9`
- `fallback-first`
- `PyBullet optional deferred`
- `POC1_SoaFirst`

## Maintenance notes
- Keep this file compact and practical.
- If current active docs change, update this router so future chats can land on the right entry points quickly.
- Do not change runtime truth here unless the validated project docs have already changed.
