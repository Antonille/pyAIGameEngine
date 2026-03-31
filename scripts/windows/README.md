# pyAIGameEngine snapshot and repo-maintenance scripts

Canonical local paths:
- project root: `C:\PythonDev\Dev1\pyGames\pyAIGameEngine`
- project-level scripts: `C:\PythonDev\Dev1\pyGames\pyAIGameEngine\scripts\windows`
- snapshot ZIP directory: `C:\PythonDev\Dev1\pyGames\Revs_pyAIGameEngine`

## Current reality
- `Apply-LatestSnapshot.ps1` and `Rebuild-ProjectFromSnapshots.ps1` still exist for legacy snapshot workflows.
- Snapshot classification in those scripts remains an **open risk** because it still depends on filename patterns such as `full_snapshot` and `sparse_snapshot`.
- This cleaned full snapshot adds `Replace-RepoWithSnapshot.ps1` for explicit full-repo replacement from a chosen ZIP.

## Preferred use cases
- Use `Replace-RepoWithSnapshot.ps1` when you want to replace the repository with a reviewed full snapshot.
- Use the older apply/rebuild scripts only when working within the legacy snapshot family and after verifying which ZIP should be selected.

## Example usage
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Replace-RepoWithSnapshot.ps1 -ZipPath C:\path	o\pyAIGameEngine_full_snapshot_2026-03-30_REV4.5_cleanup.zip -RepoRoot C:\PythonDev\Dev1\pyGames\pyAIGameEngine
powershell -ExecutionPolicy Bypass -File .\scripts\windowsun_poc1_validation.ps1 -BackendMode numpy
powershell -ExecutionPolicy Bypass -File .\scripts\windowsun_poc1_integrated_tests.ps1
```
