@echo off
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_reports_git.ps1"
if errorlevel 1 (
  echo ERREUR publication reports sur GitHub.
  pause
  exit /b 1
)
exit /b 0
