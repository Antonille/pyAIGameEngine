# REV4.6 script rewrite — install and smoke-test commands

## Install from extracted package
```powershell
powershell -ExecutionPolicy Bypass -File .\Install-UpdatedSnapshotScripts.ps1 -BackupExisting
```

```powershell
pwsh -File .\Install-UpdatedSnapshotScripts.ps1 -BackupExisting
```

## Show the resolved candidate list
```powershell
powershell -ExecutionPolicy Bypass -File "$env:path_pyEngine_scripts\Apply-LatestSnapshot.ps1" -ListOnly
```

```powershell
pwsh -File "$env:path_pyEngine_scripts\Apply-LatestSnapshot.ps1" -ListOnly
```

## Apply latest snapshot and configure local git identity
```powershell
powershell -ExecutionPolicy Bypass -File "$env:path_pyEngine_scripts\Apply-LatestSnapshot.ps1" -SnapshotKind any -SyncMode Overlay -ConfigureGitIdentity
```

## Create snapshots
```powershell
powershell -ExecutionPolicy Bypass -File "$env:path_pyEngine_scripts\New-SparseSnapshot.ps1" -SinceMode LastAny
powershell -ExecutionPolicy Bypass -File "$env:path_pyEngine_scripts\New-FullSnapshot.ps1"
```

## Apply latest full snapshot as cleanup replacement and push
```powershell
powershell -ExecutionPolicy Bypass -File "$env:path_pyEngine_scripts\Apply-LatestSnapshot.ps1" -SnapshotKind full -SyncMode Replace -CommitAndPush -SetRemoteUrl
```

## Rebuild from latest full plus later sparse/patch snapshots
```powershell
powershell -ExecutionPolicy Bypass -File "$env:path_pyEngine_scripts\Rebuild-ProjectFromSnapshots.ps1" -ClearProject
```
