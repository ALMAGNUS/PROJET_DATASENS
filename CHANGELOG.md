# CHANGELOG — DataSens E1

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

---

## [1.0.0] — 2025-12-15

### ✨ Nouvelles Fonctionnalités

#### Phase 1: Architecture Lakehouse Complète
- ✅ Architecture 3-zones (RAW → SILVER → GOLD)
- ✅ 18 tables SQL structurées (datasens.db + datasens_cleaned.db)
- ✅ Partition par date (partition_date) — ready Spark
- ✅ Fingerprinting SHA256 pour déduplication

#### Ingestion Multi-Sources (10 sources)
- ✅ RSS French News (500+ articles)
- ✅ GDELT Events API (1000+ articles)
- ✅ OpenWeather API (200+ articles)
- ✅ INSEE API (300+ articles)
- ✅ Kaggle French Opinions (1500+ articles)
- ✅ Google News RSS (500+ articles)
- ✅ Regional Media RSS (400+ articles)
- ✅ IFOP Barometers (200+ articles)
- ✅ Reddit France Web Scraping (300+ articles)
- ✅ Trustpilot Reviews Web Scraping (100+ articles)

#### Pipeline ELT Complet
- ✅ Extract: 10 sources configurées + fallback mocks
- ✅ Load: SQLite RAW zone (datasens.db)
- ✅ Transform: 10-step cleaning pipeline
- ✅ Quality Scoring: 0-1 par article
- ✅ Deduplication: Automatique avec fingerprint
- ✅ Audit Trail: cleaning_audit table complète

#### CRUD Complet
- ✅ **CREATE**: Insertion multi-sources avec traçabilité
- ✅ **READ**: Requêtes jointes + visualisations Plotly
- ✅ **UPDATE**: Mise à jour contrôlée (partition_date, quality_score)
- ✅ **DELETE**: Suppression avec intégrité référentielle

#### Visualisations & Dashboards
- ✅ Matplotlib dashboard (4 graphiques PNG)
- ✅ Plotly interactive pie chart (HTML)
- ✅ Rapport complet E1 (rapport_complet_e1.html)
  - KPIs (articles totaux, qualité, doublons)
  - Tables détaillées RAW + SILVER
  - Checklist de validation
  - Embeddings graphics

#### Tests & Validation
- ✅ CRUD tests (Create, Read, Update, Delete)
- ✅ Schema validation (18 tables)
- ✅ Quality checks (quality_score ≥ 0.5)
- ✅ Integrity checks (foreign keys)
- ✅ Deduplication verification

#### Logging & Monitoring
- ✅ sync_log table (ingestion tracking)
- ✅ cleaning_audit table (transformation history)
- ✅ data_quality_metrics (per-source stats)
- ✅ Feature engineering log
- ✅ Structured console output

#### Code & Structure
- ✅ E1_UNIFIED_MINIMAL.ipynb (135 lignes)
- ✅ quick_start.py (38 lignes)
- ✅ visualize_dashboard.py (152 lignes)
- ✅ **Total: ~325 lignes** ✅
- ✅ Professional README.md (FR + badges)
- ✅ CONTRIBUTING.md
- ✅ CHANGELOG.md (ce fichier)
- ✅ LICENSE.md (MIT)
- ✅ LOGGING.md (documentation complète)

### 📊 Données

- **RAW Zone**: ~5 000 articles bruts
- **SILVER Zone**: ~3 500-4 500 articles nettoyés (quality ≥ 0.5)
- **Partition**: `partition_date` (format DATE)
- **Fingerprint**: SHA256 (déduplication)
- **Quality Range**: 0-1 (0 = faible qualité, 1 = haute qualité)

### 🛠️ Stack Technologique

| Composant | Technologie |
|-----------|-------------|
| Ingestion | RSS + APIs + Web Scraping |
| Pipeline | Jupyter + Python 3.8+ |
| Bases | SQLite (RAW + SILVER) |
| Format GOLD | Parquet (optionnel Phase 05) |
| Qualité | SHA256 + Quality Scoring |
| Visualisation | Matplotlib + Plotly + HTML5 |
| Tests | CRUD + Schema + Quality |
| Logs | sync_log + cleaning_audit + metrics |

### 🔄 Processus E1

```
1. EXTRACTION (10 sources)
2. LOADING → RAW zone (5K articles)
3. TRANSFORMATION (10 steps)
4. QUALITY FILTERING (score ≥ 0.5)
5. DEDUPLICATION (SHA256)
6. LOADING → SILVER zone (3.5-4.5K articles)
7. VALIDATION (CRUD tests)
8. VISUALIZATION (Matplotlib + Plotly)
9. LOGGING (sync_log + audit trail)
```

---

## [1.2.0] — 2025-12-20

### 🔒 Phase 0: Isolation E1 Complète

#### Architecture Isolée
- ✅ Package `src/e1/` créé : Pipeline E1 complètement isolé
- ✅ Packages `src/e2/` et `src/e3/` créés : Prêts pour développement
- ✅ Package `src/shared/` créé : Interfaces partagées (E1DataReader)
- ✅ Structure modulaire : E1, E2, E3 séparés et protégés

#### Interface E1DataReader
- ✅ Interface abstraite `E1DataReader` (ABC) : Contrat immuable pour E2/E3
- ✅ Implémentation `E1DataReaderImpl` : Lecture seule depuis E1
- ✅ Méthodes : `read_raw_data()`, `read_silver_data()`, `read_gold_data()`, `get_database_stats()`
- ✅ Protection E1 : E2/E3 ne peuvent plus modifier E1 directement

#### Refactoring Pipeline E1
- ✅ `main.py` simplifié : 28 lignes (au lieu de 401)
- ✅ Classe `E1Pipeline` extraite dans `src/e1/pipeline.py`
- ✅ Tous les modules E1 déplacés vers `src/e1/` :
  - `core.py` → `src/e1/core.py`
  - `repository.py` → `src/e1/repository.py`
  - `tagger.py` → `src/e1/tagger.py`
  - `analyzer.py` → `src/e1/analyzer.py`
  - `aggregator.py` → `src/e1/aggregator.py`
  - `exporter.py` → `src/e1/exporter.py`

#### Tests de Non-Régression
- ✅ Suite de tests `tests/test_e1_isolation.py` : 11 tests
  - 10 tests rapides (imports, schéma, interface, structure)
  - 1 test complet marqué `@pytest.mark.slow` (exécution pipeline complète)
- ✅ Configuration `pytest.ini` : Markers personnalisés (slow, integration, unit, e1)
- ✅ Script `tests/run_e1_isolation_tests.py` : Exécution facilitée
- ✅ CI/CD mis à jour : Tests automatisés sur push/PR

#### Logique Sources Fondation
- ✅ Distinction sources fondation figées vs dynamiques
- ✅ Sources figées après première intégration :
  - `kaggle_french_opinions` → SKIP après intégration
  - `gdelt_events` → SKIP après intégration
  - `zzdb_csv` → SKIP après intégration
- ✅ Sources GDELT dynamiques (collecte quotidienne) :
  - `GDELT_Last15_English` → Continue à se collecter
  - `GDELT_Master_List` → Continue à se collecter

#### Amélioration Messages de Log
- ✅ Messages clairs et explicites (sans émojis)
- ✅ Explication détaillée de la déduplication :
  - Articles traités vs nouveaux vs dédupliqués
  - Explication du fingerprint SHA256
- ✅ Résumé après chargement : Statistiques claires
- ✅ Stats finales : Détails complets avec notes explicatives

#### Documentation Complète
- ✅ `docs/E1_ISOLATION_COMPLETE.md` : Récapitulatif Phase 0
- ✅ `docs/QUICK_START_E1_ISOLATED.md` : Guide démarrage rapide
- ✅ `docs/E1_ISOLATION_STRATEGY.md` : Stratégie d'isolation (déjà existant)
- ✅ `docs/PLAN_ACTION_E1_E2_E3.md` : Plan d'action détaillé (déjà existant)
- ✅ `tests/README_E1_ISOLATION.md` : Guide des tests
- ✅ `README.md` mis à jour : Nouvelle structure documentée

#### CI/CD
- ✅ Workflow `.github/workflows/test.yml` mis à jour :
  - Job `test-e1-isolation` : Tests rapides sur push/PR
  - Job `test-e1-complete` : Tests complets sur push vers `main`

### 📊 Statistiques Phase 0

- **Fichiers créés** : 19 fichiers
- **Lignes ajoutées** : 2,661 insertions
- **Lignes supprimées** : 396 suppressions
- **Tests créés** : 11 tests (10 rapides + 1 complet)
- **Documentation** : 5 documents créés/mis à jour

### 🔄 Changements Techniques

#### Fichiers Modifiés
- `main.py` : Simplifié (28 lignes, utilise E1 isolé)
- `README.md` : Structure isolée documentée
- `.github/workflows/test.yml` : Tests automatisés E1

#### Nouveaux Fichiers
- `src/e1/` : 8 fichiers (pipeline isolé)
- `src/e2/__init__.py` : Package E2
- `src/e3/__init__.py` : Package E3
- `src/shared/interfaces.py` : Interface E1DataReader
- `tests/test_e1_isolation.py` : Suite de tests
- `tests/README_E1_ISOLATION.md` : Documentation tests
- `pytest.ini` : Configuration pytest

### 🛡️ Règles d'Isolation

#### ✅ AUTORISÉ
- Utiliser `E1DataReader` depuis E2/E3
- Lire depuis `exports/` ou `data/` (lecture seule)
- Utiliser DB en lecture seule
- Importer uniquement interfaces publiques (`src/shared/`)

#### ❌ INTERDIT
- Modifier `src/e1/` depuis E2/E3
- Importer classes internes E1 depuis E2/E3
- Écrire dans fichiers E1 depuis E2/E3
- Modifier schéma DB E1 depuis E2/E3

### ✅ Status: Phase 0 TERMINÉE

**E1 est maintenant complètement isolé et protégé** pour la construction de E2/E3.

**Prochaines étapes** :
- Phase 1 : Docker & CI/CD
- Phase 2 : FastAPI + RBAC
- Phase 3 : PySpark

---

## [1.1.0] — 2025-12-19

### 🔧 Corrections & Améliorations

#### Fix Encodage UTF-8 (Windows)
- ✅ Ajout fix encodage UTF-8 dans `main.py` pour Windows console
- ✅ Gestion silencieuse des erreurs de déduplication (UNIQUE constraint)
- ✅ Suppression des emojis problématiques dans les messages console

#### Amélioration Pipeline
- ✅ Indicateurs de progression : compteur `[X/Y]` pour les sources
- ✅ Points de progression `.` tous les 100 articles lors du chargement
- ✅ Messages informatifs pour grandes sources (> 1000 articles)
- ✅ Optimisation gestion erreurs (déduplication silencieuse)

#### Flow Kaggle Corrigé
- ✅ Exclusion Kaggle de `_collect_local_files()` (évite duplication)
- ✅ Kaggle vient uniquement de la DB via `aggregate_raw()`
- ✅ Amélioration `KaggleExtractor` : support dossier unique sans partitionnement date
- ✅ Lecture récursive de tous les fichiers CSV/JSON dans `kaggle_french_opinions/`
- ✅ Détection automatique colonnes title/content
- ✅ Suppression limites artificielles (traitement complet des datasets)

#### Exports & Partitionnement
- ✅ Suppression génération `gold_zzdb.csv` (fusionné dans `gold.csv`)
- ✅ Exports standards : `raw.csv`, `silver.csv`, `gold.csv`, `gold.parquet`
- ✅ Partitionnement ZZDB par source dans `data/gold/date=YYYY-MM-DD/source=zzdb_*/`

#### Tables PROFILS & USER_ACTION_LOG
- ✅ Création table `profils` (authentification future)
- ✅ Création table `user_action_log` (audit trail)
- ✅ Isolation complète des tables E1 (pas de FK dans RAW_DATA, SOURCE, etc.)
- ✅ Relation 1-N : PROFILS → USER_ACTION_LOG
- ✅ Référence indirecte via `resource_type` + `resource_id`

#### Tests & Scripts
- ✅ Déplacement scripts de test vers `tests/` (8 fichiers)
- ✅ Scripts de vérification : `check_db_status.py`, `check_exports.py`, `check_kaggle_status.py`
- ✅ Tests pipeline : `test_main_quick.py`, `test_main_minimal.py`, `test_main_run.py`
- ✅ Script vérification Kaggle : `scripts/check_kaggle_files.py`

#### Documentation
- ✅ Création `FLOW_DONNEES.md` : documentation complète du flow de données
- ✅ Création `docs/FLOW_KAGGLE_COMPLET.md` : flow Kaggle détaillé
- ✅ Création `docs/TABLES_PROFILS_ACTION_LOG.md` : documentation tables auth/audit
- ✅ Création `docs/KAGGLE_DOSSIER_UNIQUE.md` : guide structure Kaggle

#### Collection Report
- ✅ Exclusion sources fondation (Kaggle, GDELT events, ZZDB) des rapports quotidiens
- ✅ Focus sur sources dynamiques dans les rapports de collecte
- ✅ Distinction claire sources statiques vs dynamiques

#### Enrichissement
- ✅ Garantie 2 topics par article (fallback "autre" si nécessaire)
- ✅ Amélioration détection sentiment négatif (listes de mots-clés étendues)
- ✅ Enrichissement complet : 100% des articles (topics + sentiment)

### 📊 Records Base de Données

- **Total articles** : 42,466
- **Taille DB** : 71.93 MB
- **Taux enrichissement** : 100% (42,465 articles enrichis)
- **Topics utilisés** : 25 topics différents
- **Sources actives** : 21 sources

#### Top 10 Sources
- Kaggle French Opinions : 38,327 articles
- Google News RSS : 1,274 articles
- ZZDB CSV : 930 articles
- Trustpilot Reviews : 578 articles
- Yahoo Finance : 444 articles
- Reddit France : 338 articles
- RSS French News : 221 articles
- OpenWeather API : 161 articles
- GDELT Events : 70 articles
- DataGouv Datasets : 50 articles

#### Distribution Sentiment
- Neutre : 19,770 articles (46.6%)
- Négatif : 16,774 articles (39.5%)
- Positif : 5,921 articles (13.9%)

### 🔄 Changements Techniques

#### Fichiers Modifiés
- `main.py` : Fix encodage + indicateurs progression
- `src/repository.py` : Déduplication silencieuse + tables PROFILS/USER_ACTION_LOG
- `src/aggregator.py` : Exclusion Kaggle de `_collect_local_files()`
- `src/exporter.py` : Suppression `gold_zzdb.csv`
- `src/core.py` : Amélioration `KaggleExtractor`
- `src/collection_report.py` : Exclusion sources fondation
- `src/tagger.py` : Garantie 2 topics
- `sources_config.json` : Configuration sources mise à jour

#### Nouveaux Fichiers
- `tests/` : 8 scripts de test
- `scripts/check_kaggle_files.py` : Vérification fichiers Kaggle
- `FLOW_DONNEES.md` : Documentation flow
- `docs/FLOW_KAGGLE_COMPLET.md` : Flow Kaggle
- `docs/TABLES_PROFILS_ACTION_LOG.md` : Documentation auth/audit

### 🐛 Corrections de Bugs

- ✅ Erreur UnicodeEncodeError sur Windows (emojis)
- ✅ Duplication Kaggle dans exports (exclusion de `_collect_local_files()`)
- ✅ Affichage erreurs UNIQUE constraint (déduplication silencieuse)
- ✅ Génération fichier `gold_zzdb.csv` indésirable (supprimé)
- ✅ Topics manquants (garantie 2 topics par article)

---

## ✅ Status: E1 COMPLET & PRODUCTION-READY

**E1 inclut tout ce qui est nécessaire pour** :
- ✅ Collecter 10 sources (~5K articles)
- ✅ Nettoyer et qualifier les données
- ✅ Générer dashboards professionnels
- ✅ Tracer toutes les transformations (logging)
- ✅ Valider intégrité (CRUD tests)

**E1 est production-ready. Lancer `python quick_start.py` maintenant.**

---

## À Venir (Extensions Optionnelles)

### Phase 05: Export GOLD (Parquet)
- [ ] Export SILVER → Parquet partitionné
- [ ] Format: `/data/gold/{source}/date={YYYY-MM-DD}/`
- [ ] Manifest JSON (lineage tracking)
- [ ] Spark SQL queries
- [ ] Optimisation partition pruning

### Phase 06: Fine-tune Modèles IA
- [ ] Load SILVER zone
- [ ] Fine-tune FlauBERT (French language understanding)
- [ ] Fine-tune CamemBERT (French BERT)
- [ ] Generate sentiment labels + confidence
- [ ] Model registry (MLflow)

### E2: Spark Data Lake
- [ ] Scale à 100k+ articles
- [ ] Spark SQL queries
- [ ] Real-time streaming ingestion
- [ ] Distributed processing

### E3: Production ML Pipeline
- [ ] MLflow experiment tracking
- [ ] FastAPI endpoints
- [ ] Real-time dashboard updates
- [ ] Model serving + versioning

---

## Notes de Maintien

- **Backup**: Bases SQLite à sauvegarder régulièrement
- **Partition**: Gérer rétention données (30-90 jours conseillé)
- **Logs**: Archiver sync_log après 6 mois
- **Sources**: Vérifier API keys + endpoint availability mensuellement

---

**Version**: 1.0.0  
**Date**: 15 décembre 2025  
**Auteur**: DataSens Project Team  
**License**: MIT
