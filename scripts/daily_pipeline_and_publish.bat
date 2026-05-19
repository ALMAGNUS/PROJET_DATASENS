@echo off
REM Run pipeline E1 + rapport db_state + push reports/ sur GitHub.
cd /d "%~dp0.."
call .venv\Scripts\activate.bat
if errorlevel 1 (
  echo ERREUR: activez .venv ou creez-le avec python -m venv .venv
  pause
  exit /b 1
)

echo [1/3] Pipeline E1...
python main.py
if errorlevel 1 (
  echo ERREUR main.py
  pause
  exit /b 1
)

echo [2/3] Rapport db_state...
python scripts\db_state_report.py
if errorlevel 1 (
  echo ERREUR db_state_report.py
  pause
  exit /b 1
)

echo [3/3] Publication reports/ sur GitHub...
call scripts\publish_reports_git.bat
exit /b %errorlevel%
