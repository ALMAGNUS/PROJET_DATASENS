@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist ".venv\Scripts\activate.bat" (
    echo ERREUR: .venv introuvable. Creez-le avec: python -m venv .venv
    pause
    exit /b 1
)

echo Liberation des ports 8001, 8501 et 27017...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" 2^>nul') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" 2^>nul') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":27017" 2^>nul') do taskkill /PID %%a /F 2>nul
ping -n 2 127.0.0.1 >nul

echo ============================================================
echo   DataSens - Lancement de tout en ordre
echo ============================================================
echo.

REM ----- 1. MongoDB (Docker) - Backup Parquet -----
docker --version >nul 2>&1
if %errorlevel% neq 0 goto no_docker_mongo
echo [1/5] MongoDB (Docker) ...
docker stop datasens-mongodb 2>nul
docker rm datasens-mongodb 2>nul
docker run -d --name datasens-mongodb -p 27017:27017 mongo:7
if %errorlevel% equ 0 (echo       OK - localhost:27017) else (echo       Echec - verifier Docker Desktop)
goto mongo_done
:no_docker_mongo
echo [1/5] MongoDB : Docker absent - Backup MongoDB indisponible
:mongo_done
echo.

REM ----- 2. Prometheus (Docker) - optionnel -----
docker --version >nul 2>&1
if %errorlevel% neq 0 goto no_docker_prom
echo [2/5] Prometheus (Docker) ...
docker network create datasens-net 2>nul
docker stop prometheus 2>nul
docker rm prometheus 2>nul
set "DP=%cd:\=/%"
docker run -d --name prometheus --network datasens-net -p 9091:9090 -v "%DP%/monitoring/prometheus.docker.yml:/etc/prometheus/prometheus.yml" -v "%DP%/monitoring/prometheus_rules.yml:/etc/prometheus/prometheus_rules.yml" prom/prometheus
if %errorlevel% equ 0 (echo       OK - http://localhost:9091) else (echo       Echec - verifier Docker Desktop et partage lecteur C:)
goto prom_done
:no_docker_prom
echo [2/5] Prometheus : Docker absent - lancer start_prometheus.bat si besoin
:prom_done
echo.

REM ----- 3. Grafana (Docker) - optionnel -----
docker --version >nul 2>&1
if %errorlevel% neq 0 goto no_docker_graf
echo [3/5] Grafana (Docker) ...
docker stop grafana 2>nul
docker rm grafana 2>nul
set "DP=%cd:\=/%"
docker run -d --name grafana --network datasens-net -p 3001:3001 -v "%DP%/monitoring/grafana/provisioning:/etc/grafana/provisioning" -v "%DP%/monitoring/grafana/dashboards:/var/lib/grafana/dashboards" -e "GF_PATHS_PROVISIONING=/etc/grafana/provisioning" -e "GF_SERVER_HTTP_PORT=3001" grafana/grafana
if %errorlevel% equ 0 (echo       OK - http://localhost:3001) else (echo       Echec - verifier Docker Desktop et partage lecteur C:)
goto graf_done
:no_docker_graf
echo [3/5] Grafana : Docker absent - lancer start_grafana.bat si besoin
:graf_done
echo.

REM ----- 4. API E2 (terminal 1) -----
echo [4/5] Demarrage API E2 (port 8001)...
start "DataSensAPI" cmd /k call "%ROOT%_launch_api.bat"
echo       OK - ne pas fermer ce terminal.
echo.

REM ----- 5. Cockpit (terminal 2) -----
echo [5/5] Attente 5 s puis demarrage Cockpit (port 8501)...
ping -n 6 127.0.0.1 >nul
start "DataSensCockpit" cmd /k call "%ROOT%_launch_cockpit.bat"
echo       OK - ne pas fermer ce terminal.
echo.

echo ============================================================
echo   Termine. Ouvrez dans le navigateur :
echo     - Cockpit :  http://localhost:8501
echo     - API :      http://localhost:8001
echo     - Grafana :  http://localhost:3001
echo     - Prometheus: http://localhost:9091
echo     - MongoDB :   localhost:27017 (Backup Parquet)
echo ============================================================
echo Pour arreter : fermer les 2 fenetres DataSens.
pause
