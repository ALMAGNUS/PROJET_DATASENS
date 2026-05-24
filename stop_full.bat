@echo off
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ========================================
echo  Arret DataSens (API + Cockpit)
echo ========================================
echo.

echo [1/3] Arret API (port 8001)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\kill_port_8001.ps1"

echo [2/3] Arret Cockpit (port 8501)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F /T 2>nul
)

echo [3/3] Fermeture fenetres DataSensBackend / DataSensFrontend...
taskkill /FI "WINDOWTITLE eq DataSensBackend*" /F 2>nul
taskkill /FI "WINDOWTITLE eq DataSensFrontend*" /F 2>nul

ping -n 2 127.0.0.1 >nul
echo.
echo Termine. Si une fenetre cmd reste ouverte, fermez-la avec la croix ou Ctrl+C.
echo Relancer : start_full.bat
echo.
