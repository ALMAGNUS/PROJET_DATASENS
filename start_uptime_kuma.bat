@echo off
REM Demarrer Uptime Kuma (Docker) pour le monitoring de disponibilite
REM Ouvrir ensuite : http://localhost:3002 (creer un compte au premier acces)

cd /d "%~dp0"

echo Verifying Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker absent du PATH.
    pause
    exit /b 1
)

echo Starting Uptime Kuma on http://localhost:3002 ...
docker run -d --name uptime-kuma -p 3002:3001 ^
  -v uptime-kuma-data:/app/data ^
  louislam/uptime-kuma:1

if errorlevel 1 (
    echo Failed to start Uptime Kuma.
    pause
    exit /b 1
)

echo.
echo Uptime Kuma demarre. Ouvrir : http://localhost:3002
echo Premier acces : creer un compte admin.
echo.
pause
