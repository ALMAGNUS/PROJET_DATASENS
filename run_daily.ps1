<#
.SYNOPSIS
    Run quotidien DataSens — collecte, fusion, branches IA, veille, inférence ML.

.DESCRIPTION
    Séquence complète :
      1. main.py               — collecte E1 (RAW → SILVER → GOLD → SQLite)
      2. merge_parquet_goldai  — fusion GOLD du jour dans GoldAI (long terme)
      3. build_gold_branches   — génère gold_app_input + gold_ia_labelled
      4. create_ia_copy        — split train/val/test temporel depuis gold_ia_labelled
      5. veille_digest         — export veille markdown/json
      6. run_inference_pipeline— inférence ML sur le GoldAI mis à jour (--limit 0 = tout)

.PARAMETER SkipInference
    Passer l'étape inférence ML (utile pour un run rapide sans GPU/CPU dispo).

.PARAMETER InferenceLimit
    Nombre max d'articles à inférer. 0 = tout (défaut). Ex: -InferenceLimit 1000

.EXAMPLE
    .\run_daily.ps1
    .\run_daily.ps1 -SkipInference
    .\run_daily.ps1 -InferenceLimit 2000
#>

param(
    [switch]$SkipInference,
    [int]$InferenceLimit = 0
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Step($label, $cmd) {
    Write-Host "`n=== $label ===" -ForegroundColor Cyan
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ECHEC: $label (exit $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "OK: $label" -ForegroundColor Green
}

Step "1. Collecte E1" ".\.venv\Scripts\python.exe main.py"
Step "2. Fusion GoldAI" ".\.venv\Scripts\python.exe scripts\merge_parquet_goldai.py"
Step "3. Branches GOLD IA" ".\.venv\Scripts\python.exe scripts\build_gold_branches.py"
Step "4. Copie IA (split temporel)" ".\.venv\Scripts\python.exe scripts\create_ia_copy.py"
Step "5. Veille digest" ".\.venv\Scripts\python.exe scripts\veille_digest.py"

if (-not $SkipInference) {
    $inferCmd = ".\.venv\Scripts\python.exe scripts\run_inference_pipeline.py --limit $InferenceLimit --checkpoint-every 500"
    Step "6. Inference ML" $inferCmd
} else {
    Write-Host "`n=== 6. Inference ML (ignorée: -SkipInference) ===" -ForegroundColor Yellow
}

Write-Host "`n Run quotidien termine." -ForegroundColor Green
