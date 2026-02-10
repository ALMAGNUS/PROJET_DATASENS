@echo off
set "ROOT=%~dp0"
cd /d "%ROOT%"
echo Demarrage DataSens : Backend (API) + Frontend (Cockpit)
echo.
echo Terminal 1 = Backend  (port 8001) - ne pas fermer
echo Terminal 2 = Frontend (port 8501) - ne pas fermer
echo.
start "DataSens Backend" cmd /k "cd /d ""%ROOT:~0,-1%"" && call .venv\Scripts\activate.bat && echo Backend API - port 8001 && python run_e2_api.py"
timeout /t 3 /nobreak >nul
start "DataSens Frontend" cmd /k "cd /d ""%ROOT:~0,-1%"" && call .venv\Scripts\activate.bat && echo Cockpit Streamlit - port 8501 && streamlit run src\streamlit\app.py"
echo.
echo Deux fenetres ouvertes. Pour arreter : fermer les 2 terminaux Backend et Frontend.
pause
