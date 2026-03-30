# pyAIGameEngine snapshot workflow scripts

Canonical local paths:
- project root: `C:\PythonDev\Dev1\pyGames\pyAIGameEngine`
- project-level scripts: `C:\PythonDev\Dev1\pyGames\pyAIGameEngine\scripts\windows`
- snapshot ZIP directory: `C:\PythonDev\Dev1\pyGames\Revs_pyAIGameEngine`

## Standard snapshot layout going forward
All newly created full and sparse snapshots should contain a top-level folder named:

`pyAIGameEngine/`

That is the standard layout now used by the snapshot creation scripts.

## Compatibility behavior
The apply/rebuild scripts detect both:
- standard rooted snapshots containing `pyAIGameEngine/`
- older legacy sparse snapshots that placed project files directly at ZIP root

For legacy rootless sparse snapshots, wrapper files such as `OPEN_THIS_FIRST.md` and `SNAPSHOT_INDEX.json` are ignored during apply/rebuild.

## Main scripts
- `Apply-LatestSnapshot.ps1`
- `Rebuild-ProjectFromSnapshots.ps1`
- `New-SparseSnapshot.ps1`
- `New-FullSnapshot.ps1`

## Example usage
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Apply-LatestSnapshot.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Apply-LatestSnapshot.ps1 -PreferFull
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Rebuild-ProjectFromSnapshots.ps1 -ClearProject
powershell -ExecutionPolicy Bypass -File .\scripts\windows\New-SparseSnapshot.ps1 -SinceMode LastAny
powershell -ExecutionPolicy Bypass -File .\scripts\windows\New-FullSnapshot.ps1
```

## Notes
- `Apply-LatestSnapshot.ps1` overlays files into the project directory. It can overwrite matching files, but it does not delete extra files already present.
- `Rebuild-ProjectFromSnapshots.ps1 -ClearProject` can be used when you want a cleaner reconstruction from the latest full snapshot plus later sparse snapshots.
- Snapshot classification is still based on filename patterns containing `full_snapshot` or `sparse_snapshot`.
