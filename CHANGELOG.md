# CHANGELOG — DataSens E1

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

---

## [Unreleased]

### Cockpit ops, lineage par les lignes, audit code (2026-05-08)

#### Added

- `scripts/change_password.py`
  - mise à jour ciblée du `password_hash` (bcrypt) dans la table SQLite `profils`,
  - flags : `--list` (recense les comptes existants), saisie masquée + double confirmation,
  - documenté dans le help sidebar du cockpit (`auth_plug.FORGOT_PASSWORD_HELP`).
- `src/streamlit/data_lineage.py` — panneau `Trace par les lignes`
  - tracé d'un même échantillon d'articles (3 à 15) à travers les 4 couches de stockage : SQLite `raw_data`, Parquet GOLD du jour, Parquet GoldAI consolidé, Parquet lu depuis MongoDB GridFS,
  - clé universelle `fingerprint`, validation end-to-end avec compteur de lignes communes,
  - intégration dans `Pipeline & Données → Run & Fusion` après le suivi d'un article unique.
- `docs/AUDIT_CODE_NETTOYAGE.md`
  - inventaire des candidats au nettoyage (racine, dossiers, scripts, code),
  - plan d'exécution séquencé par ordre de risque, exécution tracée au fil des étapes.
- `archive/legacy_docs/`
  - dossier d'archivage pour les vues d'inventaire historiques (préservation hors runtime).

#### Changed

- Code source — étape 7 de nettoyage (`docs/AUDIT_CODE_NETTOYAGE.md`)
  - passe ruff complète sur `src/` et `scripts/` : 471 issues détectées au démarrage, **0 issue** à la sortie,
  - 466 fixes appliqués automatiquement en 2 passes (safe puis unsafe-fixes),
  - 3 résiduelles fixées manuellement : variable de loop renommée en `_` (`scripts/plot_inference_results.py`), 2 branches `if` redondantes combinées (`src/streamlit/data_lineage.py`),
  - 5 RUF002 (typographie française dans docstrings : `×`, `’`) ajoutées à la liste `ignore` de `pyproject.toml` par cohérence avec RUF001/RUF003 déjà ignorées,
  - 65 fichiers modifiés (1 535 insertions, 3 494 suppressions, ~ 2 000 lignes nettes de code mort retirées : imports inutilisés, variables locales non utilisées copiées-collées entre page_modules cockpit, f-strings vides, with imbriqués, etc.),
  - smoke tests imports : `src`, `src.e2.api.main` (34 routes), 8 page_modules cockpit, pipeline E1, ML inference — tous OK,
  - pytest complet (sans `test_spark_integration.py`) : 51 passed, 1 deselected (le test pré-existant d'encodage Windows signalé en étape 6, indépendant).
- Code source — étape 6 de nettoyage (`docs/AUDIT_CODE_NETTOYAGE.md`)
  - `src/__init__.py` : suppression de 3 `print()` au top-level qui polluaient stdout à chaque import du package (visibles dans cockpit, API, tests). L'initialisation de `DATA_ROOT` est conservée, en mode silencieux,
  - `src/streamlit/auth_plug.py` : suppression d'un bloc OAuth2 entièrement commenté avec TODO placeholder (`login_oauth2`). À réintroduire dans un commit dédié si nécessaire,
  - `src/e2/api/routes/silver.py` : 4 TODO traités. Les endpoints POST/PUT/DELETE renvoient 501 **par conception** (isolation E1, E2 lecture seule). Les `detail` HTTPException reformulés en `is not supported (E1 isolation by design)` pour ne plus suggérer une fonctionnalité à venir. Le TODO de pagination supprimé (limite 1000 par défaut cohérente avec le cockpit),
  - `src/e2/api/routes/gold.py` : 1 TODO de pagination supprimé (idem silver),
  - vérification : `rg "TODO\|FIXME\|HACK\|XXX" src/` → 0 occurrence ; suite pytest sur silver/gold : 17/18 OK ; ruff sur les 4 fichiers modifiés : 0 erreur.
- Dossier `scripts/` — étape 5 de nettoyage (`docs/AUDIT_CODE_NETTOYAGE.md`)
  - décision révisée après lecture du code : la consolidation `scripts/inspect.py` initialement prévue (8 scripts d'exploration → 1) aurait cassé 10+ documents (Quick Start, Visualisation, Architecture DB, Project Structure, etc.) qui référencent ces scripts par nom direct, pour un gain de maintenance nul (chaque script < 200 lignes, fait une chose, nom parlant),
  - action retenue : archivage des 2 doublons silencieux uniquement,
    - `show_db_stats.py` archivé (doublon fonctionnel de `show_dashboard.py` : reproduit à la main via SQL ce que `DataSensDashboard` fait via la classe `src/dashboard.py`),
    - `view_datasets.py` archivé (variante plus complète de `view_exports.py` mais aucune référence dans la doc),
  - les 6 scripts d'exploration utiles restent en `scripts/` : `query_sqlite.py`, `show_tables.py`, `show_dashboard.py`, `quick_view.py`, `view_exports.py`, `visualize_sentiment.py`,
  - aucune doc ni code à modifier (les archivés n'avaient pas de référence active).
- Dossier `scripts/` — étape 4 de nettoyage (`docs/AUDIT_CODE_NETTOYAGE.md`)
  - création de `scripts/_archive/`, archivage de 17 scripts (88 → 71 fichiers actifs),
  - Catégorie A (one-shot et démos terminés, 11 scripts) : `_run_migration.py`, `_check_training_metrics.py`, `audit_e1_coverage.py`, `verify_audit_fixes.py`, `demo_collecte.py`, `demo_proof_e1.py`, `dossier_e1_examples.py`, `check_kaggle_files.py`, `activate_zzdb_source.py`, `inject_csv.py`, `migrate_sources.py`,
  - Catégorie B (smoke tests ad-hoc redondants avec `tests/`, 6 scripts) : `test_pipeline.py`, `test_project.py`, `test_zzdb.py`, `test_spark_simple.py`, `test_before_build.py`, `ai_smoke_test.py`,
  - 10 décisions d'audit révisées car références actives détectées (`setup_with_sql.py` cité dans RUNBOOK, `enrich_all_articles.py` cité par `src/dashboard.py:313`, `regenerate_exports.py` cité par `db_state_report.py:443`, etc.) — scripts conservés en `scripts/`,
  - mass-update : `pyproject.toml` (`exclude = ["scripts/_archive"]`), `scripts/README.md`, `scripts/SCRIPTS_LIST.md` (note d'en-tête + tableau résumé), `docs/VISUALISATION_SENTIMENT.md`, `docs/Dossier_E1_preuves.md`, `docs/GUIDE_ARCHITECTURE_MODE_EMPLOI_FICHIERS.md`.
- Dossiers du dépôt — étape 3 de nettoyage (`docs/AUDIT_CODE_NETTOYAGE.md`)
  - suppression de `spark-temp/` (dossier temporaire vide, recréé auto si Spark relancé),
  - suppression de `output/` (3 artefacts JSON Botasaurus, régénérés à chaque scrape),
  - décision révisée : `hadoop/` conservé (`winutils.exe` requis par PySpark sur Windows, fixé comme `HADOOP_HOME` dans `src/spark/session.py`),
  - `backups/retag_*` : suppression du dossier vide `retag_goldai_20260418_161355` et du doublon le plus ancien `retag_20260418_154959` (191 MB libérés). Conservation par sécurité de `retag_20260418_155207` (snapshot retag complet) et `retag_goldai_20260418_161455` (snapshot goldai consolidé),
  - total disque libéré : ~ 192 MB. Aucune modification de `.gitignore` (tous les chemins déjà couverts).
- Racine du dépôt — étape 2 de nettoyage (`docs/AUDIT_CODE_NETTOYAGE.md`)
  - suppression de 4 fossiles : `pipeline.log` (2 KB, log écrasé par `logs/datasens.log` depuis 12/2025), `mlflow.db` (440 KB, redondant avec `mlruns/`), `datasens.db` racine (56 KB, doublon mort de `~/datasens_project/datasens.db` actif à 91 MB), `Dockerfile.windows` (0.6 KB, variante orpheline non référencée),
  - décisions d'audit révisées après inspection des dépendances : `_launch_api.bat`, `_launch_cockpit.bat`, `run_ruff.bat` conservés car réellement utilisés (`lancer_tout.bat`, `start_full.bat`, `src/streamlit/_cockpit_helpers.py`, `README.md`, `CONTRIBUTING.md`),
  - `.gitignore` inchangé : tous les fossiles supprimés étaient déjà couverts (`*.log`, `*.db`, `mlflow.db`),
  - smoke test post-suppression : import `src.streamlit._cockpit_helpers` OK, aucune régression.
- Racine du dépôt — étape 1b de nettoyage (`docs/AUDIT_CODE_NETTOYAGE.md`)
  - `LANCER_TOUT.md` + `PLANCHE_LANCEMENT.md` consolidés dans `RUNBOOK.md` (originaux archivés dans `archive/legacy_docs/`),
  - `LOGGING.md` déplacé vers `docs/dev/LOGGING.md`,
  - `FLOW_DONNEES.md` déplacé vers `docs/dev/FLOW_DONNEES.md`,
  - `README_DOCKER.md` déplacé et renommé vers `docs/dev/DOCKER_RUNTIME.md`,
  - mass-update de 25+ références dans `README.md`, `CONTRIBUTING.md`, audits E1/E4/E5, dossiers E3/E5, `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/Dossier_E1_versioning_documentation.md`, `docs/ROADMAP_EVOLUTION.md`, `docs/AGILE_STRUCTURE.md`, `docs/e5/README.md`, `docs/e5/ANNEXE_3_PLAN_DEMO_E5.md`,
  - racine désormais à 6 fichiers .md : `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `DEPLOY.md`, `LICENSE.md`, `RUNBOOK.md`.
- `RUNBOOK.md` (nouveau)
  - inventaire unique des services (ports, dépendances, commandes),
  - 5 scénarios standardisés : Docker Compose, local, fine-tuning + MLflow, pipeline E1 seul, cockpit + API rapide,
  - section dédiée MongoDB (container vs natif Windows 7.0.28),
  - checklist de mise en service, dépannage NumPy / Docker / port / GridFS,
  - références croisées vers `docs/dev/` et `docs/e5/PROCEDURE_INSTALLATION_MONITORING.md`.
- `docs/dev/` (nouveau)
  - regroupe la documentation technique opérée par les développeurs : `LOGGING.md`, `FLOW_DONNEES.md`, `DOCKER_RUNTIME.md`.
- `docs/GUIDE_ARCHITECTURE_MODE_EMPLOI_FICHIERS.md`
  - introduction reformulée : ce guide devient le document unique de référence, les anciennes vues d'inventaire pointent désormais vers `archive/legacy_docs/`,
  - section `Références croisées utiles` mise à jour.
- Racine du dépôt — étape 1a de nettoyage (`docs/AUDIT_CODE_NETTOYAGE.md`)
  - `INVENTAIRE_PROJET.md`, `FICHIERS_PROJET_DATASENS.md`, `FICHIERS_FONCTIONNELS.md`, `GUIDE_NETTOYAGE_MANUEL.md` déplacés dans `archive/legacy_docs/` (auto-référents, remplacés par `docs/GUIDE_ARCHITECTURE_MODE_EMPLOI_FICHIERS.md`),
  - `GIT_IGNORE_GUIDE.md` et `RUFF.md` supprimés (contenu trivial, sans référence pédagogique).

#### Fixed

- `tests/test_gold_branches.py::test_build_gold_ia_labelled_creates_sentiment_label` — désalignement test ↔ contrat de l'API. Le code de production (`src/datasets/gold_branches.py::normalize_sentiment_label`) retire volontairement les accents via `_ascii_fold` pour absorber les corruptions d'encodage Windows/Spark/CSV (docstring : *"Makes label matching encoding-agnostic"*). Le test attendait `"négatif"` ; le code retourne `"negatif"`. Assertion réalignée sur `["positif", "negatif"]`. Le test devient une vérification explicite du comportement de normalisation.
- `src/e2/api/schemas/article.py` — `ArticleBase.url` et `ArticleUpdate.url` passés de `max_length=500` à `max_length=2048`. La contrainte était trop serrée pour des URL réelles (Google News avec UUID encodé, redirections trackées, paramètres OAuth) et provoquait des `ValidationError` lors du listage GOLD avec un dataset issu du pipeline. Aligné avec la limite RFC navigateurs. Tests `test_reader_can_read` et `test_list_gold_articles_authorized` à nouveau verts.
- Suite pytest complète (hors `test_spark_integration.py`) : **52 passed, 0 failed**.

### Préparation dataset IA, portage Colab, taxonomie cockpit (2026-05-08)

#### Added

- `notebooks/colab_finetune_sentiment.ipynb`
  - notebook 5 cellules (install / upload bundle / chargement / fine-tuning / évaluation),
  - `class_weight="balanced"` pour compenser le déséquilibre de classes,
  - export du modèle entraîné en archive téléchargeable.
- `exports/colab/colab_bundle.zip`
  - archive `train/val/test.parquet` prête pour le notebook Colab.
- `scripts/install_colab_model.py`
  - installation d'un modèle fine-tuné Colab dans le pipeline local en une commande:
    extraction archive, validation des artefacts HuggingFace requis, smoke test de chargement,
    mise à jour `SENTIMENT_FINETUNED_MODEL_PATH` dans `.env`.
- `src/streamlit/page_modules/pipeline_data.py`, `ia_models.py`, `pilotage_ops.py`
  - wrappers d'onglets regroupant les modules existants par finalité fonctionnelle via sous-onglets `st.tabs`.
- Panneau `Lineage de la donnée` (4 cartes : SQLite -> Parquet GOLD -> GoldAI consolidé -> GridFS MongoDB)
  - rendu en `Vue d'ensemble` (déclenchement immédiat sur le local; vérification GridFS à la demande),
  - rendu en `Pilotage & Ops -> Santé & MongoDB` (vue détaillée avec contrôle de cohérence end-to-end).
- 5e étape `MongoDB` dans `render_article_journey` (`pipeline_proof.py`)
  - statut par snapshot (`gold_articles_<date>`) et stock consolidé (`goldai_merged`),
  - 3 états visuels: présent / non sauvegardé / GridFS hors ligne (avec procédure de relance Docker).

#### Changed

- `scripts/create_ia_copy.py`
  - déduplication explicite avant split (clés prioritaires `fingerprint`, fallback `url`, fallback `content`),
  - filtre des contenus inférieurs à `--min-chars` (défaut 30),
  - split temporel par défaut sur `collected_at` / `processed_at` (en plus de `published_at`, `publication_date`, `date`, `created_at`),
  - nouveaux flags: `--min-chars`, `--no-dedup`.
- `src/streamlit/app.py`
  - réduction de la navigation: 7 onglets -> 4 onglets principaux (`Vue d'ensemble`, `Pipeline & Données`, `IA & Modèles`, `Pilotage & Ops`),
  - regroupement par finalité fonctionnelle via sous-onglets `st.tabs` (aucune suppression de fonctionnalité),
  - mode `Démo` limité à 3 panels (`Pilotage & Ops` masqué; lineage déjà visible en `Vue d'ensemble`),
  - boussole et libellés sidebar synchronisés.
- `src/streamlit/_cockpit_helpers.py` — `mongo_status`, `mongo_get_file_bytes`
  - prise en compte explicite des credentials `.env` (`MONGO_HOST`, `MONGO_PORT`, `MONGO_USER`, `MONGO_PASSWORD`, `MONGO_AUTH_SOURCE`) via construction d'URI dédiée (`_build_mongo_uri_from_env`).
- `src/streamlit/page_modules/pipeline.py`
  - remplacement de la section `Enrichissement étape par étape` (mélange grain jour / cumul) par `Pipeline du jour`:
    4 cartes au même grain (extraits / validés / nouveaux / ajoutés à GoldAI), chart horizontal cohérent,
    statut du run et stock cumulé GoldAI en complément contextuel,
  - tableau multi-périmètres conservé en mode `Expert` uniquement.
- `src/streamlit/page_modules/overview.py`
  - diagnostic explicite quand GridFS est inaccessible: erreur compacte, expander auto-ouvert avec la commande de relance Docker (`docker compose up -d mongodb`), action `Réessayer`.
- `src/streamlit/page_modules/demo.py`
  - script de présentation aligné sur les 3 panels du mode `Démo`,
  - terminologie homogénéisée (`lineage`, `pipeline du jour`, `panels`).

#### Fixed

- `data/goldai/ia/{train,val,test}.parquet`
  - élimination de la fuite `train` / `test` (7.61 % de contenus communs avant patch, 0 % après),
  - élimination des doublons internes intra-split (12.3 % / 7.2 % / 7.8 % avant patch, 0 % après),
  - filtrage des contenus inférieurs à 30 caractères (17.1 % du volume avant patch).

#### Notes

- Volumétrie après patch: `train` 15 856, `val` 1 982, `test` 1 983 (≈ 19 800 lignes effectives sur 87 659 entrées brutes GoldAI). La distribution `neutre / négatif / positif` reste déséquilibrée; compensation via `class_weight="balanced"` et `--target-pos-ratio` dans `scripts/finetune_sentiment.py`.
- Aucune régression fonctionnelle sur le cockpit: les modules d'origine (`pipeline.py`, `flux.py`, `ia.py`, `modeles.py`, `pilotage.py`, `monitoring.py`) restent accessibles via les wrappers et le mode `Expert`.

### E1/Streamlit - quality gates, traçabilité, observabilité (2026-04-20)

#### Added

- `src/e1/pipeline.py`
  - contrat d'exécution `PASS/WARN/FAIL`,
  - quality gates configurables via `.env`:
    - `MIN_LOADED_THRESHOLD`
    - `MIN_CLEAN_RATIO`
    - `MIN_ENRICHED_RATIO`
    - `SOURCE_DROP_WARN_PCT`,
  - collecte des motifs de rejet de nettoyage:
    - `cleaning_rejects`
    - `cleaning_reject_examples`,
  - traçabilité source (volume courant, volume précédent, delta, statut),
  - persistance du résumé d'exécution dans `reports/run_summary_*.json`.

- `src/streamlit/_cockpit_helpers.py`
  - `latest_run_summary_reports()`,
  - `run_summary_history()`.

#### Changed

- `src/e1/core.py`
  - authentification INSEE: support APIM (`X-INSEE-Api-Key-Integration`) ou OAuth selon configuration,
  - endpoints INSEE et liste SIREN externalisés dans `.env`,
  - paramètres de volume de collecte externalisés (`RSS`, `Reddit`, `Trustpilot`, `MonAvis`).

- `src/streamlit/page_modules/pipeline.py`
  - affichage du dernier `run_summary`,
  - historique des exécutions et vue anomalies (`WARN`),
  - clarification de périmètre avec l'onglet `Flux`.

- `src/streamlit/page_modules/flux.py`
  - factorisation de rendu des en-têtes d'étape,
  - bloc `Analyse avancée` replié par défaut pour GoldAI.

- `src/streamlit/page_modules/monitoring.py`
  - regroupement des panneaux techniques dans une section dédiée.

- `src/streamlit/page_modules/ia.py`
  - message API indisponible unifié,
  - bloc d'aide replié après première ouverture de session.

- `src/streamlit/page_modules/demo.py`
  - ajout d'un parcours court,
  - script détaillé replié par défaut.

- `src/streamlit/page_modules/overview.py`
  - harmonisation des libellés de statut d'exécution.

- `src/streamlit/page_modules/pilotage.py`
  - harmonisation des libellés d'actions opératoires.

- `src/streamlit/page_modules/modeles.py`
  - harmonisation des libellés RBAC.

- `src/streamlit/auth_plug.py`
  - normalisation des messages d'authentification (accents, cohérence terminologique).

#### Fixed

- `src/streamlit/_cockpit_helpers.py`
  - correction typage pandas sur `ia_history()`:
    `pd.DataFrame(columns=pd.Index(["date", "lignes_cumulées"]))`.

### Correctif NumPy 2.2 / bottleneck / scipy (2026-03-09)

#### Fixed

- Des commandes Python et l'API échouaient avec *"A module that was compiled using NumPy 1.x cannot be run in NumPy 2.2.6"* (bottleneck, numexpr, scipy).
- Alignement des dépendances dans `requirements.txt` : `numpy>=2.1,<2.2`, `bottleneck>=1.4.0`, `numexpr>=2.8.7`, `scipy>=1.14.0`.

#### Changed

- Ajout d'une procédure de dépannage dans `PLANCHE_LANCEMENT.md`.

### E5 / MCO — E1-metrics, Prometheus, documentation (2026-03-09)

#### Changed

- Service `datasens-e1-metrics` dans Docker Compose pour exposer les métriques E1 en continu sur le port 8000 (Prometheus).

#### Changed

- Configuration Prometheus Docker : scrape `datasens-e1-metrics:8000` et `datasens-e2-api:8001`.
- Configuration locale `prometheus.local.yml` : `localhost:8000` (E1) et `localhost:8001` (API).
- Mise à jour de `docs/e5/PROCEDURE_INSTALLATION_MONITORING.md` et `PLANCHE_LANCEMENT.md` (ordre de démarrage et plan de lancement monitoring).

### E2 - Fine-tuning sentiment_fr, Mistral, filtres topics (2026-03-12)

#### Added

- Filtre topics via `--topics finance,politique` dans `create_ia_copy.py` et `finetune_sentiment.py`, exposé dans Streamlit Pilotage (checkboxes).
- Script `scripts/run_benchmark_et_plots.bat` pour exécuter benchmark et génération des graphiques en une commande.
- Dépendances `datasets` et `accelerate>=0.26.0` ajoutées dans `requirements.txt`.

#### Changed

- Recommandation du backbone `sentiment_fr` (ac0hik, CamemBERT FR) et détection automatique du modèle fine-tuné via `SENTIMENT_FINETUNED_MODEL_PATH` ou chemins standards.
- Prompt système Mistral enrichi avec un paragraphe d'analyse politique et financière généré depuis le dataset.
- Label harmonisé dans `plot_e2_results.py` : "Fine-tuné local (projet)".

#### Fixed

- Correction d'affichage des exemples financiers dans Streamlit selon le thème sélectionné.

### E2/E3 - consolidation API, quality gate et documentation (2026-03-09)

#### Added

- Quality gate E3 exécutable localement et en CI :
  - tests `tests/test_e3_quality_gate.py`,
  - script `scripts/run_e3_quality_gate.py`,
  - workflow `.github/workflows/e3-quality-gate.yml`.
- Structuration documentaire E3 dans `docs/e3/` avec dossier principal et annexes techniques.
- Consolidation documentaire E2 dans `docs/e2/` : index `README.md` et annexes `ANNEXE_6`, `ANNEXE_7`, `ANNEXE_10`, `ANNEXE_11`, `ANNEXE_12`.

#### Changed

- Mise à jour du dossier principal E2 pour référencer les annexes 10 à 12.

#### Fixed

- Fiabilisation API E2 en exécution locale :
  - gestion du cas `raw_articles.csv` vide dans `src/shared/interfaces.py`,
  - fallback `pandas` dans `src/e2/api/routes/analytics.py` pour `/api/v1/analytics/drift-metrics` quand Spark/Java est indisponible.

### E2 - fiabilisation training/benchmark (CPU-first)

#### Added

- Normalisation robuste des labels sentiment dans `scripts/create_ia_copy.py` avant génération des splits `train/val/test` (`négatif`, `neutre`, `positif`) avec gestion des variantes d'encodage.
- Options `--max-train-samples` et `--max-val-samples` dans `scripts/finetune_sentiment.py` pour exécution rapide sur poste contraint.
- Profils `quick` (par défaut) et `--full` dans `scripts/run_training_loop_e2.bat`.

#### Changed

- Renforcement de `scripts/finetune_sentiment.py` : normalisation des labels à l'entrée et configuration `dataloader_pin_memory` adaptée CPU.
- Mise à jour de `scripts/run_training_loop_e2.bat` : installation explicite de `accelerate>=0.26.0` et `scikit-learn`, arrêt strict en cas d'erreur, paramétrage automatique fine-tuning/benchmark selon le profil.
- Documentation `README.md` complétée pour l'exécution E2 rapide et les artefacts générés dans `docs/e2/`.

---

## [1.5.0] — 2026-02-12

### Changed

**RGPD & API** : Registre Art. 30, procédure tri/suppression DP, OWASP Top 10 couvert. Grille E1 OK.

**Veille & IA** : Planning temps dédiés, benchmark CamemBERT/FlauBERT vs cloud, specs IA. MISTRAL_API_KEY dans .env.example. Grille E2 OK.

**Cockpit** : E3 bouclé (réutilise E2).

**E4** : Écarts listés + plan d'action (à appliquer si besoin).

**Ops** : Métriques/seuils/alertes, procédure incidents, Prometheus/Grafana doc, accessibilité (AVH, MS). `rule_files` activés en local. Grille E5 OK.

**CI** : Ruff dégagé, PYTHONPATH fix pour les tests.

---

## [1.4.2] — 2025-02-10

### Added

- ✅ **GoldAI Loader** : `src/ml/inference/goldai_loader.py` — charge `data/goldai/merged_all_dates.parquet`
- ✅ **Sentiment Inference** : `src/ml/inference/sentiment.py` — inférence FlauBERT/CamemBERT sur GoldAI
- ✅ **Endpoint API** : `GET /api/v1/ai/ml/sentiment-goldai?limit=50` — inférence sentiment ML
- ✅ Source : GoldAI uniquement (pas Silver), via `merge_parquet_goldai.py`

---

## [1.4.1] — 2025-02-10

### Fixed

#### Nettoyage des fichiers collectés (null + caractères spéciaux)
- ✅ **sanitize_text()** : Nouvelle fonction dans `src/e1/core.py` pour supprimer les null bytes (`\x00`), caractères de contrôle et caractère de remplacement Unicode (`\ufffd`)
- ✅ **ContentTransformer** : Nettoie désormais `title` ET `content` (avant : content uniquement)
- ✅ **_collect_local_files()** : Sanitization des `title` et `content` issus des fichiers JSON GDELT avant ajout au DataFrame
- ✅ **Lecture JSON** : `encoding='utf-8', errors='replace'` pour éviter les plantages sur encodages invalides
- ✅ Fichiers modifiés : `src/e1/core.py`, `src/e1/aggregator.py`, `src/aggregator.py`

#### Optimisations de nettoyage
- ✅ **BOM** : Suppression du caractère BOM (`\ufeff`) au début des chaînes
- ✅ **Normalisation Unicode (NFC)** : Évite les doublons de représentation (ex. café avec accent combiné)
- ✅ **sanitize_url()** : Nettoyage des URLs (null bytes, caractères de contrôle) avant stockage/export
- ✅ **ContentTransformer** : Sanitize désormais aussi `article.url` dans `transform()`
- ✅ **_collect_local_files()** : URLs sanitizées avant ajout au DataFrame

---

## [1.0.0] — 2025-12-15

### Added

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

### Data Snapshot

- **RAW Zone**: ~5 000 articles bruts
- **SILVER Zone**: ~3 500-4 500 articles nettoyés (quality ≥ 0.5)
- **Partition**: `partition_date` (format DATE)
- **Fingerprint**: SHA256 (déduplication)
- **Quality Range**: 0-1 (0 = faible qualité, 1 = haute qualité)

### Tech Stack

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

### Pipeline Flow

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

## [1.4.0] — 2025-12-20

### Added

#### Fusion Incrémentale Parquet GOLD → GoldAI
- ✅ **Script de fusion incrémentale** : `scripts/merge_parquet_goldai.py`
  - Fusion intelligente des Parquet GOLD quotidiens en GoldAI pour l'IA/Mistral
  - Fusion incrémentale : ajoute uniquement les nouvelles dates
  - Déduplication par `id` (keep='last' basé sur `collected_at`)
  - Partitionnement par date : `data/goldai/date=YYYY-MM-DD/goldai.parquet`
  - Fusion complète : `data/goldai/merged_all_dates.parquet` (pour Mistral)
  - Versioning automatique : backup des versions précédentes
  - Metadata JSON : suivi des dates incluses, nombre de lignes, version
- ✅ **Architecture OOP/SOLID/DRY** : Séparation des responsabilités
  - `GoldAIMetadataManager` : Gestion métadonnées (SRP)
  - `GoldAIDeduplicator` : Déduplication (SRP)
  - `GoldAIDataLoader` : Chargement données (SRP)
  - `GoldAIDataMerger` : Union DataFrames (SRP)
  - `GoldAISaver` : Sauvegarde (SRP)
  - `GoldAIMerger` : Orchestrateur (composition)
- ✅ **Scripts de lancement** : `merge_parquet_goldai.bat` et `.sh` pour Windows/Linux

#### Configuration
- ✅ **Nouveau paramètre** : `goldai_base_path` dans `src/config.py` (défaut: `data/goldai`)
- ✅ **Helper function** : `get_goldai_dir()` pour accès au répertoire GoldAI

### Fixed

#### Ruff Linting
- ✅ **Corrections automatiques** : 58 erreurs corrigées dans `scripts/manage_parquet.py`
  - Imports triés et formatés
  - Whitespace supprimé des lignes vides
  - Type hints modernisés (`Optional[X]` → `X | None`)
  - f-strings corrigés
  - Code conforme aux standards ruff

### Metrics

- **Fichiers créés** : 3 fichiers (script Python + 2 scripts batch/shell)
- **Lignes ajoutées** : ~240 lignes de code (architecture OOP/SOLID/DRY)
- **Corrections ruff** : 58 erreurs corrigées

### Changed

#### Nouveaux Fichiers
- `scripts/merge_parquet_goldai.py` : Script de fusion incrémentale GoldAI
- `scripts/merge_parquet_goldai.bat` : Lanceur Windows
- `scripts/merge_parquet_goldai.sh` : Lanceur Linux/Mac

#### Fichiers Modifiés
- `src/config.py` : Ajout `goldai_base_path` et `get_goldai_dir()`
- `scripts/manage_parquet.py` : Corrections ruff (58 erreurs)

---

## [1.3.0] — 2025-12-20

### Added

#### Architecture PySpark Big Data
- ✅ **SparkSession Singleton** : Gestion centralisée avec mode local pur (pas de connexion réseau)
- ✅ **Interfaces Abstraites** : `DataReader` et `DataProcessor` (DIP - Dependency Inversion Principle)
- ✅ **GoldParquetReader** : Lecteur Parquet GOLD depuis E1 (isolation E1 respectée)
- ✅ **GoldDataProcessor** : Processeur Big Data pour agrégations et analyses
- ✅ **Configuration Spark** : Mode local strict, pas de connexions réseau (résout WinError 10061)

#### Intégration E2 API
- ✅ **Endpoints Analytics** : 4 nouveaux endpoints FastAPI pour analytics PySpark
  - `/api/v1/analytics/sentiment/distribution` : Distribution des sentiments avec pourcentages
  - `/api/v1/analytics/source/aggregation` : Agrégation par source
  - `/api/v1/analytics/statistics` : Statistiques générales
  - `/api/v1/analytics/available-dates` : Liste des dates disponibles
- ✅ **Protection RBAC** : Tous les endpoints protégés par `require_reader` permission
- ✅ **Gestion d'erreurs** : Gestion robuste des erreurs (FileNotFoundError, ConnectionRefusedError)

#### Tests PySpark
- ✅ **Suite de tests complète** : `tests/test_spark_integration.py` (13 tests)
  - Tests SparkSession (singleton)
  - Tests GoldParquetReader (lecture, dates disponibles, plages de dates)
  - Tests GoldDataProcessor (agrégations, statistiques)
  - Tests d'intégration (pipeline complet, isolation E1)
- ✅ **Gestion erreurs réseau** : Tests skip automatiquement en cas de problèmes réseau Windows
- ✅ **Scripts de test** : `scripts/test_spark_simple.py` pour tests rapides locaux

#### Outils PySpark
- ✅ **Shell interactif** : `scripts/pyspark_shell.py` avec IPython/Code interactif
- ✅ **Scripts de démarrage** : `scripts/start_pyspark_shell.bat` et `.sh` pour Windows/Linux
- ✅ **Gestion schémas** : Support `unionByName` avec `allowMissingColumns=True` pour schémas évolutifs

#### Corrections Techniques
- ✅ **Ruff linting** : 197 erreurs corrigées automatiquement (imports, formatage, types)
- ✅ **Imports relatifs** : Correction de tous les imports dans `src/spark/` pour compatibilité
- ✅ **Configuration Spark** : Ajout de nombreuses options pour forcer mode local pur
- ✅ **Gestion partitions** : Lecture explicite partition par partition (évite problèmes wildcard Windows)
- ✅ **Gitignore** : Ajout de `spark-temp/` pour exclure fichiers temporaires Spark

#### Documentation
- ✅ **README_E2_API.md** : Documentation complète des endpoints analytics
- ✅ **PHASE2_COMPLETE.md** : Récapitulatif Phase 2 E2 (100% complète)
- ✅ **ARCHITECTURE_METIER_ANALYSIS.md** : Analyse architecture métier 5 étapes

### Metrics

- **Fichiers créés** : 10 fichiers PySpark
- **Lignes ajoutées** : ~1,500 lignes de code
- **Tests créés** : 13 tests PySpark (100% passing)
- **Endpoints API** : 4 nouveaux endpoints analytics
- **Parquet files** : 4 fichiers Parquet GOLD (87,907 lignes totales)

### Changed

#### Nouveaux Fichiers
- `src/spark/session.py` : SparkSession singleton
- `src/spark/interfaces/data_reader.py` : Interface DataReader
- `src/spark/interfaces/data_processor.py` : Interface DataProcessor
- `src/spark/adapters/gold_parquet_reader.py` : Lecteur Parquet GOLD
- `src/spark/processors/gold_processor.py` : Processeur Big Data
- `src/e2/api/routes/analytics.py` : Endpoints analytics FastAPI
- `tests/test_spark_integration.py` : Suite de tests PySpark
- `scripts/pyspark_shell.py` : Shell interactif PySpark
- `scripts/test_spark_simple.py` : Tests rapides locaux

#### Fichiers Modifiés
- `src/e2/api/main.py` : Ajout router analytics
- `src/e2/api/routes/__init__.py` : Export analytics_router
- `.gitignore` : Ajout spark-temp/
- `requirements.txt` : pyspark==3.5.1

### Status

**PySpark est maintenant intégré et opérationnel** pour le traitement Big Data.

**Prochaines étapes** :
- Phase 4 : ML Fine-tuning (FlauBERT, CamemBERT)
- Phase 5 : Streamlit Dashboard
- Phase 6 : Mistral IA Integration

---

## [1.2.0] — 2025-12-20

### Added

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

### Metrics

- **Fichiers créés** : 19 fichiers
- **Lignes ajoutées** : 2,661 insertions
- **Lignes supprimées** : 396 suppressions
- **Tests créés** : 11 tests (10 rapides + 1 complet)
- **Documentation** : 5 documents créés/mis à jour

### Changed

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

### Isolation Rules

#### Autorisé
- Utiliser `E1DataReader` depuis E2/E3
- Lire depuis `exports/` ou `data/` (lecture seule)
- Utiliser DB en lecture seule
- Importer uniquement interfaces publiques (`src/shared/`)

#### Interdit
- Modifier `src/e1/` depuis E2/E3
- Importer classes internes E1 depuis E2/E3
- Écrire dans fichiers E1 depuis E2/E3
- Modifier schéma DB E1 depuis E2/E3

### Status

**E1 est maintenant complètement isolé et protégé** pour la construction de E2/E3.

**Prochaines étapes** :
- Phase 1 : Docker & CI/CD
- Phase 2 : FastAPI + RBAC
- Phase 3 : PySpark

---

## [1.1.0] — 2025-12-19

### Changed

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

### Data Snapshot

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

### Changed (Technical)

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

### Fixed

- ✅ Erreur UnicodeEncodeError sur Windows (emojis)
- ✅ Duplication Kaggle dans exports (exclusion de `_collect_local_files()`)
- ✅ Affichage erreurs UNIQUE constraint (déduplication silencieuse)
- ✅ Génération fichier `gold_zzdb.csv` indésirable (supprimé)
- ✅ Topics manquants (garantie 2 topics par article)

---

## [Status]

**E1 inclut tout ce qui est nécessaire pour** :
- ✅ Collecter 10 sources (~5K articles)
- ✅ Nettoyer et qualifier les données
- ✅ Générer dashboards professionnels
- ✅ Tracer toutes les transformations (logging)
- ✅ Valider intégrité (CRUD tests)

**E1 est production-ready. Lancer `python quick_start.py` maintenant.**

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
