# Guide de Contribution — DataSens

Merci d'envisager de contribuer à **DataSens** ! Ce document guide comment participer au projet.

---

## Code de Conduite

Nous nous engageons à fournir un environnement accueillant et inclusif. Tous les contributeurs doivent respecter le [Code de Conduite](CODE_OF_CONDUCT.md).

---

## Comment Contribuer

### 📋 Signaler un Bug

1. **Avant de rapporter**, vérifiez que le bug n'existe pas déjà dans [Issues](https://github.com/ALMAGNUS/PROJET_DATASENS/issues)
2. **Incluez**: Description, étapes de reproduction, résultat attendu, résultat obtenu
3. **Annexez**: Logs (sync_log, cleaning_audit), versions Python/OS
4. **Exemple**:
   ```
   **Bug**: SILVER zone contient 0 articles
   **Étapes**:
   1. Lancé python main.py --mode daily
   2. Vérification data/datasens.db (table silver_data)
   **Résultat attendu**: ~3500 articles nettoyés
   **Résultat obtenu**: 0 articles
   **Logs**: [Voir reports/db_state_*.md et logs/]
   **Env**: Python 3.13, Windows 11
   ```

### 💡 Proposer une Fonctionnalité

1. **Ouvrir Discussion** sur [Discussions](https://github.com/ALMAGNUS/PROJET_DATASENS/discussions)
2. **Décrire**: Cas d'usage, bénéfice, implémentation proposée
3. **Exemple**:
   ```
   **Titre**: Support Streaming Kafka pour E1
   **Cas d'usage**: Ingestion temps réel ~1M articles/jour
   **Approche**: Ajouter un extractor Kafka dans src/e1/core.py
   **Impact**: module dédié, respect SOLID (isolé du reste du pipeline)
   ```

### 🔧 Soumettre une Pull Request

#### 1. Fork & Clone
```powershell
git clone https://github.com/[TON_COMPTE]/PROJET_DATASENS.git
cd PROJET_DATASENS
git checkout -b feature/ma-feature
```

#### 2. Faire les Changements

**Standards de code**:
- ✅ **SOLID/DRY**: architecture modulaire (`src/e1/`, `src/e2/`, `src/e3/`, `src/spark/`, `src/ml/`)
- ✅ **PEP 8 / Ruff**: format vérifié par `run_ruff.bat` (ou `ruff check .`)
- ✅ **Documentation**: docstrings pour classes/fonctions publiques
- ✅ **Tests**: tests unitaires (`pytest tests/`) pour nouvelles features
- ✅ **Logs**: traçabilité via `loguru` (voir `src/logging_config.py`)

**Exemples de contributions acceptées**:
- ✅ Nouvelles sources de données (RSS, API, scraping) — dans `src/e1/core.py` + `sources_config.json`
- ✅ Nouveaux endpoints API — dans `src/e2/api/routes/`
- ✅ Nouveaux traitements Spark — dans `src/spark/processors/`
- ✅ Améliorations du cockpit Streamlit — dans `src/streamlit/`
- ✅ Documentation (README, annexes E1–E5) — toujours bienvenue

**Exemples refusés** (hors scope projet DataSens) :
- ❌ Dépendances lourdes non justifiées (TensorFlow/Keras — HuggingFace suffit)
- ❌ Code hors du périmètre des 5 compétences E1–E5 sans discussion préalable

#### 3. Tester Localement
```powershell
# Pipeline E1 complet (scraping + enrichissement + export)
python main.py --mode daily

# Vérifier la cohérence (doit être OK)
python scripts/db_state_report.py

# Lancer les tests unitaires
.venv\Scripts\python.exe -m pytest tests/ -v

# Vérifier le lint (Ruff)
.\run_ruff.bat
```

#### 4. Commit avec Message Clair
```powershell
git add .
git commit -m "feat: ajoute source reddit_france + 10 tests"
git push origin feature/ma-feature
```

**Format commit** (Conventional Commits):
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation (README, CHANGELOG)
- `refactor:` Amélioration code (pas de feature)
- `test:` Ajout/amélioration tests
- `perf:` Performance optimization
- `chore:` Dépendances, setup

#### 5. Ouvrir Pull Request

Sur [Pull Requests](https://github.com/ALMAGNUS/PROJET_DATASENS/pulls):

```markdown
## Description
Brève description de la PR

## Type de Changement
- [ ] Bug fix
- [ ] Nouvelle source
- [ ] Dashboard improvement
- [ ] Documentation
- [ ] Autre: ____

## Vérification
- [ ] Code suit PEP 8
- [ ] Tests CRUD passent
- [ ] CHANGELOG.md mis à jour
- [ ] README.md mis à jour si applicable
- [ ] Logs (sync_log) documentés si applicable

## Exemple d'Exécution
```
python main.py --mode daily
RAW: 5240 articles
SILVER: 4150 articles (quality ≥ 0.5)
GOLD: 4150 articles enrichis (sentiment + topics)
Coherence: OK
```
```

---

## Structure du Projet

```
PROJET_DATASENS/
├── main.py                         # Point d'entrée du pipeline E1
├── sources_config.json             # Configuration des sources
├── requirements.txt                # Dépendances Python
├── pyproject.toml                  # Config Ruff
├── docker-compose.yml              # Services conteneurisés
├── Dockerfile                      # Image E1
├── src/
│   ├── e1/                         # C1-C5 : extraction, aggregation, export
│   ├── e2/api/                     # C6-C10 : API REST FastAPI (auth + RAW/SILVER/GOLD)
│   ├── e3/mistral/                 # C11-C15 : orchestration IA
│   ├── spark/                      # Traitements Spark (GOLD + enrichissements)
│   ├── ml/inference/               # Modèles HuggingFace (sentiment, topics)
│   ├── streamlit/                  # Cockpit dashboard
│   ├── storage/                    # MongoDB GridFS (backup modèles)
│   ├── monitoring/                 # Intégration Prometheus
│   ├── observability/              # Lineage service
│   ├── data_contracts/             # Schemas + guards
│   └── config.py, dashboard.py, metrics.py, logging_config.py
├── data/                           # Données (ignorées par Git)
│   ├── datasens.db                 # SQLite principal (RAW + SILVER)
│   ├── raw/silver/gold/            # Zones Parquet
│   └── lake/                       # Data lake consolidé
├── tests/                          # Tests unitaires (pytest)
├── notebooks/                      # Notebooks pédagogiques E1 + référence
├── scripts/                        # Scripts utilitaires (manage_parquet, db_state_report, …)
├── docs/                           # Documentation complète (E1 → E5 + annexes + _archive)
├── reports/                        # Rapports quotidiens db_state_*.{md,json}
├── monitoring/                     # Prometheus + Grafana (provisioning)
├── models/                         # Modèles fine-tunés (ignorés par Git)
├── README.md                       # Documentation principale
├── CHANGELOG.md                    # Historique versions
├── CONTRIBUTING.md                 # Ce fichier
├── LICENSE.md                      # MIT License
├── LOGGING.md                      # Documentation logs
└── BACKLOG.md                      # Dette technique identifiée
```

---

## Documentation Logs

### SYNC_LOG Table

Documente chaque ingestion de données:

```sql
CREATE TABLE sync_log (
    sync_id INTEGER PRIMARY KEY,
    source_name TEXT NOT NULL,
    sync_start TIMESTAMP,
    sync_end TIMESTAMP,
    articles_fetched INTEGER,
    articles_inserted INTEGER,
    errors_count INTEGER,
    status TEXT,  -- 'SUCCESS', 'PARTIAL', 'FAILED'
    error_message TEXT,
    metadata JSON
);
```

**Exemple d'Entrée**:
```json
{
    "sync_id": 1,
    "source_name": "rss_french_news",
    "sync_start": "2025-12-15 10:00:00",
    "sync_end": "2025-12-15 10:05:00",
    "articles_fetched": 500,
    "articles_inserted": 485,
    "errors_count": 15,
    "status": "PARTIAL",
    "error_message": "15 articles with invalid URLs",
    "metadata": {"retry_count": 2, "timeout": false}
}
```

### CLEANING_AUDIT Table

Trace toutes les transformations:

```sql
CREATE TABLE cleaning_audit (
    audit_id INTEGER PRIMARY KEY,
    raw_article_id INTEGER,
    step_number INTEGER,
    step_name TEXT,
    action TEXT,
    value_before TEXT,
    value_after TEXT,
    timestamp TIMESTAMP
);
```

**Étapes Trackées**:
1. LOAD: Charge depuis RAW
2. NORMALIZE: Trim titre/contenu
3. PARSE_DATES: Parse published_at
4. QUALITY_SCORE: Calcule score
5. FINGERPRINT: Détecte doublons
6. FILTER: Applique threshold ≥ 0.5
7. DEDUP: Marque duplicatas
8. INSERT: Insère en SILVER
9. AUDIT_LOG: Log transformation
10. PARTITION: Crée partition_date

### DATA_QUALITY_METRICS Table

Résume qualité par source:

```sql
CREATE TABLE data_quality_metrics (
    metric_id INTEGER PRIMARY KEY,
    source_name TEXT NOT NULL,
    metric_date DATE,
    total_articles INTEGER,
    avg_quality_score REAL,
    null_count INTEGER,
    duplicate_count INTEGER,
    invalid_urls INTEGER,
    incomplete_records INTEGER,
    processing_time_seconds REAL
);
```

---

## Directives de Code

### Python Style

```python
# ✅ BON: Clair, minimaliste
def ingest(source_name):
    """Fetch articles from source"""
    try:
        data = fetch_source(source_name)
        return data or get_fallback_data(source_name)
    except Exception as e:
        log_error(source_name, str(e))
        return []

# ❌ MAUVAIS: Verbeux, sur-engénirisé
def ingest(source_name, max_retries=3, timeout=10, 
           enable_cache=True, cache_duration=3600):
    # ... 50 lignes
```

### Tests

```python
# ✅ CRUD Tests requis
assert len(raw_data) > 0  # CREATE
assert read_count(raw_db) > 0  # READ
assert quality_score_updated > 0  # UPDATE
assert duplicates_removed > 0  # DELETE
```

### Logs

```python
# ✅ Log tout ce qui importe
sync_log.insert({
    'source': 'rss_french_news',
    'articles_fetched': 500,
    'articles_inserted': 485,
    'errors': 15,
    'status': 'PARTIAL'
})

# ❌ Pas assez de logs
print("Sync done")
```

---

## Processus de Review

1. **Automated Checks**:
   - ✅ Format du code (Ruff / PEP 8)
   - ✅ Tests unitaires `pytest tests/` passent
   - ✅ Rapport `db_state_report.py` → `coherence: OK`

2. **Code Review** (par maintainers):
   - Respect des principes SOLID/DRY ?
   - Documentation (docstrings + mise à jour docs/ si nécessaire) ?
   - Logs appropriés via `loguru` ?
   - Impacts sur autres composants (E1-E5) ?

3. **Merge**:
   - Approuvé: Merge et release versioning
   - Refusé: Feedback + suggestions d'amélioration

---

## Questions ?

- 🐛 **Bug?** → [Issues](https://github.com/ALMAGNUS/PROJET_DATASENS/issues)
- 💬 **Discussion?** → [Discussions](https://github.com/ALMAGNUS/PROJET_DATASENS/discussions)
- 📧 **Contact?** → [À ajouter]

---

**Merci de contribuer à DataSens!** 🙌

**Dernière mise à jour**: 18 avril 2026  
**Mainteneurs**: DataSens Team
