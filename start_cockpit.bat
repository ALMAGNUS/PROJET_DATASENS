@echo off
cd /d "%~dp0"
title DataSens Cockpit
echo Cockpit seul. Backend API : lancer start_full.bat ou dans un 2e terminal : python run_e2_api.py
echo.
call .venv\Scripts\activate.bat 2>nul
streamlit run src\streamlit\app.py
pause
