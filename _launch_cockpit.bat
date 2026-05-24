@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo.
echo ========================================
echo  DataSens Frontend — Cockpit Streamlit
echo  http://127.0.0.1:8501
echo  Arreter : fermer cette fenetre OU stop_full.bat
echo ========================================
echo.

start /b powershell -WindowStyle Hidden -Command "Start-Sleep -Seconds 10; Start-Process 'http://127.0.0.1:8501'"
streamlit run src\streamlit\app.py --server.port 8501

echo.
echo Cockpit arrete.
echo Appuyez sur une touche pour fermer cette fenetre Frontend...
pause >nul
