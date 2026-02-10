@echo off
REM Demarrer Prometheus en local (scrape l'API E2 sur localhost:8001)
REM Ouvrir ensuite : http://localhost:9090

cd /d "%~dp0"

where prometheus 2>nul || (
    echo Prometheus n'est pas dans le PATH.
    echo Telechargez-le : https://prometheus.io/download/
    echo Ou avec Docker : docker run -d -p 9090:9090 -v "%cd%\monitoring\prometheus.local.yml:/etc/prometheus/prometheus.yml" prom/prometheus
    pause
    exit /b 1
)

echo Starting Prometheus on http://localhost:9090 ...
start "Prometheus" prometheus --config.file=monitoring/prometheus.local.yml --web.enable-lifecycle
echo Prometheus demarre. Ouvrir : http://localhost:9090
pause
