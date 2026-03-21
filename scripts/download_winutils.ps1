# Télécharge winutils.exe (Hadoop 3.3.x) pour PySpark sous Windows.
# Usage : depuis la racine du projet :
#   powershell -ExecutionPolicy Bypass -File scripts/download_winutils.ps1
#   .\scripts\download_winutils.ps1 -Force   # réécrit le fichier

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {}

$projectRoot = Split-Path -Parent $PSScriptRoot
$binDir = Join-Path $projectRoot "hadoop\bin"
$dest = Join-Path $binDir "winutils.exe"

# Aligné Spark 3.5.x / PySpark 3.5.x (Hadoop 3.3.5 côté binaires Windows)
$winutilsUrl = "https://github.com/cdarlint/winutils/raw/refs/heads/master/hadoop-3.3.5/bin/winutils.exe"

New-Item -ItemType Directory -Path $binDir -Force | Out-Null

if ((Test-Path $dest) -and -not $Force) {
    $len = (Get-Item $dest).Length
    if ($len -ge 4096) {
        Write-Host "OK: winutils.exe deja present ($len octets) -> $dest"
        Write-Host "    Pour re-telecharger : -Force"
        exit 0
    }
}

Write-Host "Telechargement winutils (Hadoop 3.3.5)..."
Write-Host "  -> $dest"
Invoke-WebRequest -Uri $winutilsUrl -OutFile $dest -UseBasicParsing

if (-not (Test-Path $dest) -or ((Get-Item $dest).Length -lt 4096)) {
    Remove-Item $dest -Force -ErrorAction SilentlyContinue
    throw "Telechargement invalide (fichier trop petit ou absent). Verifiez le reseau ou installez manuellement (voir hadoop/README.md)."
}

Write-Host "OK: winutils.exe installe ($((Get-Item $dest).Length) octets)."
