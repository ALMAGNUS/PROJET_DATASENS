# Inventaire du dépôt DataSens (PROJET_DATASENS)

Document généré pour étude : liste **exhaustive des fichiers suivis par Git** (`git ls-files`).

- **Date de génération :** 2026-04-11
- **Nombre total de fichiers versionnés :** 574
- **Fichiers exclus de cette liste :** tout ce qui est dans `.gitignore` (ex. `data/`, `exports/`, `.env`, `*.db`, `logs/`, `output/`, caches, modèles lourds) et le dossier `.git/`.

---

## 1. Synthèse par dossier racine

| Dossier / zone | Fichiers |
|----------------|----------|
| `racine (fichiers seuls)` | 42 |
| `.github` | 4 |
| `docs` | 270 |
| `hadoop` | 2 |
| `monitoring` | 9 |
| `notebooks` | 15 |
| `reports` | 40 |
| `scripts` | 89 |
| `src` | 79 |
| `tests` | 21 |
| `zzdb` | 3 |

### Détail du dossier `docs/`

| Sous-zone | Fichiers |
|-----------|----------|
| Fichiers directement sous `docs/` | 94 |
| `docs/e2/` | 93 |
| `docs/e3/` | 6 |
| `docs/e4/` | 10 |
| `docs/e5/` | 7 |
| `docs/images/` | 1 |
| `docs/veille/` | 59 |

---

## 2. Inventaire détaillé par répertoire

### Racine du dépôt

*42 fichier(s)*

- `.env.example`
- `.gitignore`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `DEPLOY.md`
- `Dockerfile`
- `Dockerfile.windows`
- `FICHIERS_FONCTIONNELS.md`
- `FICHIERS_PROJET_DATASENS.md`
- `FLOW_DONNEES.md`
- `GIT_IGNORE_GUIDE.md`
- `LANCER_TOUT.md`
- `LICENSE.md`
- `LOGGING.md`
- `PLANCHE_LANCEMENT.md`
- `README.md`
- `README_DOCKER.md`
- `RUFF.md`
- `VEILLE_SENTIMENT_MODELS.md`
- `_fix_unicode_prometheus.py`
- `_launch_api.bat`
- `_launch_cockpit.bat`
- `docker-compose.yml`
- `fix_ruff_unicode.py`
- `lancer_tout.bat`
- `main.py`
- `pyproject.toml`
- `pyrightconfig.json`
- `pytest.ini`
- `redec_open_api.json`
- `requirements.txt`
- `run_daily.ps1`
- `run_e2_api.py`
- `run_ruff.bat`
- `sources_config.json`
- `start_cockpit.bat`
- `start_full.bat`
- `start_grafana.bat`
- `start_mongo.bat`
- `start_prometheus.bat`
- `start_uptime_kuma.bat`
- `validation_report.json`

### .github/

*4 fichier(s)*

- `.github/workflows/build.yml`
- `.github/workflows/ci-cd.yml`
- `.github/workflows/e3-quality-gate.yml`
- `.github/workflows/test.yml`

### docs/

#### Fichiers directement sous `docs/`

*94 fichier(s)*

- `docs/ACCESSIBILITE_DOCUMENTATION.md`
- `docs/AGILE_ROADMAP.md`
- `docs/AGILE_STRUCTURE.md`
- `docs/ARCHITECTURE.md`
- `docs/ARCHITECTURE_DB.md`
- `docs/ARCHITECTURE_METIER_ANALYSIS.md`
- `docs/AUDIT_AMELIORATIONS_MCO_MLOPS.md`
- `docs/AUDIT_ARCHITECTURE.md`
- `docs/AUDIT_E1_COMPETENCES.md`
- `docs/AUDIT_E2_COMPETENCES.md`
- `docs/AUDIT_E3_COMPETENCES.md`
- `docs/AUDIT_E4_ECART.md`
- `docs/AUDIT_E5_COMPETENCES.md`
- `docs/AUDIT_OOP_SOLID_DRY.md`
- `docs/AUDIT_TECHNIQUE.md`
- `docs/AUDIT_USER_ACTION_LOG.md`
- `docs/BIBLE_EXPLORATION_SQLITE.md`
- `docs/BUFFER_SQLITE_ARCHITECTURE.md`
- `docs/BUILD_AND_DEPLOY.md`
- `docs/CHEMIN_DONNEE.md`
- `docs/CODE_QUALITY_AUDIT.md`
- `docs/DASHBOARD_GUIDE.md`
- `docs/DATA_FLOW.md`
- `docs/DB_QUERIES.md`
- `docs/DB_QUERIES_EXCEL.md`
- `docs/DEPLOYMENT.md`
- `docs/Dossier_E1_C33_processus_agregation.md`
- `docs/Dossier_E1_dataset_IA_E2.md`
- `docs/Dossier_E1_nettoyage+scripts.md`
- `docs/Dossier_E1_preuves.md`
- `docs/Dossier_E1_prometheus_grafana_cicd.md`
- `docs/Dossier_E1_topics_sentiments+scripts.md`
- `docs/Dossier_E1_versioning_documentation.md`
- `docs/Dossier_E2_A3_C6_C7_C8.md`
- `docs/Dossier_E2_A3_C6_C7_C8_FINAL.md`
- `docs/Dossier_E2_A3_C6_C7_C8_FINAL_EXPORT_GDOCS.txt`
- `docs/Dossier_E2_A3_C6_C7_C8_FINAL_EXPORT_GDOCS_MIX.txt`
- `docs/Dossier_E2_A3_C6_C7_C8_FINAL_EXPORT_GDOCS_V2.txt`
- `docs/Dossier_E2_A3_C6_C7_C8_FINAL_VERSION_PROPRE.md`
- `docs/E1_CAPTURES_MONITORING.md`
- `docs/E1_ISOLATION_COMPLETE.md`
- `docs/E1_ISOLATION_STRATEGY.md`
- `docs/E1_PROTECTION.md`
- `docs/E1_STATUS.md`
- `docs/ENRICHISSEMENT.md`
- `docs/ER_DIAGRAM_ALL_TABLES.md`
- `docs/ER_DIAGRAM_COMPLET.md`
- `docs/ETAT_DES_LIEUX_RUN_ROUTES_STOCKAGE.md`
- `docs/EXPLICATION_RELATIONS_MERISE.md`
- `docs/FASTAPI_RBAC_IMPLEMENTATION.md`
- `docs/FASTAPI_UNIFIED_ARCHITECTURE.md`
- `docs/FLOW_KAGGLE_COMPLET.md`
- `docs/FLOW_KAGGLE_DB.md`
- `docs/GITHUB_PROJECTS_SETUP.md`
- `docs/KAGGLE_DATASETS_EXPLANATION.md`
- `docs/KAGGLE_DOSSIER_UNIQUE.md`
- `docs/METRIQUES_SEUILS_ALERTES.md`
- `docs/MISTRAL_IA_INSIGHTS.md`
- `docs/MONITORING_E2_API.md`
- `docs/ORGANISATION.md`
- `docs/PARQUET_MANAGEMENT.md`
- `docs/PHASE2_COMPLETE.md`
- `docs/PHASE3_PYSPARK_COMPLETE.md`
- `docs/PHASE_1_DOCKER_CI_CD_COMPLETE.md`
- `docs/PHASE_2_FASTAPI_RBAC_STATUS.md`
- `docs/PIPELINE_ANALYSIS.md`
- `docs/PLAN_ACTION_E1_E2_E3.md`
- `docs/PLAN_STREAMLIT_E2.md`
- `docs/PREPARATION_E2_E3.md`
- `docs/PROCEDURE_INCIDENTS.md`
- `docs/PROCEDURE_TRI_DONNEES_PERSONNELLES.md`
- `docs/PROJECT_ANALYSIS.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/PYSPARK_ACCUMULATION_STRATEGY.md`
- `docs/PYSPARK_INTEGRATION_STRATEGY.md`
- `docs/PYSPARK_SAFE_INTEGRATION.md`
- `docs/QUICK_START.md`
- `docs/QUICK_START_E1_ISOLATED.md`
- `docs/RBAC_ZONES_METIER.md`
- `docs/README.md`
- `docs/README_DOCKER.md`
- `docs/README_E2_API.md`
- `docs/REGISTRE_TRAITEMENTS_RGPD.md`
- `docs/RESUME_PROPOSITIONS.md`
- `docs/ROADMAP_EVOLUTION.md`
- `docs/SCHEMA_DESIGN.md`
- `docs/SCHEMA_PROFILS.md`
- `docs/TABLES_PROFILS_ACTION_LOG.md`
- `docs/VEILLE_PLANIFICATION.md`
- `docs/VERIFICATION_E2.md`
- `docs/VERIFICATION_NOM_TABLE_ACTION_LOG.md`
- `docs/VISION_ACADEMIQUE.md`
- `docs/VISUALISATION_SENTIMENT.md`
- `docs/WORKFLOW_PARQUET_PYSPARK.md`

#### `docs/e2/`

*93 fichier(s)*

- `docs/e2/AI_BENCHMARK.md`
- `docs/e2/AI_BENCHMARK_RESULTS.json`
- `docs/e2/AI_REQUIREMENTS.md`
- `docs/e2/ANNEXE_10_PREUVES_EXECUTION_E2.md`
- `docs/e2/ANNEXE_11_CAPTURES_E2.md`
- `docs/e2/ANNEXE_12_PLAN_DEMO_E2_15MIN.md`
- `docs/e2/ANNEXE_3_C7_PREUVE_EXECUTION_BENCHMARK.md`
- `docs/e2/ANNEXE_6_C6_GOOGLE_ALERTS_FEEDLY_MOTS_CLES.md`
- `docs/e2/ANNEXE_7_C6_PREUVE_COLLECTE_VEILLE.md`
- `docs/e2/ANNEXE_9_PREUVES_VISUELLES_MLOPS_API.md`
- `docs/e2/ANNEXE_C6_GOOGLE_ALERTS_MOTS_CLES.md`
- `docs/e2/ANNEXE_C6_SOURCES_MOTS_CLES.json`
- `docs/e2/ANNEXE_C6_SOURCES_MOTS_CLES.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-10.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-10.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-11.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-11.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-12.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-12.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-13.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-13.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-16.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-16.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-17.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-17.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-18.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-18.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-19.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-19.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-20.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-20.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-21.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-21.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-22.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-22.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-23.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-23.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-24.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-24.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-25.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-25.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-26.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-26.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-30.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-30.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-31.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-03-31.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-01.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-01.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-02.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-02.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-03.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-03.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-04.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-04.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-05.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-05.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-06.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-06.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-07.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-07.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-08.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-08.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-09.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-09.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-10.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-10.md`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-11.json`
- `docs/e2/ANNEXE_C6_VEILLE_2026-04-11.md`
- `docs/e2/E2_FAQ.md`
- `docs/e2/GUIDE_BENCHMARK_FINETUNING.md`
- `docs/e2/HF_MODEL_DEPLOY_RUNBOOK.md`
- `docs/e2/HF_MODEL_PUBLISH.json`
- `docs/e2/ML_PIPELINE_SPLIT_STEP1.md`
- `docs/e2/ML_PIPELINE_SPLIT_STEP2.md`
- `docs/e2/ML_PIPELINE_SPLIT_STEP3.md`
- `docs/e2/MODELE_TAXONOMIE.md`
- `docs/e2/README.md`
- `docs/e2/STRATEGIE_MODELE_MLOPS.md`
- `docs/e2/TRAINING_RESULTS.json`
- `docs/e2/TRAINING_RESULTS_QUICK.json`
- `docs/e2/figures/e2_benchmark_class_imbalance.png`
- `docs/e2/figures/e2_benchmark_curves_normalized.png`
- `docs/e2/figures/e2_benchmark_f1_per_class.png`
- `docs/e2/figures/e2_benchmark_overview.png`
- `docs/e2/figures/e2_inference_confidence_by_class.png`
- `docs/e2/figures/e2_inference_latency.png`
- `docs/e2/figures/e2_inference_probability_profiles.png`
- `docs/e2/figures/e2_inference_sentiment_distribution.png`
- `docs/e2/figures/e2_innovation_pareto_quality_latency.png`
- `docs/e2/figures/e2_training_quick_loss_curve.png`
- `docs/e2/figures/e2_training_quick_runtime.png`
- `docs/e2/figures/e2_training_quick_validation_metrics.png`

#### `docs/e3/`

*6 fichier(s)*

- `docs/e3/ANNEXE_1_PREUVES_EXECUTION_QUALITY_GATE.md`
- `docs/e3/ANNEXE_2_CAPTURES_E3.md`
- `docs/e3/ANNEXE_3_PLAN_DEMO_E3_15MIN.md`
- `docs/e3/ANNEXE_4_EXTRAITS_CODE_E3.md`
- `docs/e3/DOSSIER_E3_A4_A5_C9_C10_C11_C12_C13.md`
- `docs/e3/README.md`

#### `docs/e4/`

*10 fichier(s)*

- `docs/e4/ANNEXE_1_PREUVES_E4.md`
- `docs/e4/ANNEXE_2_CAPTURES_E4.md`
- `docs/e4/ANNEXE_3_PLAN_DEMO_E4.md`
- `docs/e4/ANNEXE_4_EXTRAITS_CODE_E4.md`
- `docs/e4/CD_CHAINE_LIVRAISON.md`
- `docs/e4/CI_CHAINE_TESTS.md`
- `docs/e4/DOSSIER_E4_A6_A7_A8_C14_C15_C16_C17_C18_C19.md`
- `docs/e4/OBJECTIFS_ACCESSIBILITE.md`
- `docs/e4/PARCOURS_UTILISATEUR.md`
- `docs/e4/README.md`

#### `docs/e5/`

*7 fichier(s)*

- `docs/e5/ANNEXE_1_PREUVES_EXECUTION_E5.md`
- `docs/e5/ANNEXE_2_CAPTURES_E5.md`
- `docs/e5/ANNEXE_3_PLAN_DEMO_E5.md`
- `docs/e5/ANNEXE_4_EXTRAITS_CODE_E5.md`
- `docs/e5/DOSSIER_E5_A9_C20_C21.md`
- `docs/e5/PROCEDURE_INSTALLATION_MONITORING.md`
- `docs/e5/README.md`

#### `docs/images/`

*1 fichier(s)*

- `docs/images/README.md`

#### `docs/veille/`

*59 fichier(s)*

- `docs/veille/README.md`
- `docs/veille/veille_2026-02-12.md`
- `docs/veille/veille_2026-03-09.md`
- `docs/veille/veille_2026-03-10.json`
- `docs/veille/veille_2026-03-10.md`
- `docs/veille/veille_2026-03-11.json`
- `docs/veille/veille_2026-03-11.md`
- `docs/veille/veille_2026-03-12.json`
- `docs/veille/veille_2026-03-12.md`
- `docs/veille/veille_2026-03-13.json`
- `docs/veille/veille_2026-03-13.md`
- `docs/veille/veille_2026-03-16.json`
- `docs/veille/veille_2026-03-16.md`
- `docs/veille/veille_2026-03-17.json`
- `docs/veille/veille_2026-03-17.md`
- `docs/veille/veille_2026-03-18.json`
- `docs/veille/veille_2026-03-18.md`
- `docs/veille/veille_2026-03-19.json`
- `docs/veille/veille_2026-03-19.md`
- `docs/veille/veille_2026-03-20.json`
- `docs/veille/veille_2026-03-20.md`
- `docs/veille/veille_2026-03-21.json`
- `docs/veille/veille_2026-03-21.md`
- `docs/veille/veille_2026-03-22.json`
- `docs/veille/veille_2026-03-22.md`
- `docs/veille/veille_2026-03-23.json`
- `docs/veille/veille_2026-03-23.md`
- `docs/veille/veille_2026-03-24.json`
- `docs/veille/veille_2026-03-24.md`
- `docs/veille/veille_2026-03-25.json`
- `docs/veille/veille_2026-03-25.md`
- `docs/veille/veille_2026-03-26.json`
- `docs/veille/veille_2026-03-26.md`
- `docs/veille/veille_2026-03-30.json`
- `docs/veille/veille_2026-03-30.md`
- `docs/veille/veille_2026-03-31.json`
- `docs/veille/veille_2026-03-31.md`
- `docs/veille/veille_2026-04-01.json`
- `docs/veille/veille_2026-04-01.md`
- `docs/veille/veille_2026-04-02.json`
- `docs/veille/veille_2026-04-02.md`
- `docs/veille/veille_2026-04-03.json`
- `docs/veille/veille_2026-04-03.md`
- `docs/veille/veille_2026-04-04.json`
- `docs/veille/veille_2026-04-04.md`
- `docs/veille/veille_2026-04-05.json`
- `docs/veille/veille_2026-04-05.md`
- `docs/veille/veille_2026-04-06.json`
- `docs/veille/veille_2026-04-06.md`
- `docs/veille/veille_2026-04-07.json`
- `docs/veille/veille_2026-04-07.md`
- `docs/veille/veille_2026-04-08.json`
- `docs/veille/veille_2026-04-08.md`
- `docs/veille/veille_2026-04-09.json`
- `docs/veille/veille_2026-04-09.md`
- `docs/veille/veille_2026-04-10.json`
- `docs/veille/veille_2026-04-10.md`
- `docs/veille/veille_2026-04-11.json`
- `docs/veille/veille_2026-04-11.md`

### hadoop/

*2 fichier(s)*

- `hadoop/README.md`
- `hadoop/bin/.gitkeep`

### monitoring/

*9 fichier(s)*

- `monitoring/README_GRAFANA.md`
- `monitoring/grafana/dashboards/datasens-e1-dashboard.json`
- `monitoring/grafana/dashboards/datasens-full.json`
- `monitoring/grafana/provisioning/dashboards/dashboard.yml`
- `monitoring/grafana/provisioning/datasources/prometheus.yml`
- `monitoring/prometheus.docker.yml`
- `monitoring/prometheus.local.yml`
- `monitoring/prometheus.yml`
- `monitoring/prometheus_rules.yml`

### notebooks/

*15 fichier(s)*

- `notebooks/datasens_E1/01_setup_env.ipynb`
- `notebooks/datasens_E1/02_schema_create.ipynb`
- `notebooks/datasens_E1/02_schema_create_SIMPLE.ipynb`
- `notebooks/datasens_E1/03_MINI_SCHEMA.ipynb`
- `notebooks/datasens_E1/03a_ingest_sources_top5.ipynb`
- `notebooks/datasens_E1/03b_ingest_sources_media.ipynb`
- `notebooks/datasens_E1/03c_ingest_sources_advanced.ipynb`
- `notebooks/datasens_E1/03d_data_cleaning_pipeline.ipynb`
- `notebooks/datasens_E1/04_crud_tests.ipynb`
- `notebooks/datasens_E1/05_snapshot_and_readme.ipynb`
- `notebooks/datasens_E1/06_topics_and_tagging.ipynb`
- `notebooks/datasens_E1/07_manual_data_sources.ipynb`
- `notebooks/datasens_E1/08_data_validation_quality.ipynb`
- `notebooks/datasens_E1/09_model_output_preparation.ipynb`
- `notebooks/datasens_E1_v1/E1_UNIFIED_MINIMAL.ipynb`

### reports/

*40 fichier(s)*

- `reports/db_state_2026-03-26T112357Z.json`
- `reports/db_state_2026-03-26T112357Z.md`
- `reports/db_state_2026-03-26T112535Z.json`
- `reports/db_state_2026-03-26T112535Z.md`
- `reports/db_state_2026-03-30T095034Z.json`
- `reports/db_state_2026-03-30T095034Z.md`
- `reports/db_state_2026-03-31T070030Z.json`
- `reports/db_state_2026-03-31T070030Z.md`
- `reports/db_state_2026-04-01T070318Z.json`
- `reports/db_state_2026-04-01T070318Z.md`
- `reports/db_state_2026-04-01T073038Z.json`
- `reports/db_state_2026-04-01T073038Z.md`
- `reports/db_state_2026-04-01T074220Z.json`
- `reports/db_state_2026-04-01T074220Z.md`
- `reports/db_state_2026-04-01T164703Z.json`
- `reports/db_state_2026-04-01T164703Z.md`
- `reports/db_state_2026-04-01T164839Z.json`
- `reports/db_state_2026-04-01T164839Z.md`
- `reports/db_state_2026-04-02T131310Z.json`
- `reports/db_state_2026-04-02T131310Z.md`
- `reports/db_state_2026-04-04T105652Z.json`
- `reports/db_state_2026-04-04T105652Z.md`
- `reports/db_state_2026-04-05T090756Z.json`
- `reports/db_state_2026-04-05T090756Z.md`
- `reports/db_state_2026-04-06T082902Z.json`
- `reports/db_state_2026-04-06T082902Z.md`
- `reports/db_state_2026-04-07T064544Z.json`
- `reports/db_state_2026-04-07T064544Z.md`
- `reports/db_state_2026-04-07T071304Z.json`
- `reports/db_state_2026-04-07T071304Z.md`
- `reports/db_state_2026-04-08T072154Z.json`
- `reports/db_state_2026-04-08T072154Z.md`
- `reports/db_state_2026-04-09T065158Z.json`
- `reports/db_state_2026-04-09T065158Z.md`
- `reports/db_state_2026-04-10T063540Z.json`
- `reports/db_state_2026-04-10T063540Z.md`
- `reports/db_state_2026-04-10T145459Z.json`
- `reports/db_state_2026-04-10T145459Z.md`
- `reports/db_state_2026-04-11T070905Z.json`
- `reports/db_state_2026-04-11T070905Z.md`

### scripts/

*89 fichier(s)*

- `scripts/QUERIES_SQL.md`
- `scripts/README.md`
- `scripts/SCRIPTS_LIST.md`
- `scripts/_check_training_metrics.py`
- `scripts/_run_migration.py`
- `scripts/activate_zzdb_source.py`
- `scripts/ai_benchmark.py`
- `scripts/ai_smoke_test.py`
- `scripts/audit_e1_coverage.py`
- `scripts/backup_parquet_to_mongo.py`
- `scripts/bootstrap_ml_labels.py`
- `scripts/build_gold_branches.py`
- `scripts/check_deploy.ps1`
- `scripts/check_docker.ps1`
- `scripts/check_docker.sh`
- `scripts/check_inference_quality.py`
- `scripts/check_kaggle_files.py`
- `scripts/cleanup_sqlite_buffer.bat`
- `scripts/cleanup_sqlite_buffer.py`
- `scripts/cleanup_sqlite_buffer.sh`
- `scripts/create_ia_copy.py`
- `scripts/create_test_user.py`
- `scripts/create_user.py`
- `scripts/db_state_report.py`
- `scripts/demo_collecte.py`
- `scripts/demo_proof_e1.py`
- `scripts/deploy.ps1`
- `scripts/deploy.sh`
- `scripts/deploy_clean.ps1`
- `scripts/dossier_e1_examples.py`
- `scripts/download_winutils.bat`
- `scripts/download_winutils.ps1`
- `scripts/enrich_all_articles.py`
- `scripts/export_gold.py`
- `scripts/export_mistral_dataset.py`
- `scripts/finetune_sentiment.bat`
- `scripts/finetune_sentiment.py`
- `scripts/fix_venv.bat`
- `scripts/init_profils_table.py`
- `scripts/inject_csv.py`
- `scripts/kill_port_8001.ps1`
- `scripts/list_mongo_parquet.py`
- `scripts/manage_parquet.bat`
- `scripts/manage_parquet.py`
- `scripts/manage_parquet.sh`
- `scripts/merge_parquet_goldai.bat`
- `scripts/merge_parquet_goldai.py`
- `scripts/merge_parquet_goldai.sh`
- `scripts/migrate_sources.py`
- `scripts/plot_e2_results.py`
- `scripts/plot_inference_results.py`
- `scripts/publish_best_model_to_hf.py`
- `scripts/pyspark_shell.py`
- `scripts/query_sqlite.py`
- `scripts/quick_view.py`
- `scripts/reanalyze_sentiment.py`
- `scripts/regenerate_exports.py`
- `scripts/run_benchmark_e2.bat`
- `scripts/run_benchmark_et_plots.bat`
- `scripts/run_daily_pipeline.ps1`
- `scripts/run_e1_metrics.py`
- `scripts/run_e2_tests.py`
- `scripts/run_e3_quality_gate.py`
- `scripts/run_e5_verification.py`
- `scripts/run_inference_pipeline.py`
- `scripts/run_ruff.ps1`
- `scripts/run_training_loop_e2.bat`
- `scripts/scheduler.py`
- `scripts/setup_with_sql.py`
- `scripts/show_dashboard.py`
- `scripts/show_db_stats.py`
- `scripts/show_tables.py`
- `scripts/start_pyspark_shell.bat`
- `scripts/start_pyspark_shell.sh`
- `scripts/test_before_build.py`
- `scripts/test_ml_sentiment.ps1`
- `scripts/test_pipeline.py`
- `scripts/test_project.py`
- `scripts/test_spark_simple.py`
- `scripts/test_zzdb.py`
- `scripts/validate_e1_project.py`
- `scripts/validate_json.py`
- `scripts/veille_digest.py`
- `scripts/veille_sources.json`
- `scripts/verify_audit_fixes.py`
- `scripts/verify_audit_trail.py`
- `scripts/view_datasets.py`
- `scripts/view_exports.py`
- `scripts/visualize_sentiment.py`

### src/

*79 fichier(s)*

- `src/__init__.py`
- `src/collection_report.py`
- `src/config.py`
- `src/dashboard.py`
- `src/data_contracts/__init__.py`
- `src/data_contracts/guards.py`
- `src/data_contracts/schemas.py`
- `src/datasets/__init__.py`
- `src/datasets/gold_branches.py`
- `src/e1/__init__.py`
- `src/e1/aggregator.py`
- `src/e1/analyzer.py`
- `src/e1/console.py`
- `src/e1/core.py`
- `src/e1/exporter.py`
- `src/e1/pipeline.py`
- `src/e1/repository.py`
- `src/e1/tagger.py`
- `src/e1/ui_messages.py`
- `src/e2/__init__.py`
- `src/e2/api/__init__.py`
- `src/e2/api/dependencies/__init__.py`
- `src/e2/api/dependencies/auth.py`
- `src/e2/api/dependencies/permissions.py`
- `src/e2/api/main.py`
- `src/e2/api/middleware/__init__.py`
- `src/e2/api/middleware/audit.py`
- `src/e2/api/middleware/prometheus.py`
- `src/e2/api/routes/__init__.py`
- `src/e2/api/routes/ai.py`
- `src/e2/api/routes/analytics.py`
- `src/e2/api/routes/auth.py`
- `src/e2/api/routes/gold.py`
- `src/e2/api/routes/raw.py`
- `src/e2/api/routes/silver.py`
- `src/e2/api/routes/sources.py`
- `src/e2/api/schemas/__init__.py`
- `src/e2/api/schemas/ai.py`
- `src/e2/api/schemas/article.py`
- `src/e2/api/schemas/auth.py`
- `src/e2/api/schemas/source.py`
- `src/e2/api/schemas/token.py`
- `src/e2/api/schemas/user.py`
- `src/e2/api/services/__init__.py`
- `src/e2/api/services/data_service.py`
- `src/e2/api/services/user_service.py`
- `src/e2/auth/__init__.py`
- `src/e2/auth/security.py`
- `src/e3/__init__.py`
- `src/e3/mistral/__init__.py`
- `src/e3/mistral/service.py`
- `src/logging_config.py`
- `src/metrics.py`
- `src/ml/__init__.py`
- `src/ml/inference/__init__.py`
- `src/ml/inference/goldai_loader.py`
- `src/ml/inference/local_hf_service.py`
- `src/ml/inference/sentiment.py`
- `src/monitoring/__init__.py`
- `src/observability/lineage_service.py`
- `src/shared/__init__.py`
- `src/shared/interfaces.py`
- `src/spark/__init__.py`
- `src/spark/adapters/__init__.py`
- `src/spark/adapters/gold_parquet_reader.py`
- `src/spark/interfaces/__init__.py`
- `src/spark/interfaces/data_processor.py`
- `src/spark/interfaces/data_reader.py`
- `src/spark/processors/__init__.py`
- `src/spark/processors/gold_processor.py`
- `src/spark/session.py`
- `src/storage/__init__.py`
- `src/storage/mongo_gridfs.py`
- `src/streamlit/__init__.py`
- `src/streamlit/app.py`
- `src/streamlit/auth_plug.py`
- `src/streamlit/components/__init__.py`
- `src/streamlit/metrics.py`
- `src/streamlit/pages/__init__.py`

### tests/

*21 fichier(s)*

- `tests/README_E1_ISOLATION.md`
- `tests/check_db_status.py`
- `tests/check_exports.py`
- `tests/check_kaggle_status.py`
- `tests/run_e1_isolation_tests.py`
- `tests/test_data_contracts_guards.py`
- `tests/test_e1_isolation.py`
- `tests/test_e1_pipeline_quiet.py`
- `tests/test_e2_api.py`
- `tests/test_e3_quality_gate.py`
- `tests/test_gold_branches.py`
- `tests/test_goldai_loader_ids.py`
- `tests/test_inference_predictions.py`
- `tests/test_init.py`
- `tests/test_kaggle_quick.py`
- `tests/test_main_minimal.py`
- `tests/test_main_quick.py`
- `tests/test_main_run.py`
- `tests/test_pipeline_light.py`
- `tests/test_spark_integration.py`
- `tests/test_ui_messages.py`

### zzdb/

*3 fichier(s)*

- `zzdb/__init__.py`
- `zzdb/catapulte_to_pipeline.py`
- `zzdb/cycle_faker_10.py`

---

## 3. Hors périmètre Git (données locales typiques)

Ces emplacements existent souvent sur une machine de dev mais **ne sont pas listés ici** s'ils sont ignorés :

- `data/` — raw, silver, gold, lake, goldai, etc.
- `exports/` — CSV/exports
- `*.db`, `*.sqlite` — SQLite
- `logs/`, `*.log`
- `output/` — artefacts scraping (Botasaurus)
- `.venv/`, `venv/` — environnement Python
- `models/`, `.cache/` — modèles et caches HF
- `error_logs/` — captures d'erreur locales
- `README.pdf` — si présent non versionné

Pour lister les fichiers ignorés présents sur le disque : `git status --ignored` (peut être volumineux).

---

## 4. Documents de référence dans le dépôt

- `FICHIERS_FONCTIONNELS.md` — autre vue fonctionnelle des fichiers.
- `FICHIERS_PROJET_DATASENS.md` — inventaire / périmètre projet.
- `docs/PROJECT_STRUCTURE.md` — structure documentée (à recouper avec l'arborescence réelle `src/e1/`, etc.).

