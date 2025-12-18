# Script de vérification Docker (PowerShell pour Windows)

Write-Host "=========================================="
Write-Host "VERIFICATION DOCKER - DataSens E1"
Write-Host "=========================================="
Write-Host ""

# Vérifier Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker n'est pas installe"
    exit 1
}
Write-Host "[OK] Docker installe"

# Vérifier Docker Compose
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker Compose n'est pas installe"
    exit 1
}
Write-Host "[OK] Docker Compose installe"

# Test syntaxe docker-compose.yml
Write-Host ""
Write-Host "[TEST] Verification syntaxe docker-compose.yml..."
$result = docker-compose config 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] docker-compose.yml syntaxe valide"
} else {
    Write-Host "[ERROR] docker-compose.yml a des erreurs"
    Write-Host $result
    exit 1
}

Write-Host ""
Write-Host "=========================================="
Write-Host "[OK] VERIFICATION DOCKER TERMINEE"
Write-Host "=========================================="
Write-Host ""
Write-Host "Pour build: docker-compose build"
Write-Host "Pour lancer: docker-compose up -d"

