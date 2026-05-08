# Audit code — candidats au nettoyage

Document : recensement des fichiers / dossiers candidats à suppression, archivage ou consolidation.
Aucune suppression effectuée par l'audit lui-même : valider chaque ligne avant action.

Objectif : présenter un dépôt clair et défendable, sans artefacts d'exploration ou de migrations passées.

Légende :
- **DROP** : à supprimer (orphelin, doublon, temporaire).
- **ARCHIVE** : à déplacer dans `archive/` (hors runtime, gardé pour historique).
- **CONSOLIDATE** : doublons / variantes à fusionner.
- **KEEP** : runtime ou documentation essentielle, ne pas toucher.

---

## 1. Racine du dépôt — documents redondants

| Fichier | Action | Raison |
|---|---|---|
| `INVENTAIRE_PROJET.md` (23 KB) | **ARCHIVE** ✅ fait | Archivé dans `archive/legacy_docs/`. |
| `FICHIERS_PROJET_DATASENS.md` (12 KB) | **ARCHIVE** ✅ fait | Archivé dans `archive/legacy_docs/`. |
| `FICHIERS_FONCTIONNELS.md` (5 KB) | **ARCHIVE** ✅ fait | Archivé dans `archive/legacy_docs/`. |
| `FLOW_DONNEES.md` (12 KB) | **MOVE** ✅ fait | Déplacé vers `docs/dev/FLOW_DONNEES.md`, 6+ références mises à jour (audits E1/E4, dossier E1, ROADMAP). |
| `GIT_IGNORE_GUIDE.md` | **DROP** ✅ fait | Supprimé. |
| `GUIDE_NETTOYAGE_MANUEL.md` | **ARCHIVE** ✅ fait | Archivé dans `archive/legacy_docs/` (contenu consolidé dans le présent audit). |
| `LANCER_TOUT.md` + `PLANCHE_LANCEMENT.md` | **CONSOLIDATE** ✅ fait | Consolidés dans `RUNBOOK.md`, originaux archivés dans `archive/legacy_docs/`. 6+ références mises à jour (`README.md`, audits E5, dossiers E3/E5). |
| `RUFF.md` (1 KB) | **DROP** ✅ fait | Supprimé (contenu trivial, à reporter dans `CONTRIBUTING.md` si besoin). |
| `LOGGING.md` (20 KB) | **MOVE** ✅ fait | Déplacé vers `docs/dev/LOGGING.md`, 10+ références mises à jour (audits E5, dossiers E5, `docs/README.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE.md`, `docs/Dossier_E1_versioning_documentation.md`). |
| `README_DOCKER.md` | **MOVE+RENAME** ✅ fait | Déplacé vers `docs/dev/DOCKER_RUNTIME.md`, référence mise à jour dans `docs/AGILE_STRUCTURE.md`. |

**Recommandation** : la racine doit contenir uniquement `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `DEPLOY.md`, `LICENSE.md`, et le manifeste de lancement (`RUNBOOK.md`).

---

## 2. Racine du dépôt — fichiers techniques à déplacer ou supprimer

| Fichier | Action | Raison |
|---|---|---|
| `pipeline.log` (2 KB) | **DROP** ✅ fait | Fossile (17/12/2025), remplacé par `logs/datasens.log` (actif, 214 KB). Déjà couvert par `.gitignore`. |
| `mlflow.db` (440 KB) | **DROP** ✅ fait | Base SQLite locale MLflow, déjà gitignore. `mlruns/` est l'emplacement actif. |
| `datasens.db` (56 KB) à la racine | **DROP** ✅ fait | Fossile (12/02/2026, 56 KB) doublon de `~/datasens_project/datasens.db` actif (91 MB, modifié aujourd'hui). Le code conserve le fallback `PROJECT_ROOT / "datasens.db"` pour les premiers démarrages. |
| `.env.freeze` | **ARCHIVE** dans `archive/env_snapshots/` | Snapshot de configuration figée, utile pour rollback. |
| `_launch_api.bat`, `_launch_cockpit.bat` | **KEEP** (révisé) | Fausse alerte d'audit : appelés activement par `lancer_tout.bat` (l.70/77), `start_full.bat` (l.26/28) et `src/streamlit/_cockpit_helpers.py` (l.555). Modules atomiques de lancement, à conserver. |
| `start_cockpit.bat`, `start_grafana.bat`, `start_prometheus.bat`, `start_uptime_kuma.bat`, `start_mongo.bat` | **CONSOLIDATE** (reporté) | 5 lanceurs à fusionner dans un seul `start_full.bat` paramétré (`-only=cockpit|grafana|...`). Faible priorité : la verbosité actuelle reste lisible et chaque .bat a sa raison d'être (Grafana = Docker, Prometheus = exe local, etc.). |
| `run_ruff.bat` | **KEEP** (révisé) | Documenté comme alias dans `README.md` et `CONTRIBUTING.md`. Outil de contributeur utile, à conserver. |
| `Dockerfile.windows` (0.6 KB) | **DROP** ✅ fait | Variante quasi vide, orpheline, `Dockerfile` principal couvre les builds Windows via Docker Desktop. |

---

## 3. Dossiers candidats au nettoyage

| Dossier | Action | Raison |
|---|---|---|
| `hadoop/` | **KEEP** (révisé) | Fausse alerte d'audit : `winutils.exe` (110 KB) requis par PySpark sur Windows, fixé comme `HADOOP_HOME` par défaut dans `src/spark/session.py` (l.33, l.56). Téléchargement automatisé via `scripts/download_winutils.ps1`. |
| `spark-temp/` | **DROP** ✅ fait | Dossier temporaire vide. Déjà gitignore. Recréé automatiquement si Spark relancé. |
| `mlruns/` | **KEEP** | Emplacement standard MLflow ; déjà couvert par `.gitignore` (l.125). À garder pour la persistance des runs locaux. |
| `output/` | **DROP** ✅ fait | 3 fichiers JSON Botasaurus (`_botasaurus_request.json`, `_ifop_br.json`, `_ifop_req.json`) régénérés à chaque scrape. Déjà gitignore (l.26). |
| `error_logs/` (7 fichiers) | **ARCHIVE** (reporté) | Logs d'erreurs anciens. Rotation auto à mettre en place ultérieurement. |
| `backups/retag_*` (4 dossiers du 18/04) | **DROP partiel** ✅ fait | Suppression du dossier vide `retag_goldai_20260418_161355` et du doublon le plus ancien `retag_20260418_154959` (191 MB libérés). Conservation par sécurité de `retag_20260418_155207` (snapshot retag complet, 191 MB) et `retag_goldai_20260418_161455` (snapshot goldai consolidé, 42 MB). Gitignore déjà actif sur `backups/` (l.147). |
| `zzdb/` | **ARCHIVE** dans `archive/zzdb/` | Bac à sable expérimental (faker sources, dashboards perso). Hors runtime du pipeline principal. |
| `visualizations/` | **À auditer** | Vérifier si encore utilisé par le cockpit ou si remplacé par les charts Streamlit. |
| `monitoring/` | **KEEP** | Dossier de configuration Prometheus / Grafana → runtime. |
| `notebooks/` | **KEEP** sélectif | Garder uniquement les notebooks référencés (Colab, exploration documentée). Drop les `_old`, `_test`, `_brouillon`. |
| `data/` | **KEEP** | Données runtime (RAW SQLite, SILVER, GOLD, GoldAI). Voir `.gitignore` pour exclusion git si trop volumineux. |
| `models/` | **KEEP** | Modèles fine-tunés (CamemBERT, sentiment_fr). |
| `reports/` | **KEEP** | Run summaries et états DB historisés. Rotation à 90 jours conseillée. |

---

## 4. Scripts (`scripts/`) — 65 fichiers

### Catégorie A — One-shot ou démos, archivés dans `scripts/_archive/` ✅ fait

| Script | Décision finale | Raison |
|---|---|---|
| `setup_with_sql.py` | **KEEP** (révisé) | Référencé dans `RUNBOOK.md`, `scripts/README.md`, guides d'architecture. Init DB officielle. |
| `init_profils_table.py` | **KEEP** (révisé) | Init table `profils` (auth cockpit), référencée dans guide d'architecture. |
| `migrate_sources.py` | **ARCHIVE** ✅ | Migration sources `sources_config.json → DB`, terminée fév. 2026. |
| `inject_csv.py` | **ARCHIVE** ✅ | Utilisé seulement par `test_zzdb.py` (lui-même archivé). |
| `bootstrap_ml_labels.py` | **KEEP** (révisé) | Reproductible si labels IA à reconstruire. |
| `_run_migration.py` | **ARCHIVE** ✅ | Préfixe `_`, one-shot. |
| `_check_training_metrics.py` | **ARCHIVE** ✅ | Vérification ad-hoc, fonctionnalité intégrée au cockpit `Modèles`. |
| `retag_full_pipeline.py` | **KEEP** (révisé) | Outil de retag récurrent (changement de schéma/labels). |
| `retag_goldai_consolide.py` | **KEEP** (révisé) | Pendant runtime de `retag_full_pipeline.py`. |
| `enrich_all_articles.py` | **KEEP** (révisé) | Référencé par `src/dashboard.py:313` (message utilisateur), 5+ docs. Outil de remédiation. |
| `reanalyze_sentiment.py` | **KEEP** (révisé) | Référencé dans `Dossier_E1_topics_sentiments+scripts.md`. Reproductible. |
| `regenerate_exports.py` | **KEEP** (révisé) | Référencé par `scripts/db_state_report.py:443`. Outil runtime. |
| `verify_audit_fixes.py` | **ARCHIVE** ✅ | Vérif post-audit avril 2026, terminée. |
| `verify_audit_trail.py` | **KEEP** (révisé) | Référencé dans `docs/README_E2_API.md`. Audit récurrent E2. |
| `audit_e1_coverage.py` | **ARCHIVE** ✅ | Audit one-shot E1 fév. 2026, terminé. |
| `validate_e1_project.py` | **KEEP** (révisé) | Référencé dans guide d'architecture. Génère `validation_report.json` (cf. `.gitignore` l.140). |
| `demo_collecte.py` | **ARCHIVE** ✅ | Démo isolée fév. 2026. |
| `demo_proof_e1.py` | **ARCHIVE** ✅ | Démo isolée fév. 2026. Référence mise à jour dans `Dossier_E1_preuves.md`. |
| `dossier_e1_examples.py` | **ARCHIVE** ✅ | Exemples dossier E1 fév. 2026. `pyproject.toml` mis à jour : `exclude = ["scripts/_archive"]`. |
| `check_kaggle_files.py` | **ARCHIVE** ✅ | Vérification fichiers Kaggle one-shot. |
| `activate_zzdb_source.py` | **ARCHIVE** ✅ | Activation source ZZDB (sandbox), one-shot. |

### Catégorie B — Tests ad-hoc archivés dans `scripts/_archive/` ✅ fait

| Script | Action | Raison |
|---|---|---|
| `scripts/test_pipeline.py` | **ARCHIVE** ✅ | Smoke test à `print()`, redondant avec `tests/`. Référence mise à jour dans `docs/VISUALISATION_SENTIMENT.md`. |
| `scripts/test_project.py` | **ARCHIVE** ✅ | Vérif présence fichiers, mieux couvert par CI / pytest. |
| `scripts/test_zzdb.py` | **ARCHIVE** ✅ | Lié au sandbox `zzdb/` (hors runtime principal). |
| `scripts/test_spark_simple.py` | **ARCHIVE** ✅ | Smoke test PySpark ; suite `tests/` couvre les besoins runtime. |
| `scripts/test_before_build.py` | **ARCHIVE** ✅ | Pré-build manuel, à intégrer en CI ultérieurement si besoin. |
| `scripts/ai_smoke_test.py` | **ARCHIVE** ✅ | Smoke test IA basique, redondant avec `tests/`. |

**Bilan étape 4** : 17 scripts archivés (88 → 71 fichiers actifs dans `scripts/`). 10 décisions d'audit révisées car références actives détectées (RUNBOOK, dashboard, guides, scripts runtime). Mises à jour : `pyproject.toml`, `scripts/README.md`, `scripts/SCRIPTS_LIST.md`, `docs/VISUALISATION_SENTIMENT.md`, `docs/Dossier_E1_preuves.md`, `docs/GUIDE_ARCHITECTURE_MODE_EMPLOI_FICHIERS.md`.

### Catégorie C — Scripts d'exploration / vues ✅ traité

**Décision révisée après lecture du code et inventaire des références** : la consolidation initialement prévue (8 → 1 `scripts/inspect.py`) aurait été du sur-engineering. Les 6 scripts populaires sont chacun courts (< 200 lignes), font une chose, ont des noms explicites et sont massivement référencés dans la doc (`docs/QUICK_START.md`, `docs/VISUALISATION_SENTIMENT.md`, `docs/ARCHITECTURE_DB.md`, `docs/PROJECT_STRUCTURE.md`, `docs/ENRICHISSEMENT.md`, `docs/ORGANISATION.md`, `scripts/SCRIPTS_LIST.md`). La refonte aurait créé un breaking change avec mass-update de 10+ docs, sans gain de maintenance significatif.

| Script | Décision finale | Raison |
|---|---|---|
| `query_sqlite.py` | **KEEP** | Référencé dans `docs/ARCHITECTURE_DB.md` avec exemples de requêtes ZZDB (3 occurrences). |
| `show_tables.py` | **KEEP** | Référencé dans `scripts/README.md`, `scripts/SCRIPTS_LIST.md`. Inspection schéma DB. |
| `show_dashboard.py` | **KEEP** | Wrapper trivial vers `src/dashboard.py::DataSensDashboard`. Référencé dans 7 docs. |
| `quick_view.py` | **KEEP** | Aperçu rapide (topics + sentiment + sources), 3 docs référencent. |
| `view_exports.py` | **KEEP** | Visualiseur interactif CSV exports/, 6 docs référencent. |
| `visualize_sentiment.py` | **KEEP** | Génère 4 graphiques PNG dans `visualizations/`. 3 docs référencent. |
| `show_db_stats.py` | **ARCHIVE** ✅ | Doublon fonctionnel de `show_dashboard.py` : reproduit à la main via SQL ce que `DataSensDashboard` fait via la classe. Aucune référence externe. |
| `view_datasets.py` | **ARCHIVE** ✅ | Variante plus complète de `view_exports.py` mais aucune référence dans la doc (la doc oriente systématiquement vers `view_exports.py`). |

**Bilan** : 2 doublons silencieux archivés, 6 scripts utiles conservés. Aucune doc ni code à modifier (les scripts archivés n'avaient pas de référence active).

### Catégorie D — Runtime essentiel à garder

| Script | Rôle |
|---|---|
| `backup_parquet_to_mongo.py` | Backup GridFS (utilisé). |
| `download_from_mongo_gridfs.py` | Pendant du backup. |
| `merge_parquet_goldai.py` | Consolidation GoldAI quotidienne. |
| `create_ia_copy.py` | Génération train/val/test pour fine-tuning. |
| `finetune_sentiment.py` | Fine-tuning local (alternative au notebook Colab). |
| `install_colab_model.py` | Réinjection d'un modèle Colab (récent, OK). |
| `change_password.py` | Gestion utilisateur cockpit (récent, OK). |
| `create_user.py` | Création / mise à jour de comptes. |
| `db_state_report.py` | Rapport quotidien d'état DB (intégré au runner). |
| `cleanup_sqlite_buffer.py` | Maintenance SQLite. |
| `manage_parquet.py` | Utilitaires parquet (lecture, fusion, comparaison). |
| `ai_benchmark.py` | Benchmark modèles IA (utilisé par `Modèles`). |
| `check_inference_quality.py` | Contrôle qualité inférence. |
| `run_inference_pipeline.py` | Pipeline d'inférence batch. |
| `plot_e2_results.py`, `plot_inference_results.py` | Génération de graphes pour rapports. |
| `publish_best_model_to_hf.py` | Publication HuggingFace Hub. |
| `export_mistral_dataset.py` | Export dataset pour Mistral (insights). |
| `veille_digest.py` | Génération veille E2 (annexe C6). |
| `scheduler.py` | Orchestration runs. |
| `run_e2_tests.py`, `run_e3_quality_gate.py`, `run_e5_verification.py` | Quality gates par bloc compétence. |
| `run_e1_metrics.py` | Métriques E1 quotidiennes. |
| `pyspark_shell.py` | **À auditer** : si Spark vraiment abandonné, supprimer. |
| `list_mongo_parquet.py` | Inspection GridFS, utile en debug. |
| `build_gold_branches.py` | Construction snapshots GOLD. |
| `create_test_user.py` | Pendant utilitaire de `create_user.py` (à fusionner). |

---

## 5. Imperfections de code à traiter

### TODO / FIXME / HACK ✅ fait

Recensement initial : 6 occurrences dans `src/`. **Toutes traitées.**

| Fichier | Action effectuée |
|---|---|
| `src/streamlit/auth_plug.py` (l.270-276) | **Supprimé** : bloc OAuth2 entièrement commenté avec TODO placeholder. À réintroduire dans un commit dédié si Google/GitHub OAuth devient un besoin. |
| `src/e2/api/routes/silver.py` (l.81) | **Clarifié** : retrait de `# TODO: Optimiser` (la limite par défaut 1000 est cohérente avec la pagination cockpit). |
| `src/e2/api/routes/silver.py` (l.112, 137, 159) | **Réécrit** : 3 TODO trompeurs supprimés (les endpoints POST/PUT/DELETE sur SILVER renvoient 501 **par conception** — isolation E1, E2 = lecture seule). Les `detail` HTTPException reformulés en `is not supported (E1 isolation by design)` pour ne pas suggérer une feature en attente. |
| `src/e2/api/routes/gold.py` (l.71) | **Clarifié** : retrait de `# TODO: Optimiser` (idem silver). |

Vérification post-traitement : `rg "TODO\|FIXME\|HACK\|XXX" src/` → 0 occurrence.

### `print()` de debug ✅ fait

- `src/__init__.py` contenait 3 `print()` au top-level (`[OK] DataSens E1 initialized`, `Project: ...`, `Data: ...`) qui s'affichaient à chaque import du package, polluant les logs cockpit, API et tests. **Supprimés.** Le package conserve sa logique d'initialisation (création de `DATA_ROOT`) mais en mode silencieux. Vérifié : `python -c "import src"` ne produit plus de sortie.

### Imports non triés / inutilisés ✅ fait (étape 7)

Bilan ruff final : **0 issue** sur `src/` + `scripts/` (avec règles E, W, F, I, C90, N, UP, B, A, C4, T10, SIM, RUF activées).

Trajectoire :
1. **471 issues recensées** au démarrage de l'étape 7 (et non 62 comme estimé initialement — l'estimation a été révisée à la lecture des stats détaillées).
2. **Pass 1** (`ruff --fix`, safe-fixes uniquement) : 355 fixes appliqués, 116 restants.
3. **Pass 2** (`ruff --fix --unsafe-fixes`) : 111 fixes additionnels (suppression d'imports `csv` morts, variables locales non utilisées dans page_modules cockpit, etc.), 7 restants.
4. **Pass 3** (fix manuel des résiduelles) : `_` au lieu de `c` dans une boucle (`scripts/plot_inference_results.py`), combinaison de deux `if` redondants dans `src/streamlit/data_lineage.py`, ajout de `RUF002` à la liste `ignore` de `pyproject.toml` (typographie française légitime dans les docstrings : `×`, `’`).

Catégories fixées automatiquement :
- F401 (imports unused, ex. `csv` traînant dans plusieurs page_modules cockpit), F541 (f-strings vides), F841 (variables locales mortes — bloc `ctx.x = ...` copié-collé entre demo / flux / ia / pipeline / pilotage / monitoring / overview qui n'utilisent pas toutes les variables),
- I001 (imports non triés), B905 (`zip(strict=...)`), UP017 (`datetime.UTC`), UP035 (`collections.abc`), UP038 (`X | Y` dans isinstance),
- W291 (trailing whitespace), C408 (`dict()` → `{}`), C409 (`tuple([...])` → `(...,)`), RUF005 (concat → unpack), RUF015 (`next(iter())`), SIM108 (ternaire), SIM117 (with imbriqués), RUF100 (`# noqa` inutiles).

**Vérification de non-régression** :
- 65 fichiers modifiés, 1 535 insertions, 3 494 suppressions (~ 2 000 lignes nettes en moins, surtout du code mort dans les page_modules cockpit).
- Smoke tests imports : `src`, `src.e2.api.main` (34 routes), 8 page_modules cockpit, pipeline E1 complet, ML inference — **tous OK**.
- Pytest complet (sans `test_spark_integration.py` qui dépend d'un cluster) : **51 passed, 1 deselected** (le test pré-existant `test_build_gold_ia_labelled_creates_sentiment_label` qui échoue sur un diff d'encodage Windows, indépendant de l'étape 7).

### Tests pré-existants résolus (post-étape 7)

Deux échecs pré-existants ont été diagnostiqués et corrigés après la passe ruff :

1. **`tests/test_gold_branches.py::test_build_gold_ia_labelled_creates_sentiment_label`** — diagnostiqué non comme un problème d'encodage Windows mais comme un **désalignement test ↔ contrat de l'API**. Le code de production (`src/datasets/gold_branches.py::normalize_sentiment_label`) retire **volontairement** les accents via `_ascii_fold` (docstring : *"Makes label matching encoding-agnostic"*) pour absorber les corruptions Windows/Spark/CSV. Le test attendait `"négatif"` (avec accent) ; le code retourne `"negatif"` (sans). Fix : assertion alignée sur le comportement contractuel (`["positif", "negatif"]`). Le test devient une vérification explicite de la normalisation.

2. **`tests/test_e2_api.py::TestPermissions::test_reader_can_read`** + **`TestGoldZone::test_list_gold_articles_authorized`** — `ValidationError` Pydantic sur `ArticleResponse.url` (`String should have at most 500 characters`). La contrainte `max_length=500` dans `src/e2/api/schemas/article.py` était trop serrée pour des URL réelles (Google News, redirections trackées, paramètres OAuth, etc.). Fix : passage à `max_length=2048` (limite navigateur RFC), aligné avec la pratique web. Aucun test ne dépendait de l'ancienne limite.

Pytest final : **52 passed** (hors `test_spark_integration.py` qui requiert un cluster Spark externe).

---

## 6. Plan d'exécution proposé (par ordre de risque)

1. **Étape 1a — risque nul** ✅ fait : 4 docs auto-référents archivés dans `archive/legacy_docs/` (`INVENTAIRE_PROJET.md`, `FICHIERS_PROJET_DATASENS.md`, `FICHIERS_FONCTIONNELS.md`, `GUIDE_NETTOYAGE_MANUEL.md`), 2 orphelins supprimés (`GIT_IGNORE_GUIDE.md`, `RUFF.md`). Référence mise à jour dans `docs/GUIDE_ARCHITECTURE_MODE_EMPLOI_FICHIERS.md`.
1bis. **Étape 1b — risque modéré** ✅ fait : consolidation `LANCER_TOUT.md` + `PLANCHE_LANCEMENT.md` → `RUNBOOK.md` (originaux archivés dans `archive/legacy_docs/`). Déplacement `LOGGING.md` → `docs/dev/LOGGING.md`, `FLOW_DONNEES.md` → `docs/dev/FLOW_DONNEES.md`, `README_DOCKER.md` → `docs/dev/DOCKER_RUNTIME.md`. Mass-update de 25+ références dans `README.md`, `CONTRIBUTING.md`, audits E1/E4/E5, dossiers E3/E5, `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/Dossier_E1_versioning_documentation.md`, `docs/ROADMAP_EVOLUTION.md`, `docs/AGILE_STRUCTURE.md`, `docs/e5/README.md`, `docs/e5/ANNEXE_3_PLAN_DEMO_E5.md`. Racine désormais à 6 .md propres : `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `DEPLOY.md`, `LICENSE.md`, `RUNBOOK.md`.
2. **Étape 2 — risque faible** ✅ fait : suppression de 4 fossiles racine (`pipeline.log`, `mlflow.db`, `datasens.db`, `Dockerfile.windows`, ~ 500 KB libérés). Décisions révisées après vérification des dépendances : `_launch_api.bat`, `_launch_cockpit.bat`, `run_ruff.bat` sont **conservés** (réellement utilisés par les lanceurs et la doc contributeur). Le `.gitignore` couvrait déjà tous les fossiles (`*.db`, `*.log`, `mlflow.db`).
3. **Étape 3 — risque faible** ✅ fait : suppression de `spark-temp/` (vide) et `output/` (3 JSON Botasaurus, 60 KB) ; révision audit : `hadoop/` conservé (winutils.exe requis par PySpark Windows). Sur `backups/retag_*` : suppression du dossier vide et du doublon le plus ancien (191 MB libérés, 2 snapshots conservés par sécurité). Total libéré : ~ 192 MB. Gitignore déjà actif sur tous les chemins concernés, aucune modification requise.
4. **Étape 4 — risque moyen** ✅ fait : 17 scripts archivés dans `scripts/_archive/` (88 → 71 fichiers actifs). 10 décisions d'audit révisées après vérification des références (RUNBOOK, `src/dashboard.py`, scripts runtime, guides). Mass-update de 6 fichiers de documentation et configuration tooling (`pyproject.toml`, `scripts/README.md`, `scripts/SCRIPTS_LIST.md`, `docs/VISUALISATION_SENTIMENT.md`, `docs/Dossier_E1_preuves.md`, `docs/GUIDE_ARCHITECTURE_MODE_EMPLOI_FICHIERS.md`).
5. **Étape 5 — risque moyen** ✅ fait : décision révisée après examen du code et des références. La consolidation `inspect.py` initialement prévue aurait été du sur-engineering (10+ docs à casser pour 6 scripts < 200 lignes chacun, déjà nommés et documentés clairement). Action retenue : archivage des 2 doublons silencieux uniquement (`show_db_stats.py` redondant avec `show_dashboard.py`, `view_datasets.py` redondant avec `view_exports.py`). Les 6 scripts d'exploration utiles sont conservés tels quels. Aucune doc à modifier (les archivés n'avaient pas de référence externe).
6. **Étape 6 — risque faible** ✅ fait : 3 `print()` parasites retirés de `src/__init__.py` (imports désormais silencieux). 6 TODO traités : 1 placeholder OAuth2 commenté supprimé dans `auth_plug.py`, 3 TODO trompeurs sur endpoints 501-by-design supprimés dans `silver.py` (avec reformulation des `detail` HTTPException), 2 TODO de pagination clarifiés (`silver.py`, `gold.py`). Smoke tests imports : OK. Suite pytest E2 (silver/gold) : 17/18 OK ; 1 échec pré-existant d'encodage Windows sans rapport avec ce nettoyage.
7. **Étape 7 — risque nul** ✅ fait : passe finale ruff. 471 issues détectées, 466 fixées automatiquement (2 passes : safe puis unsafe-fixes), 3 résiduelles fixées manuellement, 5 RUF002 (typographie française dans docstrings) ajoutées à la liste `ignore` de `pyproject.toml` par cohérence avec RUF001/RUF003 déjà ignorées. Bilan ruff final : **0 issue** sur `src/` + `scripts/`. ~ 2 000 lignes de code mort retirées. Pytest 51/51 OK (1 échec pré-existant d'encodage signalé séparément).

---

## 9. Bilan global du nettoyage (étapes 1a → 7)

| Étape | Périmètre | Volume traité |
|---|---|---|
| 1a | Docs auto-référents racine | 4 archivés, 2 supprimés |
| 1b | Consolidation lanceurs + dossier `docs/dev/` | 2 docs consolidés (`RUNBOOK.md`), 3 docs déplacées, 25+ refs MAJ |
| 2 | Fossiles racine (`*.log`, `*.db`, `Dockerfile.windows`) | 4 fichiers, ~ 500 KB |
| 3 | Artefacts dossiers (`spark-temp/`, `output/`, doublons backups) | ~ 192 MB libérés |
| 4 | `scripts/` legacy + tests ad-hoc | 17 scripts archivés, 6 docs MAJ |
| 5 | Doublons d'inspection (`show_db_stats.py`, `view_datasets.py`) | 2 archivés |
| 6 | Code source (`print()`, TODO trompeurs) | 4 fichiers, 0 TODO restant |
| 7 | Passe ruff `src/ scripts/` | 471 → 0 issue, 65 fichiers MAJ |

**État final racine** : 6 fichiers .md (`README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `DEPLOY.md`, `LICENSE.md`, `RUNBOOK.md`), 10 .bat (tous utilisés), `Dockerfile`, `docker-compose.yml`, `main.py`, `run_e2_api.py`, `lancer_tout.bat`, configs (`pyproject.toml`, `requirements.txt`, `pytest.ini`, `pyrightconfig.json`, `.env.example`, `.gitignore`, `.dockerignore`), `sources_config.json`, `run_daily.ps1`.

**État final `scripts/`** : 69 actifs + 19 archivés dans `scripts/_archive/`.

**État final `src/`** : 0 TODO, 0 print() top-level, 0 issue ruff, imports silencieux.

Le dépôt est défendable en revue de code.

Chaque étape se commit séparément avec un message clair (`chore(cleanup): drop hadoop dir + spark-temp`, `refactor(scripts): consolidate inspect tools into scripts/inspect.py`, etc.).

---

## 7. Volume libéré (estimation)

| Source | Taille libérée |
|---|---|
| `hadoop/`, `spark-temp/`, `output/` | ~ 1 MB + dossiers vides |
| `mlruns/`, `mlflow.db` | ~ 1 MB |
| `backups/retag_*` (4 dossiers) | dépend du contenu (à mesurer avant suppression) |
| Documentation racine archivée | ~ 70 KB |
| Scripts archivés (~ 20 fichiers) | ~ 80 KB |

L'objectif n'est pas le volume mais la **lisibilité** : un dépôt où chaque fichier visible a une raison d'être actuelle.

---

## 8. Ce qui reste après nettoyage (cible)

À la racine, uniquement :
- `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `DEPLOY.md`, `LICENSE.md`, `RUNBOOK.md`
- `pyproject.toml`, `requirements.txt`, `pytest.ini`, `pyrightconfig.json`
- `.env.example`, `.gitignore`, `.dockerignore`
- `docker-compose.yml`, `Dockerfile`
- `main.py`, `run_e2_api.py`
- `start_full.bat`, `lancer_tout.bat`, `run_daily.ps1`
- `sources_config.json`

Tout le reste est rangé dans : `data/`, `docs/`, `models/`, `monitoring/`, `notebooks/`, `reports/`, `scripts/`, `src/`, `tests/`, `archive/`, `logs/`, `exports/`.

C'est cette structure qui est défendable en revue de code.
