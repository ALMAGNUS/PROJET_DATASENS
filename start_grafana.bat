@echo off
REM Demarrer Grafana (Docker) pour le cockpit DataSens
REM Ouvrir ensuite : http://localhost:3001 (login: admin / admin)

cd /d "%~dp0"

echo Verifying Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker absent du PATH.
    pause
    exit /b 1
)
docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo Docker Desktop n est pas demarre ou pas pret.
    echo 1. Lancez Docker Desktop depuis le menu Demarrer
    echo 2. Attendez 30 secondes qu il soit pret
    echo 3. Relancez ce script
    echo.
    pause
    exit /b 1
)

echo Stopping existing container...
docker stop grafana 2>nul
docker rm grafana 2>nul
ping -n 3 127.0.0.1 >nul

echo Starting Grafana on http://localhost:3001 ...
docker run -d --name grafana -p 3001:3001 ^
  -v "%cd%\monitoring\grafana\provisioning:/etc/grafana/provisioning" ^
  -v "%cd%\monitoring\grafana\dashboards:/var/lib/grafana/dashboards" ^
  -e "GF_PATHS_PROVISIONING=/etc/grafana/provisioning" ^
  -e "GF_SERVER_HTTP_PORT=3001" ^
  grafana/grafana

if errorlevel 1 (
    echo Failed to start Grafana.
    pause
    exit /b 1
)

echo.
echo Grafana demarre. Ouvrir : http://localhost:3001 (login admin/admin)
echo.
pause
