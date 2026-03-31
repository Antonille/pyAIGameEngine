Apply this sparse refresh into the repo root.

Suggested usage from repo root after placing the folder or ZIP in the revisions area:

```powershell
pwsh -ExecutionPolicy Bypass -File .\Apply-PackageFromRevs.ps1 pyAIGameEngine_REV4.8_test_report_procedure_update.zip
git status --short
git add -A
git commit -m "Adopt named Test Report Procedure in active docs"
git push origin main
```
