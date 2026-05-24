@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo Liberation port 8001...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\kill_port_8001.ps1"
if errorlevel 1 (
    echo Nouvelle tentative dans 3 secondes...
    ping -n 3 127.0.0.1 >nul
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\kill_port_8001.ps1"
)

echo.
echo ========================================
echo  DataSens Backend - API E2
echo  http://127.0.0.1:8001/health
echo  Arreter : fermer cette fenetre OU stop_full.bat
echo ========================================
echo.

.venv\Scripts\python.exe run_e2_api.py
set EXITCODE=%ERRORLEVEL%

if not "%EXITCODE%"=="0" (
    echo.
    echo [ERREUR] API arretee - code %EXITCODE%
    echo   1. stop_full.bat
    echo   2. start_full.bat
    echo   3. Gestionnaire des taches : python.exe
    echo.
)

echo.
echo Appuyez sur une touche pour fermer cette fenetre Backend...
pause > nul
exit /b %EXITCODE%
