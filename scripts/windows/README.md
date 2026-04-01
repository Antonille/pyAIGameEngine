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
- Root-level `Apply-PackageFromRevs.ps1` is the preferred generic package-apply helper for reviewed ZIP or folder packages from the revisions directory.

## Validation helpers
- `run_poc1_validation.ps1` = wrapper for fallback validation / rollout path
- `run_poc1_integrated_tests.ps1` = wrapper for the integrated harness
- `POC1_SoaFirst/scripts/validate_configurable_interface.py` = direct configurable-interface manifest validation/compile step

## Example usage
```powershell
powershell -ExecutionPolicy Bypass -File .\Apply-PackageFromRevs.ps1 pyAIGameEngine_full_snapshot_2026-03-31_REV4.9_configurable_interface_full_snapshot.zip -SyncMode Mirror
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_poc1_validation.ps1 -BackendMode numpy
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_poc1_integrated_tests.ps1 -BackendMode numpy -SuiteGroup core
.\.venv\Scripts\python.exe .\POC1_SoaFirst\scripts\validate_configurable_interface.py --emit-doc --output-json
```
