@echo off
REM Recree le .venv proprement (evite WinError 5 / Acces refuse)
REM Fermer Cursor, terminaux Python, Jupyter avant de lancer.

cd /d "%~dp0\.."

echo [1/4] Suppression de l'ancien .venv...
if exist .venv (
    rmdir /s /q .venv
    if exist .venv (
        echo ERREUR: Impossible de supprimer .venv. Fermez Cursor et tous les terminaux.
        pause
        exit /b 1
    )
)

echo [2/4] Creation du nouveau venv...
python -m venv .venv

echo [3/4] Activation et installation...
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] Termine.
echo.
echo Relancez: .venv\Scripts\activate
pause
