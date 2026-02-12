# Script pour tester l'endpoint ML sentiment GoldAI
# Usage: .\scripts\test_ml_sentiment.ps1

$baseUrl = "http://localhost:8001"

# 1. Login pour obtenir le token
Write-Host "1. Login..."
$loginBody = @{ email = "reader@datasens.test"; password = "reader123" } | ConvertTo-Json
try {
    $loginResp = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
    $token = $loginResp.access_token
    Write-Host "   OK: Token obtenu" -ForegroundColor Green
} catch {
    Write-Host "   ERREUR: Impossible de se connecter. Astuces:" -ForegroundColor Red
    Write-Host "   - L'API tourne? (uvicorn src.e2.api.main:app --host 0.0.0.0 --port 8001)"
    Write-Host "   - Utilisateurs créés? (python scripts/create_test_user.py)"
    exit 1
}

# 2. Appel ML sentiment GoldAI
Write-Host "`n2. Inférence ML sentiment GoldAI (limit=10)..."
$headers = @{ "Authorization" = "Bearer $token" }
try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/v1/ai/ml/sentiment-goldai?limit=10" -Headers $headers
    Write-Host "   OK: $($result.count) articles analysés" -ForegroundColor Green
    $result.results | Select-Object -First 3 | Format-Table id, title, sentiment_ml, score -AutoSize
} catch {
    Write-Host "   ERREUR: $_" -ForegroundColor Red
    exit 1
}
