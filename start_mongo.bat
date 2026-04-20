@echo off
chcp 65001 >nul
REM Démarre MongoDB (Docker Compose) pour backup Parquet → GridFS et tests cockpit.
cd /d "%~dp0"

echo.
echo ========================================
echo   DataSens — MongoDB (Docker)
echo   Port localhost : 27017
echo   Service compose : mongodb
echo ========================================
echo.

where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR : la commande "docker" est introuvable.
    echo Installez Docker Desktop et ajoutez-le au PATH.
    pause
    exit /b 1
)

echo Vérification du moteur Docker...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERREUR : Docker ne répond pas ^(client OK mais moteur en erreur, ou Docker arrêté^).
    echo   1. Ouvrez Docker Desktop et attendez "Running".
    echo   2. Si erreur 500 : redémarrez Docker Desktop, ou en admin : wsl --shutdown
    echo   3. Puis relancez ce script.
    pause
    exit /b 1
)

echo Démarrage du conteneur...
docker compose up -d mongodb
if %errorlevel% neq 0 (
    echo.
    echo Nouvel essai avec docker-compose ^(ancienne syntaxe^)...
    docker-compose up -d mongodb
)
if %errorlevel% neq 0 (
    echo.
    echo ERREUR : impossible de démarrer mongodb.
    echo Depuis ce dossier, en ligne de commande :
    echo   docker compose up -d mongodb
    pause
    exit /b 1
)

echo.
echo Attente 5 s pour laisser Mongo écouter sur 27017...
timeout /t 5 /nobreak >nul
echo OK — vous pouvez lancer backup_parquet_to_mongo.py ou le cockpit.
echo.
pause
