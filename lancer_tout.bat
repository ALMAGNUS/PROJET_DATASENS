@echo off
set "ROOT=%~dp0"
cd /d "%ROOT%"

REM Liberer ports 8001 et 8501 avant demarrage
echo Liberation des ports 8001 et 8501...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" 2^>nul') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501" 2^>nul') do taskkill /PID %%a /F 2>nul
ping -n 2 127.0.0.1 >nul

echo ============================================================
echo   DataSens - Lancement de tout dans l'ordre
echo ============================================================
echo.

REM ----- 1. Prometheus (Docker) - optionnel -----
docker --version >nul 2>&1
set DOCKER_OK=%errorlevel%
if %DOCKER_OK% equ 0 (
    echo [1/4] Prometheus (Docker) ...
    docker stop prometheus 2>nul
    docker rm prometheus 2>nul
    docker run -d --name prometheus -p 9090:9090 -v "%cd%\monitoring\prometheus.local.yml:/etc/prometheus/prometheus.yml" prom/prometheus 2>nul
    if %errorlevel% equ 0 (echo       OK - http://localhost:9090) else (echo       Echec - demarrez start_prometheus.bat si besoin)
) else (
    echo [1/4] Prometheus : Docker absent - ignore.
)
echo.

REM ----- 2. Grafana (Docker) - optionnel -----
if %DOCKER_OK% equ 0 (
    echo [2/4] Grafana (Docker) ...
    docker stop grafana 2>nul
    docker rm grafana 2>nul
    docker run -d --name grafana -p 3000:3000 -v "%cd%\monitoring\grafana\provisioning:/etc/grafana/provisioning" -v "%cd%\monitoring\grafana\dashboards:/var/lib/grafana/dashboards" -e "GF_PATHS_PROVISIONING=/etc/grafana/provisioning" grafana/grafana 2>nul
    if %errorlevel% equ 0 (echo       OK - http://localhost:3000 dans 10 s, login admin/admin) else (echo       Echec)
) else (
    echo [2/4] Grafana : Docker absent - ignore. Lancez start_grafana.bat si Docker est installe.
)
echo.

REM ----- 3. API E2 (terminal 1) -----
echo [3/4] Demarrage API E2 (port 8001) dans un nouveau terminal...
start "DataSens - API E2" cmd /k "cd /d "%ROOT%" && call .venv\Scripts\activate.bat && echo API E2 - http://localhost:8001 && python run_e2_api.py"
echo       OK - ne pas fermer ce terminal.
echo.

REM ----- 4. Attendre puis Cockpit (terminal 2) -----
echo [4/4] Attente 5 s puis demarrage Cockpit (port 8501)...
ping -n 6 127.0.0.1 >nul
start "DataSens - Cockpit" cmd /k "cd /d "%ROOT%" && call .venv\Scripts\activate.bat && echo Cockpit - http://localhost:8501 && streamlit run src\streamlit\app.py"
echo       OK - ne pas fermer ce terminal.
echo.

echo ============================================================
echo   Termine. Ouvrez dans le navigateur :
echo     - Cockpit :  http://localhost:8501
echo     - API :      http://localhost:8001
echo     - Grafana :  http://localhost:3000  (si Docker a demarre Grafana)
echo     - Prometheus: http://localhost:9090 (si Docker a demarre Prometheus)
echo ============================================================
echo Pour arreter : fermer les 2 fenetres "DataSens - API E2" et "DataSens - Cockpit".
echo Detail des commandes : voir LANCER_TOUT.md
echo.
pause
