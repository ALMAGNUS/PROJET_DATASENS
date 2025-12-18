# Script pour corriger le push Git (retirer les gros fichiers)
# Usage: .\scripts\fix_git_push.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Correction Push Git" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Vérifier .gitignore
Write-Host "[1/5] Vérification .gitignore..." -ForegroundColor Yellow
$gitignore = Get-Content .gitignore -Raw
if ($gitignore -notmatch "\.venv") {
    Add-Content .gitignore "`n# Virtual environment`n.venv/`nvenv/`nenv/`nENV/"
    Write-Host "  ✅ .venv/ ajouté à .gitignore" -ForegroundColor Green
} else {
    Write-Host "  ✅ .venv/ déjà dans .gitignore" -ForegroundColor Green
}

if ($gitignore -notmatch "^data/") {
    Add-Content .gitignore "`n# Data files`ndata/"
    Write-Host "  ✅ data/ ajouté à .gitignore" -ForegroundColor Green
} else {
    Write-Host "  ✅ data/ déjà dans .gitignore" -ForegroundColor Green
}

# Retirer .venv du tracking
Write-Host "`n[2/5] Retrait de .venv du tracking..." -ForegroundColor Yellow
git rm -r --cached .venv 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ .venv retiré du tracking" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  .venv déjà retiré ou absent" -ForegroundColor Yellow
}

# Retirer data/ du tracking
Write-Host "`n[3/5] Retrait de data/ du tracking..." -ForegroundColor Yellow
git rm -r --cached data/ 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ data/ retiré du tracking" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  data/ déjà retiré ou absent" -ForegroundColor Yellow
}

# Ajouter .gitignore
Write-Host "`n[4/5] Mise à jour de .gitignore..." -ForegroundColor Yellow
git add .gitignore
Write-Host "  ✅ .gitignore ajouté" -ForegroundColor Green

# Commit
Write-Host "`n[5/5] Création du commit de nettoyage..." -ForegroundColor Yellow
$hasChanges = git diff --cached --quiet
if (-not $hasChanges) {
    git commit -m "chore: retirer .venv et data/ du tracking Git (fichiers trop volumineux)"
    Write-Host "  ✅ Commit créé" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Aucun changement à commiter" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Correction terminée" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n⚠️  IMPORTANT: Les gros fichiers sont dans l'historique Git" -ForegroundColor Yellow
Write-Host "   Pour un nettoyage complet, utilisez git-filter-repo ou BFG Repo-Cleaner" -ForegroundColor Gray
Write-Host "`nPour pousser maintenant:" -ForegroundColor Cyan
Write-Host "   git push origin main`n" -ForegroundColor White
