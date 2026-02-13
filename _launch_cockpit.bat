@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Cockpit - http://localhost:8501
start /b powershell -WindowStyle Hidden -Command "Start-Sleep -Seconds 10; Start-Process 'http://localhost:8501'"
streamlit run src\streamlit\app.py --server.port 8501
pause
