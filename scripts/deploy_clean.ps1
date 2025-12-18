# Script de déploiement avec nettoyage complet
# Usage: .\scripts\deploy_clean.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  DataSens E1 - Déploiement Propre" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Arrêter les services existants
Write-Host "[1/6] Arrêt des services existants..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null
Write-Host "  ✅ Services arrêtés" -ForegroundColor Green

# Supprimer les images existantes
Write-Host "`n[2/6] Nettoyage des images existantes..." -ForegroundColor Yellow
$images = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String "datasens|projet_datasens"
if ($images) {
    foreach ($img in $images) {
        Write-Host "  🗑️  Suppression: $img" -ForegroundColor Gray
        docker rmi -f $img 2>&1 | Out-Null
    }
}
Write-Host "  ✅ Images nettoyées" -ForegroundColor Green

# Nettoyer les volumes orphelins (optionnel)
Write-Host "`n[3/6] Nettoyage des volumes..." -ForegroundColor Yellow
docker volume prune -f 2>&1 | Out-Null
Write-Host "  ✅ Volumes nettoyés" -ForegroundColor Green

# Vérifier Docker
Write-Host "`n[4/6] Vérification de Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  ✅ $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker n'est pas installé" -ForegroundColor Red
    exit 1
}

# Vérifier les fichiers
Write-Host "`n[5/6] Vérification des fichiers..." -ForegroundColor Yellow
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
    Write-Host "`n❌ Fichiers manquants. Arrêt." -ForegroundColor Red
    exit 1
}

# Build propre (sans cache)
Write-Host "`n[6/6] Build propre (sans cache)..." -ForegroundColor Yellow
Write-Host "  ⏳ Cela peut prendre plusieurs minutes..." -ForegroundColor Gray

try {
    docker-compose build --no-cache
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Build réussi" -ForegroundColor Green
        
        # Démarrer les services
        Write-Host "`n🚀 Démarrage des services..." -ForegroundColor Yellow
        docker-compose up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Services démarrés" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Erreur au démarrage" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  ❌ Erreur lors du build" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Erreur: $_" -ForegroundColor Red
    exit 1
}

# Attendre un peu
Start-Sleep -Seconds 5

# Vérifier les services
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  État des services:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
docker-compose ps

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
