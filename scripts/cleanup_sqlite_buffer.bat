@echo off
REM Script Windows pour nettoyer le buffer SQLite
cd /d "%~dp0\.."
python scripts\cleanup_sqlite_buffer.py
pause
