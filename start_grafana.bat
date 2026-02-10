@echo off
REM Demarrer Grafana (Docker) pour le cockpit DataSens
REM Ouvrir ensuite : http://localhost:3000 (login: admin / admin)

cd /d "%~dp0"

echo Verifying Docker...
docker --version 2>nul || (
    echo Docker n'est pas installe ou pas dans le PATH.
    echo Option sans Docker : telechargez Grafana sur https://grafana.com/grafana/download
    echo puis lancez grafana-server.exe (port 3000).
    pause
    exit /b 1
)

echo Stopping existing container if any...
docker stop grafana 2>nul
docker rm grafana 2>nul

echo Starting Grafana on http://localhost:3000 ...
docker run -d --name grafana -p 3000:3000 ^
  -v "%cd%\monitoring\grafana\provisioning:/etc/grafana/provisioning" ^
  -v "%cd%\monitoring\grafana\dashboards:/var/lib/grafana/dashboards" ^
  -e "GF_PATHS_PROVISIONING=/etc/grafana/provisioning" ^
  -e "GF_SERVER_HTTP_PORT=3000" ^
  grafana/grafana

if errorlevel 1 (
    echo Failed to start Grafana.
    pause
    exit /b 1
)

echo.
echo Grafana demarre. Attendre 5-10 secondes puis ouvrir : http://localhost:3000
echo Premier login : admin / admin (Grafana demandera de changer le mot de passe)
echo.
echo Pour importer le dashboard : Menu ^> Dashboards ^> Import ^> Upload datasens-full.json
echo Fichier : monitoring\grafana\dashboards\datasens-full.json
echo.
pause
