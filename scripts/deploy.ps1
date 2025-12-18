# Script de déploiement DataSens E1 (PowerShell)
# Usage: .\scripts\deploy.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  DataSens E1 - Déploiement" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Vérifier Docker
Write-Host "[1/5] Vérification de Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  ✅ $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker n'est pas installé ou non accessible" -ForegroundColor Red
    exit 1
}

# Vérifier Docker Compose
Write-Host "`n[2/5] Vérification de Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "  ✅ $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker Compose n'est pas installé" -ForegroundColor Red
    exit 1
}

# Vérifier les fichiers nécessaires
Write-Host "`n[3/5] Vérification des fichiers..." -ForegroundColor Yellow
$requiredFiles = @("Dockerfile", "docker-compose.yml", "sources_config.json", "requirements.txt")
$allPresent = $true

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file manquant" -ForegroundColor Red
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Write-Host "`n❌ Fichiers manquants. Arrêt du déploiement." -ForegroundColor Red
    exit 1
}

# Build et démarrage
Write-Host "`n[4/5] Build et démarrage des services..." -ForegroundColor Yellow
Write-Host "  ⏳ Cela peut prendre quelques minutes..." -ForegroundColor Gray

try {
    docker-compose up -d --build
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Services démarrés avec succès" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Erreur lors du démarrage" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Erreur: $_" -ForegroundColor Red
    exit 1
}

# Vérifier les services
Write-Host "`n[5/5] Vérification des services..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$services = docker-compose ps --format json | ConvertFrom-Json
foreach ($service in $services) {
    $status = $service.State
    $name = $service.Name
    if ($status -eq "running") {
        Write-Host "  ✅ $name : $status" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $name : $status" -ForegroundColor Yellow
    }
}

# Afficher les URLs
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Services disponibles:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  📊 Pipeline E1:    http://localhost:8000/metrics" -ForegroundColor White
Write-Host "  📈 Prometheus:    http://localhost:9090" -ForegroundColor White
Write-Host "  📉 Grafana:       http://localhost:3000" -ForegroundColor White
Write-Host "     (admin / admin - à changer!)" -ForegroundColor Yellow
Write-Host "`n  📋 Voir les logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "  🛑 Arrêter:        docker-compose down`n" -ForegroundColor Gray
