# pyAIGameEngine snapshot and repo-maintenance scripts

## Canonical local environment variables
- `path_pyAIGameEngine` = project root
- `path_pyEngine_scripts` = project-level Windows scripts folder
- `path_revs_pyAIGameEngine` = snapshot ZIP directory

Historical aliases such as `path_zip_revs` and `path_rev_zip` are retired and should not appear in active scripts or documentation.

## Current reality
- `Apply-LatestSnapshot.ps1` and `Rebuild-ProjectFromSnapshots.ps1` still exist for legacy snapshot workflows.
- Snapshot classification in those scripts remains an **open risk** until the dedicated selector-hardening pass is completed.
- `Replace-RepoWithSnapshot.ps1` is the preferred explicit full-repo replacement path when the goal is cleanup/pruning against a reviewed full snapshot.

## Preferred use cases
- Use `Replace-RepoWithSnapshot.ps1` when you want to replace the repository with a reviewed full snapshot.
- Use the older apply/rebuild scripts only when working within the legacy snapshot family and after verifying which ZIP should be selected.

## Transport and line-ending note
- Prefer downloadable script artifacts or ZIP packages over raw chat copy/paste.
- Keep repo-owned line-ending policy in `.gitattributes`.
- If a pasted script must be saved manually, review its line endings in an editor before commit.

## Example usage
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Replace-RepoWithSnapshot.ps1 -ZipPath C:\path\to\pyAIGameEngine_full_snapshot_2026-03-30_REV4.5_cleanup.zip -RepoRoot C:\PythonDev\Dev1\pyGames\pyAIGameEngine
powershell -ExecutionPolicy Bypass -File .\scripts\windows
un_poc1_validation.ps1 -BackendMode numpy
powershell -ExecutionPolicy Bypass -File .\scripts\windows
un_poc1_integrated_tests.ps1
```
