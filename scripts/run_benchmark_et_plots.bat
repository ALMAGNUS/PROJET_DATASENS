@echo off
REM Benchmark + plots — à lancer après le fine-tuning
cd /d "%~dp0\.."

echo [1/2] Benchmark...
python scripts\ai_benchmark.py --dataset data/goldai/ia/test.parquet --per-class 120
if errorlevel 1 goto :fail

echo.
echo [2/2] Generation des figures...
python scripts\plot_e2_results.py
if errorlevel 1 goto :fail

echo.
echo OK. Resultats dans:
echo   - docs\e2\AI_BENCHMARK_RESULTS.json
echo   - docs\e2\figures\e2_benchmark_*.png
goto :end

:fail
echo Erreur. Verifiez que data/goldai/ia/test.parquet existe (Copie IA).
exit /b 1

:end
exit /b 0
