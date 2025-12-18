# Script pour créer un nouveau dépôt Git sans historique (version automatique)
# Usage: .\scripts\git_fresh_start_auto.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Nouveau Dépôt Git (Sans Historique)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "⚠️  Création d'un nouveau dépôt sans historique..." -ForegroundColor Yellow

Write-Host "`n[1/5] Création d'une nouvelle branche orpheline..." -ForegroundColor Yellow
git checkout --orphan clean-main
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Erreur" -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ Branche créée" -ForegroundColor Green

Write-Host "`n[2/5] Ajout de tous les fichiers (sauf .venv et data/)..." -ForegroundColor Yellow
git add -A
Write-Host "  ✅ Fichiers ajoutés" -ForegroundColor Green

Write-Host "`n[3/5] Création du commit initial..." -ForegroundColor Yellow
$commitMsg = @"
feat: E1 pipeline complet - déploiement Docker, scripts SQL, monitoring

État de la base de données:
- Articles: 1856
- Analyses sentiment: 1856 (100% couverture)
- Distribution: neutre:1714 | positif:88 | négatif:54
- Sources actives: 10
- Associations topics: 2009

Nouvelles fonctionnalités:
- Déploiement Docker avec docker-compose
- Scripts SQL directs pour interroger la base
- Monitoring Prometheus avec métriques détaillées
- CI/CD GitHub Actions configuré
- Scripts de déploiement automatisés
- Documentation complète de déploiement
"@
git commit -m $commitMsg
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Erreur lors du commit" -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ Commit créé" -ForegroundColor Green

Write-Host "`n[4/5] Suppression de l'ancienne branche main..." -ForegroundColor Yellow
git branch -D main 2>&1 | Out-Null
Write-Host "  ✅ Ancienne branche supprimée" -ForegroundColor Green

Write-Host "`n[5/5] Renommage de la branche en main..." -ForegroundColor Yellow
git branch -m main
Write-Host "  ✅ Branche renommée" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Nouveau dépôt créé !" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n⚠️  Pour pousser (force push requis):" -ForegroundColor Yellow
Write-Host "   git push -f origin main" -ForegroundColor White
Write-Host "`n⚠️  Cela va écraser l'historique sur GitHub !`n" -ForegroundColor Red
