@echo off
REM Demarrer Prometheus en local (scrape l'API E2 sur localhost:8001)
REM Ouvrir ensuite : http://localhost:9090

cd /d "%~dp0"

where prometheus >nul 2>&1
if errorlevel 1 (
    echo Prometheus absent du PATH.
    echo Telechargez : https://prometheus.io/download/
    pause
    exit /b 1
)

echo Starting Prometheus on http://localhost:9090 ...
start "Prometheus" prometheus --config.file=monitoring/prometheus.local.yml --web.enable-lifecycle
echo Prometheus demarre. Ouvrir : http://localhost:9090
pause
