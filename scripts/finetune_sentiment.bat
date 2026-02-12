@echo off
REM Fine-tuning sentiment (CamemBERT) sur copie IA
REM Usage: finetune_sentiment.bat [--epochs 3]
cd /d "%~dp0\.."
python scripts/finetune_sentiment.py --model camembert --epochs 3 %*
