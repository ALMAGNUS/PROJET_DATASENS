# Script de vérification du déploiement DataSens E1
# Usage: .\scripts\check_deploy.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Vérification du Déploiement" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Vérifier les conteneurs
Write-Host "[1/3] État des conteneurs..." -ForegroundColor Yellow
docker-compose ps

# Vérifier les logs récents
Write-Host "`n[2/3] Derniers logs du pipeline..." -ForegroundColor Yellow
docker-compose logs --tail=10 datasens-e1

# Vérifier les métriques
Write-Host "`n[3/3] Vérification des métriques..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✅ Métriques accessibles (http://localhost:8000/metrics)" -ForegroundColor Green
    Write-Host "     Taille de la réponse: $($response.Content.Length) caractères" -ForegroundColor Gray
} catch {
    Write-Host "  ⚠️  Métriques non accessibles (le service démarre peut-être encore...)" -ForegroundColor Yellow
}

# Résumé
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Services disponibles:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  📊 Pipeline E1:    http://localhost:8000/metrics" -ForegroundColor White
Write-Host "  📈 Prometheus:    http://localhost:9090" -ForegroundColor White
Write-Host "  📉 Grafana:       http://localhost:3000" -ForegroundColor White
Write-Host "`n  📋 Commandes utiles:" -ForegroundColor Gray
Write-Host "     docker-compose logs -f datasens-e1" -ForegroundColor Gray
Write-Host "     docker-compose ps" -ForegroundColor Gray
Write-Host "     docker-compose restart datasens-e1`n" -ForegroundColor Gray
