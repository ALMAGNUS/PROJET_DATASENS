@echo off
REM Demarre MongoDB (Docker) pour Backup Parquet
cd /d "%~dp0"
echo Demarrage MongoDB sur localhost:27017...
docker-compose up -d mongodb
if %errorlevel% neq 0 (
    echo.
    echo ERREUR: Docker non demarre ou introuvable.
    echo Lancez Docker Desktop puis reessayez.
    pause
    exit /b 1
)
echo.
echo MongoDB demarre. Attente 5 secondes...
timeout /t 5 /nobreak >nul
echo OK - Backup MongoDB disponible (port 27017)
pause
