@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0export_snapshot.ps1" %*
