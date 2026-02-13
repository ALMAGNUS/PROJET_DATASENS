@echo off
set "ROOT=%~dp0"
cd /d "%ROOT%"

REM Liberer les ports (API 8001, Streamlit 8501, Prometheus 9090, Grafana 3000)
echo Liberation des ports 8001 8501 9090 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" 2^>nul') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" 2^>nul') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9090" 2^>nul') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" 2^>nul') do taskkill /PID %%a /F 2>nul
ping -n 2 127.0.0.1 >nul

if not exist ".venv\Scripts\activate.bat" (
    echo ERREUR: .venv introuvable. Creez-le avec: python -m venv .venv
    pause
    exit /b 1
)

echo Demarrage DataSens : Backend (API) + Frontend (Cockpit)
echo.
echo Terminal 1 = Backend  (port 8001) - ne pas fermer
echo Terminal 2 = Frontend (port 8501) - ne pas fermer
echo.
echo Ports: API 8001, Cockpit 8501
echo.
start "DataSensBackend" cmd /k call "%ROOT%_launch_api.bat"
ping -n 4 127.0.0.1 >nul
start "DataSensFrontend" cmd /k call "%ROOT%_launch_cockpit.bat"
echo.
echo Deux fenetres ouvertes. Pour arreter : fermer les 2 terminaux Backend et Frontend.
pause
