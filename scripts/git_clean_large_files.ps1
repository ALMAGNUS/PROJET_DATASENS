# Script pour nettoyer les gros fichiers du dépôt Git
# Usage: .\scripts\git_clean_large_files.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Nettoyage des Gros Fichiers Git" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Vérifier qu'on est dans un repo Git
if (-not (Test-Path ".git")) {
    Write-Host "❌ Ce n'est pas un dépôt Git" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Retrait de .venv du tracking Git..." -ForegroundColor Yellow
git rm -r --cached .venv 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ .venv retiré" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  .venv déjà ignoré ou absent" -ForegroundColor Yellow
}

Write-Host "`n[2/4] Retrait de data/ du tracking Git..." -ForegroundColor Yellow
git rm -r --cached data/ 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ data/ retiré" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  data/ déjà ignoré ou absent" -ForegroundColor Yellow
}

Write-Host "`n[3/4] Retrait de exports/ du tracking Git..." -ForegroundColor Yellow
git rm -r --cached exports/ 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ exports/ retiré" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  exports/ déjà ignoré ou absent" -ForegroundColor Yellow
}

Write-Host "`n[4/4] Vérification du .gitignore..." -ForegroundColor Yellow
$gitignoreContent = Get-Content .gitignore -Raw
if ($gitignoreContent -match "\.venv" -and $gitignoreContent -match "data/" -and $gitignoreContent -match "exports/") {
    Write-Host "  ✅ .gitignore correctement configuré" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Vérifiez que .gitignore contient .venv/, data/, exports/" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Nettoyage terminé" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nProchaines étapes:" -ForegroundColor Yellow
Write-Host "  1. git add .gitignore" -ForegroundColor White
Write-Host "  2. git commit -m 'chore: retirer gros fichiers du tracking'" -ForegroundColor White
Write-Host "  3. git push origin main`n" -ForegroundColor White
