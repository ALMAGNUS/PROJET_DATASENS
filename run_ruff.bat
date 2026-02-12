@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat 2>nul
set PYTHONIOENCODING=utf-8
echo [1/2] Ruff check (fix auto)...
ruff check src scripts main.py run_e2_api.py tests --fix
set R1=%errorlevel%
echo.
echo [2/2] Ruff format...
ruff format src scripts main.py run_e2_api.py tests
set R2=%errorlevel%
echo.
if %R1% neq 0 echo Ruff check a signale des erreurs.
if %R2% neq 0 echo Ruff format a signale des differences.
echo Termine. Pour verifier sans corriger: ruff check src scripts main.py run_e2_api.py tests
pause
