@echo off
setlocal

REM E2 full loop: IA copy -> fine-tune -> benchmark
REM ATTENTION: Ce script lance TOUJOURS un entraînement (quick par défaut, full avec --full).
REM Pour benchmark + figures SANS entraînement: run_benchmark_et_plots.bat
cd /d "%~dp0\.."

set "MODE=quick"
if /I "%~1"=="--full" set "MODE=full"
if /I "%~1"=="full" set "MODE=full"

set "FT_EPOCHS=1"
set "FT_BATCH=8"
set "FT_MAXLEN=192"
set "FT_MAX_TRAIN=3000"
set "FT_MAX_VAL=800"
set "BENCH_PER_CLASS=80"
set "BENCH_MAX_SAMPLES=240"

if /I "%MODE%"=="full" (
  set "FT_EPOCHS=3"
  set "FT_BATCH=16"
  set "FT_MAXLEN=256"
  set "FT_MAX_TRAIN=0"
  set "FT_MAX_VAL=0"
  set "BENCH_PER_CLASS=120"
  set "BENCH_MAX_SAMPLES=0"
)

echo Running mode: %MODE%

if not exist ".venv_benchmark\Scripts\python.exe" (
  echo [1/6] Creating benchmark venv
  python -m venv .venv_benchmark
  if errorlevel 1 goto :fail
)

echo [2/6] Upgrading pip
".venv_benchmark\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :fail

echo [3/6] Installing minimal ML dependencies
".venv_benchmark\Scripts\python.exe" -m pip install torch transformers sentencepiece safetensors huggingface-hub datasets pandas pyarrow "accelerate>=0.26.0" scikit-learn
if errorlevel 1 goto :fail

echo [4/6] Building IA copy (train/val/test)
".venv_benchmark\Scripts\python.exe" scripts\create_ia_copy.py --train 0.8 --val 0.1 --test 0.1
if errorlevel 1 goto :fail

echo [5/6] Fine-tuning local model (sentiment_fr)
".venv_benchmark\Scripts\python.exe" scripts\finetune_sentiment.py --model sentiment_fr --epochs %FT_EPOCHS% --batch-size %FT_BATCH% --max-length %FT_MAXLEN% --max-train-samples %FT_MAX_TRAIN% --max-val-samples %FT_MAX_VAL%
if errorlevel 1 goto :fail

echo [6/6] Running benchmark (includes finetuned model if found)
".venv_benchmark\Scripts\python.exe" scripts\ai_benchmark.py --per-class %BENCH_PER_CLASS% --max-samples %BENCH_MAX_SAMPLES%
if errorlevel 1 goto :fail

echo [7/7] Generation des figures E2
".venv_benchmark\Scripts\python.exe" scripts\plot_e2_results.py
if errorlevel 1 goto :fail

echo.
echo Full E2 training loop done. Check:
echo - docs\e2\AI_BENCHMARK.md
echo - docs\e2\AI_BENCHMARK_RESULTS.json
echo - docs\e2\TRAINING_RESULTS.json
echo - docs\e2\figures\e2_training_%MODE%_*.png
echo - models\sentiment_fr-sentiment-finetuned
echo - Mode used: %MODE%

endlocal
exit /b 0

:fail
echo.
echo [ERROR] E2 training loop stopped due to a failure. See logs above.
endlocal
exit /b 1
