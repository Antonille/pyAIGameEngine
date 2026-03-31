# Apply REV4.6 docs update

Copy the files in this package into the repo root, preserving paths.

Suggested commands:
```powershell
$RepoRoot = 'C:\PythonDev\Dev1\pyGames\pyAIGameEngine'
$PackageRoot = 'C:\path\to\pyAIGameEngine_REV4.6_docs_currentize'
robocopy $PackageRoot $RepoRoot /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
git -C $RepoRoot status --short
```

After review:
```powershell
git -C $RepoRoot add -A
git -C $RepoRoot commit -m "Currentize docs for canonical env vars, line endings, and artifact-first workflow"
git -C $RepoRoot push origin main
```
