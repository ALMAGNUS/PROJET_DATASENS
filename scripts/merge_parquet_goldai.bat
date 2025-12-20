@echo off
REM Script de fusion incrémentale Parquet GOLD → GoldAI (Windows)
cd /d "%~dp0\.."
python scripts\merge_parquet_goldai.py %*
pause
