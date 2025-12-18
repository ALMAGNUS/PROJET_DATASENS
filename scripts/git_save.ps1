# Script de sauvegarde Git
# Usage: .\scripts\git_save.ps1 [message]

param(
    [string]$Message = "feat: E1 pipeline complet avec déploiement Docker"
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Sauvegarde Git - DataSens E1" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Vérifier qu'on est dans un repo Git
if (-not (Test-Path ".git")) {
    Write-Host "❌ Ce n'est pas un dépôt Git" -ForegroundColor Red
    exit 1
}

# Afficher l'état
Write-Host "[1/4] État actuel..." -ForegroundColor Yellow
git status --short | Select-Object -First 20
$total = (git status --short | Measure-Object).Count
Write-Host "  Total: $total fichiers modifiés/ajoutés" -ForegroundColor Gray

# Ajouter tous les fichiers
Write-Host "`n[2/4] Ajout des fichiers..." -ForegroundColor Yellow
git add -A
Write-Host "  ✅ Fichiers ajoutés" -ForegroundColor Green

# Commit
Write-Host "`n[3/4] Création du commit..." -ForegroundColor Yellow
Write-Host "  Message: $Message" -ForegroundColor Gray
git commit -m $Message

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Commit créé" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Aucun changement à commiter" -ForegroundColor Yellow
}

# Afficher les commits en attente
Write-Host "`n[4/4] Commits en attente de push..." -ForegroundColor Yellow
$commits = git log origin/main..HEAD --oneline 2>$null
if ($commits) {
    Write-Host "  Commits à pousser:" -ForegroundColor Gray
    $commits | ForEach-Object { Write-Host "    $_" -ForegroundColor White }
    Write-Host "`n  Pour pousser:" -ForegroundColor Cyan
    Write-Host "    git push origin main" -ForegroundColor White
} else {
    Write-Host "  ✅ Aucun commit en attente" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Sauvegarde terminée" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
