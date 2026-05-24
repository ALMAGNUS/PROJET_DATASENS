@echo off
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ========================================
echo  DataSens — demarrage complet
echo ========================================
echo.

echo Nettoyage session precedente...
taskkill /FI "WINDOWTITLE eq DataSensBackend*" /F 2>nul
taskkill /FI "WINDOWTITLE eq DataSensFrontend*" /F 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\kill_port_8001.ps1"
if errorlevel 1 (
    echo.
    echo Port 8001 encore occupe — nouvelle tentative...
    ping -n 3 127.0.0.1 >nul
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\kill_port_8001.ps1"
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING" 2^>nul') do taskkill /PID %%a /F /T 2>nul
ping -n 2 127.0.0.1 >nul

if not exist ".venv\Scripts\activate.bat" (
    echo ERREUR: .venv introuvable. Creez-le avec: python -m venv .venv
    pause
    exit /b 1
)

echo.
echo Demarrage : 2 fenetres Backend + Frontend (restent ouvertes)
echo   Arret propre : stop_full.bat
echo.

REM cmd /k = fenetre reste ouverte (meme en cas d'erreur)
start "DataSensBackend" cmd /k call "%ROOT%_launch_api.bat"

echo Attente demarrage API (port 8001, max ~90 s)...
for /L %%i in (1,1,45) do (
    "%ROOT%.venv\Scripts\python.exe" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=2)" 2>nul && goto api_ready
    ping -n 2 127.0.0.1 >nul
)
echo.
echo ATTENTION: API non detectee.
echo   Regardez la fenetre DataSensBackend (message d'erreur).
echo   Si port 8001 occupe : stop_full.bat puis relancer.
echo.
goto start_cockpit

:api_ready
echo API OK — demarrage du cockpit.

:start_cockpit
start "DataSensFrontend" cmd /k call "%ROOT%_launch_cockpit.bat"

echo.
echo OK — 2 fenetres : DataSensBackend + DataSensFrontend
echo Pour tout arreter : stop_full.bat
echo.
pause
