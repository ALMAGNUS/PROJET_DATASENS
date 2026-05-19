# Publie reports/ sur GitHub (commit + push) si des fichiers ont changé.
# Usage:
#   powershell -File scripts/publish_reports_git.ps1
#   scripts\publish_reports_git.bat
# Planificateur Windows : déclencher après main.py + db_state_report.py (voir RUNBOOK § 3.1).

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".git")) {
    Write-Error "Pas un dépôt Git : $Root"
}

$reportsDir = Join-Path $Root "reports"
if (-not (Test-Path $reportsDir)) {
    Write-Host "[SKIP] Dossier reports/ absent."
    exit 0
}

git add reports/
$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "[OK] Aucun changement dans reports/ — rien à pousser."
    exit 0
}

$stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
$msg = @"
chore(reports): rapports pipeline $stamp

db_state / run_summary générés localement (publication quotidienne).
"@

git commit -m $msg
if ($LASTEXITCODE -ne 0) {
    Write-Error "git commit a échoué."
}

git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Error "git push a échoué (vérifiez la connexion et les droits sur origin/main)."
}

Write-Host "[OK] reports/ publié sur origin/main."
exit 0
