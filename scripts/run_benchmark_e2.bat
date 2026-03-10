@echo off
setlocal

REM Benchmark E2 with isolated environment (Windows)
cd /d "%~dp0\.."

if not exist ".venv_benchmark\Scripts\python.exe" (
  echo [1/4] Creating virtual environment .venv_benchmark
  python -m venv .venv_benchmark
)

echo [2/4] Upgrading pip
".venv_benchmark\Scripts\python.exe" -m pip install --upgrade pip

echo [3/4] Installing minimal benchmark dependencies
".venv_benchmark\Scripts\python.exe" -m pip install torch transformers sentencepiece safetensors huggingface-hub pandas pyarrow

echo [4/4] Running benchmark (balanced per class from goldai parquet)
".venv_benchmark\Scripts\python.exe" scripts\ai_benchmark.py

echo.
echo Benchmark finished. Check:
echo - docs\e2\AI_BENCHMARK.md
echo - docs\e2\AI_BENCHMARK_RESULTS.json
echo - docs\e2\AI_REQUIREMENTS.md

endlocal
