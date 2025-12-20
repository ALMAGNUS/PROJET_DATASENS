@echo off
REM Script Windows pour lancer manage_parquet.py
cd /d "%~dp0\.."
set PYTHONPATH=%CD%\src;%PYTHONPATH%
python scripts\manage_parquet.py
pause
