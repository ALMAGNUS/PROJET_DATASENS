# Fichiers DataSens — Utiles vs Inutiles

## 🔴 RACINE — Entrées & config

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `main.py` | Point d'entrée pipeline E1 — lance E1Pipeline (collecte, enrichissement, export) | ✅ Oui |
| `run_e2_api.py` | Lance l'API FastAPI (uvicorn) sur port 8001 | ✅ Oui |
| `sources_config.json` | Config des sources (RSS, API, scraping) — utilisé par E1 | ✅ Oui |
| `requirements.txt` | Dépendances Python | ✅ Oui |
| `.env.example` | Template variables d'env (DB_PATH, MISTRAL_API_KEY, etc.) | ✅ Oui |
| `.gitignore` | Exclusions Git | ✅ Oui |
| `pyproject.toml` | Config projet (ruff ignore, etc.) | ✅ Oui |
| `pyrightconfig.json` | Config analyseur de types | ✅ Oui |
| `pytest.ini` | Config pytest (markers slow, e1, etc.) | ✅ Oui |
| `docker-compose.yml` | Stack Docker (API, Prometheus, Grafana, etc.) | ✅ Oui |
| `Dockerfile` | Image Docker | ✅ Oui |
| `Dockerfile.windows` | Image Docker Windows | ✅ Oui |

---

## 🟢 SCRIPTS .BAT — Lancement rapide

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `start_full.bat` | Lance Backend API + Cockpit Streamlit (2 fenêtres) | ✅ Oui |
| `lancer_tout.bat` | Variante démarrage complet | ✅ Oui |
| `start_cockpit.bat` | Lance Streamlit uniquement | ✅ Oui |
| `start_prometheus.bat` | Lance Prometheus | ✅ Oui |
| `start_grafana.bat` | Lance Grafana | ✅ Oui |
| `run_ruff.bat` | Lance le linter Ruff | ✅ Oui |

---

## 📂 src/ — Code source

### src/ racine (partagé ou legacy)

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `src/config.py` | Centralise config (DB, ports, env) — utilisé partout | ✅ Oui |
| `src/logging_config.py` | Config loguru | ✅ Oui |
| `src/metrics.py` | Métriques Prometheus (pipeline E1) | ✅ Oui |
| `src/dashboard.py` | Dashboard enrichissement — utilisé par E1Pipeline | ✅ Oui |
| `src/collection_report.py` | Rapport de collecte session — utilisé par E1Pipeline | ✅ Oui |
| ~~src/core.py~~ | Supprimé (doublon e1/core, jamais importé) | ❌ Nettoyé |
| ~~src/repository.py~~ | Supprimé (doublon e1/repository) | ❌ Nettoyé |
| `src/aggregator.py` | DataAggregator — utilisé par **regenerate_exports**, streamlit, test_zzdb | ✅ Oui |
| `src/exporter.py` | GoldExporter — utilisé par **regenerate_exports** | ✅ Oui |
| `src/analyzer.py` | SentimentAnalyzer — utilisé par **enrich_all_articles**, reanalyze_sentiment | ✅ Oui |
| `src/tagger.py` | TopicTagger — utilisé par **enrich_all_articles** | ✅ Oui |

### src/e1/ — Pipeline E1 (isolé)

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `src/e1/pipeline.py` | Orchestration pipeline E1 complet | ✅ Oui |
| `src/e1/core.py` | Extractors, ContentTransformer, Source — version E1 | ✅ Oui |
| `src/e1/repository.py` | CRUD DB pour E1 | ✅ Oui |
| `src/e1/aggregator.py` | Agrégation RAW/SILVER/GOLD | ✅ Oui |
| `src/e1/analyzer.py` | Analyse sentiment | ✅ Oui |
| `src/e1/tagger.py` | Classification topics | ✅ Oui |
| `src/e1/exporter.py` | Export Parquet/CSV | ✅ Oui |
| `src/e1/console.py` | Affichage console | ✅ Oui |
| `src/e1/ui_messages.py` | Messages UI | ✅ Oui |

### src/e2/ — API FastAPI

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `src/e2/api/main.py` | App FastAPI, routes | ✅ Oui |
| `src/e2/api/routes/*.py` | Routes (auth, raw, silver, gold, analytics, ai, sources) | ✅ Oui |
| `src/e2/api/services/*.py` | Services métier | ✅ Oui |
| `src/e2/api/schemas/*.py` | Schémas Pydantic | ✅ Oui |
| `src/e2/api/dependencies/*.py` | Auth, permissions | ✅ Oui |
| `src/e2/api/middleware/*.py` | Prometheus, audit | ✅ Oui |
| `src/e2/auth/security.py` | JWT, hash mots de passe | ✅ Oui |

### src/e3/ — Mistral IA

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `src/e3/mistral/service.py` | Client API Mistral | ✅ Oui |

### src/spark/ — PySpark

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `src/spark/session.py` | SparkSession singleton | ✅ Oui |
| `src/spark/adapters/gold_parquet_reader.py` | Lecture Parquet GOLD | ✅ Oui |
| `src/spark/processors/gold_processor.py` | Agrégations Big Data | ✅ Oui |
| `src/spark/interfaces/*.py` | Interfaces DIP | ✅ Oui |

### src/ml/ — Inférence ML

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `src/ml/inference/sentiment.py` | Inférence FlauBERT/CamemBERT | ✅ Oui |
| `src/ml/inference/goldai_loader.py` | Charge GoldAI Parquet | ✅ Oui |
| `src/ml/inference/local_hf_service.py` | Service local HuggingFace | ✅ Oui |

### src/streamlit/ — Cockpit

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `src/streamlit/app.py` | App Streamlit principale | ✅ Oui |
| `src/streamlit/auth_plug.py` | Plug auth (JWT) | ✅ Oui |

### src/shared/

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `src/shared/interfaces.py` | E1DataReader (contrat E2/E3) | ✅ Oui |

### src/storage/, src/api/, src/monitoring/

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `src/storage/mongo_gridfs.py` | Stockage MongoDB/GridFS | ⚠️ Optionnel (ZZDB) |
| ~~src/api/*~~ | Supprimé (doublon e2/api/) | ❌ Nettoyé |
| `src/monitoring/*` | Monitoring | ⚠️ À vérifier |

---

## 📜 scripts/ — Utilitaires

### Pipeline & DB

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `setup_with_sql.py` | Init DB SQLite + schéma | ✅ Oui |
| `show_tables.py` | Affiche structure tables | ✅ Oui |
| `show_db_stats.py` | Stats DB | ✅ Oui |
| `show_dashboard.py` | Dashboard enrichissement (console) | ✅ Oui |
| `regenerate_exports.py` | Régénère raw/silver/gold CSV + Parquet | ✅ Oui |
| `export_gold.py` | Export GOLD uniquement | ✅ Oui |
| `enrich_all_articles.py` | Enrichit topics + sentiment rétroactivement | ✅ Oui |
| `reanalyze_sentiment.py` | Ré-analyse sentiment de tous les articles | ✅ Oui |
| `migrate_sources.py` | Ajoute sources manquantes depuis config | ✅ Oui |

### Visualisation

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `view_exports.py` | Explorateur CSV interactif | ✅ Oui |
| `view_datasets.py` | Vue datasets | ✅ Oui |
| `quick_view.py` | Aperçu rapide GOLD | ✅ Oui |
| `visualize_sentiment.py` | Graphiques sentiment (PNG) | ✅ Oui |

### Parquet & GoldAI

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `merge_parquet_goldai.py` | Fusion incrémentale GOLD → GoldAI | ✅ Oui |
| `manage_parquet.py` | Manipulation Parquet (menu) | ✅ Oui |
| `list_mongo_parquet.py` | Liste Parquet dans Mongo | ⚠️ Si MongoDB actif |

### IA & ML

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `ai_benchmark.py` | Benchmark CamemBERT vs API | ✅ Oui |
| `ai_smoke_test.py` | Test rapide IA | ✅ Oui |
| `finetune_sentiment.py` | Fine-tuning modèle sentiment | ✅ Oui |
| `create_ia_copy.py` | Copie dataset pour IA | ⚠️ Utilitaire ponctuel |

### Veille

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `veille_digest.py` | Génère digest veille | ✅ Oui |
| `veille_sources.json` | Config sources veille | ✅ Oui |

### Tests / validation

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `validate_json.py` | Valide sources_config.json | ✅ Oui |
| `validate_e1_project.py` | Vérifie structure projet E1 | ✅ Oui |
| `test_pipeline.py` | Test pipeline | ✅ Oui |
| `test_before_build.py` | Pré-build checks | ✅ Oui |
| `test_project.py` | Tests projet | ✅ Oui |
| `test_spark_simple.py` | Test PySpark rapide | ✅ Oui |
| `test_zzdb.py` | Test source ZZDB | ⚠️ Si ZZDB utilisé |
| `run_e2_tests.py` | Lance tests E2 API | ✅ Oui |

### Users & auth

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `create_user.py` | Crée utilisateur | ✅ Oui |
| `create_test_user.py` | Crée user test | ✅ Oui |
| `init_profils_table.py` | Init table profils | ✅ Oui |

### Autres

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `scheduler.py` | Planification pipeline (cron-like) | ✅ Oui |
| `query_sqlite.py` | Requêtes SQL directes | ✅ Oui |
| `cleanup_sqlite_buffer.py` | Nettoyage buffer SQLite | ⚠️ Maintenance |
| `backup_parquet_to_mongo.py` | Backup Parquet → Mongo | ⚠️ Si Mongo |
| `audit_e1_coverage.py` | Audit couverture E1 | ⚠️ Diagnostic |
| `activate_zzdb_source.py` | Active source ZZDB | ⚠️ Si ZZDB |
| `check_kaggle_files.py` | Vérif fichiers Kaggle | ✅ Oui |
| `dossier_e1_examples.py` | Exemples E1 | ⚠️ Démo |
| `demo_proof_e1.py` | Preuve E1 | ⚠️ Démo |
| `demo_collecte.py` | Démo collecte | ⚠️ Démo |
| `verify_audit_trail.py` | Vérif audit trail | ✅ Oui |
| `deploy*.ps1`, `deploy.sh` | Déploiement | ⚠️ Ops |
| `check_docker*.ps1/sh` | Vérif Docker | ✅ Oui |

---

## 🧪 tests/

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `test_e1_isolation.py` | Tests non-régression E1 (CI) | ✅ Oui |
| `test_e2_api.py` | Tests API FastAPI | ✅ Oui |
| `test_spark_integration.py` | Tests PySpark | ✅ Oui |
| `test_e1_pipeline_quiet.py` | Test pipeline E1 quiet | ✅ Oui |
| `test_main_*.py` | Tests main | ✅ Oui |
| `test_init.py`, `test_pipeline_light.py`, etc. | Divers tests | ✅ Oui |
| `check_db_status.py`, `check_exports.py`, `check_kaggle_status.py` | Checks | ✅ Oui |
| `run_e1_isolation_tests.py` | Lanceur tests E1 | ✅ Oui |

---

## 📊 monitoring/

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `prometheus.local.yml` | Config Prometheus local | ✅ Oui |
| `prometheus.yml` | Config Prometheus | ✅ Oui |
| `prometheus_rules.yml` | Règles alertes | ✅ Oui |
| `grafana/dashboards/*.json` | Dashboards Grafana | ✅ Oui |
| `grafana/provisioning/*.yml` | Provisioning Grafana | ✅ Oui |

---

## 🔧 .github/workflows/

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `ci-cd.yml` | CI/CD principal (tests, build) | ✅ Oui |
| `test.yml` | Tests E1 | ✅ Oui |
| `build.yml` | Build image | ✅ Oui |

---

## 📄 DOC — Racine

| Fichier | Rôle | Utilisé ? |
|---------|------|-----------|
| `README.md` | Doc principale | ✅ Oui |
| `CHANGELOG.md` | Historique versions | ✅ Oui |
| `CONTRIBUTING.md` | Guide contributeurs | ✅ Oui |
| `LICENSE.md` | Licence | ✅ Oui |
| `LOGGING.md` | Doc logging | ✅ Oui |
| `FLOW_DONNEES.md` | Flow données | ✅ Oui |
| `LANCER_TOUT.md` | Doc démarrage | ✅ Oui |
| `README_DOCKER.md` | Doc Docker | ✅ Oui |
| `DEPLOY.md` | Déploiement | ✅ Oui |
| `GIT_IGNORE_GUIDE.md` | Guide .gitignore | ⚠️ Référence |
| `RUFF.md` | Doc Ruff | ⚠️ Ruff retiré du CI |
| `FICHIERS_FONCTIONNELS.md` | Liste fichiers (legacy) | ⚠️ Partiellement obsolète |

---

## ❌ FICHIERS INUTILES ou OBSOLÈTES

| Fichier | Raison |
|---------|--------|
| ~~fix_ruff_unicode.py~~ | Script one-shot correctif Unicode | ❌ Supprimé |
| ~~_fix_unicode_prometheus.py~~ | Correctif one-shot Unicode Prometheus | ❌ Supprimé |
| ~~src/api/~~ | Supprimé (doublon e2/api/) | ❌ Nettoyé |
| ~~src/repository.py~~ | Supprimé (doublon e1/repository) | ❌ Nettoyé |
| `RUFF.md` | Ruff retiré du CI — doc obsolète |
| `scripts/demo_*.py`, `dossier_e1_examples.py` | Démo — pas critique |

---

## 📋 RÉSUMÉ

- **~80+ fichiers utiles** (code, config, scripts, tests, monitoring)
- **~10 fichiers à nettoyer** (one-shot, doublons, démos)
- **Duplication connue** : `src/` racine (aggregator, analyzer, tagger, exporter) vs `src/e1/` — scripts legacy utilisent racine, pipeline E1 utilise e1/

---

*Généré pour analyse projet DataSens — à affiner selon usage réel.*
