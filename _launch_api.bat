@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo API E2 - http://localhost:8001
python run_e2_api.py
pause
