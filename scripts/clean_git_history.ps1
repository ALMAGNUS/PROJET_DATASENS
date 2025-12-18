# Script pour nettoyer l'historique Git des gros fichiers
# Usage: .\scripts\clean_git_history.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Nettoyage Historique Git" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "⚠️  ATTENTION: Cette opération va réécrire l'historique Git" -ForegroundColor Red
Write-Host "   Tous les commits seront modifiés" -ForegroundColor Yellow
Write-Host "`nOptions:" -ForegroundColor Cyan
Write-Host "  1. Utiliser git-filter-repo (recommandé)" -ForegroundColor White
Write-Host "  2. Utiliser BFG Repo-Cleaner" -ForegroundColor White
Write-Host "  3. Créer une nouvelle branche sans historique" -ForegroundColor White
Write-Host "`nSolution rapide (nouvelle branche):" -ForegroundColor Yellow
Write-Host "  git checkout --orphan clean-main" -ForegroundColor Gray
Write-Host "  git add -A" -ForegroundColor Gray
Write-Host "  git commit -m 'Initial commit - sans historique'" -ForegroundColor Gray
Write-Host "  git branch -D main" -ForegroundColor Gray
Write-Host "  git branch -m main" -ForegroundColor Gray
Write-Host "  git push -f origin main" -ForegroundColor Gray
Write-Host "`n⚠️  Cette méthode supprime TOUT l'historique Git" -ForegroundColor Red
Write-Host "   Utilisez uniquement si vous êtes sûr !`n" -ForegroundColor Yellow
