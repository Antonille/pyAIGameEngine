# pyAIGameEngine Windows snapshot scripts — REV4.6 rewrite

These scripts were rewritten to reduce truth drift and make the workflow safer under both **Windows PowerShell 5.1** and **PowerShell 7+ / pwsh**.

## Runtime compatibility
All scripts are written to run under:
- `powershell.exe` (Windows PowerShell 5.1)
- `pwsh.exe` (PowerShell 7+)

## Environment variables used
The scripts prefer these environment variables and validate them before doing work:
- `path_pyAIGameEngine` = repo root
- `path_pyEngine_scripts` = `...\pyAIGameEngine\scripts\windows`
- `path_revs_pyAIGameEngine` = revisions/snapshots folder

If `path_pyAIGameEngine` is missing or mis-pointed, the scripts derive project root from `path_pyEngine_scripts`.
If `path_revs_pyAIGameEngine` is missing, the scripts default to a sibling `Revs_pyAIGameEngine` folder next to the repo root.

## Reliability changes
- Utility ZIPs are excluded from snapshot selection.
- Snapshot kinds supported: `full`, `sparse`, `patch`, `any`.
- Snapshot manifests are written to new full/sparse snapshots as `pyAIGameEngine/SNAPSHOT_INDEX.json`.
- `Apply-LatestSnapshot.ps1` supports:
  - `Overlay` mode for additive apply
  - `Replace` mode for cleanup/full replacement while preserving top-level items such as `.git` and `.venv`
- Apply/rebuild scripts refuse to run against a dirty git worktree unless `-AllowDirtyRepo` is specified.
- Git identity is configured locally in the repo when commit/push flow is requested.
- Remote URL can be updated explicitly with `-SetRemoteUrl`.
- GitHub username resolution prefers existing `origin` owner to avoid typos; otherwise it falls back to `GITHUB_USERNAME`, then `Antonille`.

## Git defaults
- git user.email = `Scott.Antonille@gmail.com`
- git user.name  = `Scott Antonille`
- repo name      = `pyAIGameEngine`
- branch         = `main`

## Main scripts
- `pyAIGameEngine.Common.ps1`
- `Apply-LatestSnapshot.ps1`
- `Rebuild-ProjectFromSnapshots.ps1`
- `New-SparseSnapshot.ps1`
- `New-FullSnapshot.ps1`

## Example usage
List candidates:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Apply-LatestSnapshot.ps1 -ListOnly
pwsh -File .\scripts\windows\Apply-LatestSnapshot.ps1 -ListOnly
```

Apply latest snapshot additively:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Apply-LatestSnapshot.ps1 -SnapshotKind any -SyncMode Overlay
```

Apply latest full snapshot as cleanup replacement:
```powershell
pwsh -File .\scripts\windows\Apply-LatestSnapshot.ps1 -SnapshotKind full -SyncMode Replace
```

Rebuild from latest full + later sparse/patch snapshots:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Rebuild-ProjectFromSnapshots.ps1 -ClearProject
```

Create sparse snapshot:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\New-SparseSnapshot.ps1 -SinceMode LastAny
```

Create full snapshot:
```powershell
pwsh -File .\scripts\windows\New-FullSnapshot.ps1
```

Apply, configure git identity, commit, and push:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Apply-LatestSnapshot.ps1 -SnapshotKind full -SyncMode Replace -CommitAndPush -SetRemoteUrl
```
