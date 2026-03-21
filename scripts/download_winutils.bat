@echo off
REM Télécharge winutils.exe pour PySpark sous Windows (voir hadoop\README.md)
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0download_winutils.ps1" %*
if errorlevel 1 pause
