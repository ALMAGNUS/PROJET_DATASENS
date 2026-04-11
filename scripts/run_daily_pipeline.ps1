#Requires -Version 5.1
<#
.SYNOPSIS
    Chaîne quotidienne DataSens : E1 → GoldAI → branches IA → (Mongo) → veille.
.DESCRIPTION
    À lancer depuis n'importe où : le script se place à la racine du repo.
    Utilise .venv\Scripts\python.exe si présent, sinon `python` du PATH.
.PARAMETER SkipMongo
    Ne lance pas backup_parquet_to_mongo.py (si Docker Mongo indisponible).
.PARAMETER TopicsFilter
    Ex: "finance,politique,meteo" — passé à create_ia_copy.py. Vide = toutes les données (recommandé pour le ML).
.PARAMETER SkipVeille
    Ne lance pas veille_digest.py.
.EXAMPLE
    .\scripts\run_daily_pipeline.ps1
.EXAMPLE
    .\scripts\run_daily_pipeline.ps1 -SkipMongo
#>
param(
    [switch]$SkipMongo,
    [switch]$SkipVeille,
    [string]$TopicsFilter = ""
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "python"
}

function Invoke-DatasensStep {
    param(
        [Parameter(Mandatory)][string]$RelativePath,
        [string[]]$Arguments = @()
    )
    $full = Join-Path $Root $RelativePath
    if (-not (Test-Path $full)) {
        Write-Error "Fichier introuvable: $full"
        exit 1
    }
    Write-Host ""
    Write-Host ">>> $RelativePath $($Arguments -join ' ')" -ForegroundColor Cyan
    & $py $full @Arguments
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ECHEC (code $LASTEXITCODE): $RelativePath" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "DataSens — run pipeline (racine: $Root)" -ForegroundColor Green
Write-Host "Python: $py"

# 1 — Ingestion, SQLite, exports RAW/SILVER/GOLD
Invoke-DatasensStep "main.py"

# 2 — Fusion GOLD → GoldAI (Spark)
Invoke-DatasensStep "scripts\merge_parquet_goldai.py"

# 3 — Branches app / ia
Invoke-DatasensStep "scripts\build_gold_branches.py"

# 4 — Splits train/val/test (+ annotated). Sans filtre topics = meilleure généralisation ML.
$iaArgs = @()
if ($TopicsFilter) {
    $iaArgs = @("--topics", $TopicsFilter)
}
Invoke-DatasensStep "scripts\create_ia_copy.py" -Arguments $iaArgs

# 5 — Archivage long terme GridFS (Mongo doit tourner + MONGO_STORE_PARQUET=true dans .env)
if (-not $SkipMongo) {
    Invoke-DatasensStep "scripts\backup_parquet_to_mongo.py"
} else {
    Write-Host "`n>>> backup_parquet_to_mongo.py — IGNORE (-SkipMongo)" -ForegroundColor Yellow
}

# 6 — Veille C6
if (-not $SkipVeille) {
    Invoke-DatasensStep "scripts\veille_digest.py"
} else {
    Write-Host "`n>>> veille_digest.py — IGNORE (-SkipVeille)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "OK — Pipeline terminee." -ForegroundColor Green
