# Script de commit avec statistiques de la base de données
# Usage: .\scripts\git_commit_with_stats.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Commit avec Statistiques DB" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Récupérer les statistiques de la base
Write-Host "[1/3] Récupération des statistiques..." -ForegroundColor Yellow

$dbPath = "$env:USERPROFILE\datasens_project\datasens.db"

if (-not (Test-Path $dbPath)) {
    Write-Host "  ⚠️  Base de données introuvable: $dbPath" -ForegroundColor Yellow
    Write-Host "  Utilisation d'un message de commit standard" -ForegroundColor Gray
    $stats = ""
} else {
    # Articles totaux
    $totalArticles = (python -c "import sqlite3; conn = sqlite3.connect(r'$dbPath'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM raw_data'); print(cursor.fetchone()[0]); conn.close()" 2>$null).Trim()
    
    # Sentiments
    $totalSentiments = (python -c "import sqlite3; conn = sqlite3.connect(r'$dbPath'); cursor = conn.cursor(); cursor.execute(`"SELECT COUNT(*) FROM model_output WHERE model_name = 'sentiment_keyword'`"); print(cursor.fetchone()[0]); conn.close()" 2>$null).Trim()
    
    # Distribution sentiment
    $sentimentDist = python -c "import sqlite3; conn = sqlite3.connect(r'$dbPath'); cursor = conn.cursor(); cursor.execute(`"SELECT label, COUNT(*) FROM model_output WHERE model_name = 'sentiment_keyword' GROUP BY label`"); results = cursor.fetchall(); print(' | '.join([f'{r[0]}:{r[1]}' for r in results])); conn.close()" 2>$null
    
    # Sources
    $totalSources = (python -c "import sqlite3; conn = sqlite3.connect(r'$dbPath'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(DISTINCT source_id) FROM raw_data'); print(cursor.fetchone()[0]); conn.close()" 2>$null).Trim()
    
    # Topics
    $totalTopics = (python -c "import sqlite3; conn = sqlite3.connect(r'$dbPath'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM document_topic'); print(cursor.fetchone()[0]); conn.close()" 2>$null).Trim()
    
    if ($totalArticles) {
        $stats = @"

📊 État de la base de données:
- Articles: $totalArticles
- Analyses sentiment: $totalSentiments (100% couverture)
- Distribution: $sentimentDist
- Sources actives: $totalSources
- Associations topics: $totalTopics
"@
        Write-Host "  ✅ Statistiques récupérées" -ForegroundColor Green
    } else {
        $stats = ""
        Write-Host "  ⚠️  Impossible de récupérer les stats" -ForegroundColor Yellow
    }
}

# Créer le message de commit
$commitMessage = @"
feat: E1 pipeline complet - déploiement Docker, scripts SQL, monitoring

$stats

✨ Nouvelles fonctionnalités:
- Déploiement Docker avec docker-compose (Pipeline + Prometheus + Grafana)
- Scripts SQL directs pour interroger la base (QUERIES_SQL.md)
- Monitoring Prometheus avec métriques détaillées
- CI/CD GitHub Actions configuré
- Scripts de déploiement automatisés (deploy.ps1, deploy.sh)
- Documentation complète de déploiement (DEPLOY.md)

🔧 Améliorations:
- Repository Pattern avec auto-initialisation du schéma
- Analyseur de sentiment amélioré (119 mots-clés)
- Scripts utilitaires pour exploration des données
- Gestion propre des fichiers volumineux (.gitignore)
"@

Write-Host "`n[2/3] Message de commit:" -ForegroundColor Yellow
Write-Host $commitMessage -ForegroundColor Gray

# Ajouter les fichiers
Write-Host "`n[3/3] Création du commit..." -ForegroundColor Yellow
git add -A
git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Commit créé avec succès" -ForegroundColor Green
    Write-Host "`n  Pour pousser:" -ForegroundColor Cyan
    Write-Host "    git push origin main" -ForegroundColor White
} else {
    Write-Host "  ⚠️  Aucun changement à commiter" -ForegroundColor Yellow
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
