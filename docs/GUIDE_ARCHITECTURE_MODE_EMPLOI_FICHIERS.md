# Guide architecture + mode d'emploi des fichiers DataSens

Ce guide est le document **unique de référence** pour l'architecture et l'usage des fichiers DataSens.

Il remplace les anciennes vues d'inventaire (`FICHIERS_PROJET_DATASENS.md`, `INVENTAIRE_PROJET.md`, `FICHIERS_FONCTIONNELS.md`) consolidées et archivées dans `archive/legacy_docs/` pour conservation historique.

Objectif : comprendre l'architecture, savoir quels fichiers sont critiques, utiliser les scripts sans se perdre.

---

## 0) Mises à jour importantes du jour (2026-04-20)

Cette section résume les changements récents côté robustesse pipeline + cockpit.

### A. Logs, quality gates, run contract

- `src/e1/pipeline.py`
  - contrat de run `PASS/WARN/FAIL`,
  - quality gates configurables (`MIN_LOADED_THRESHOLD`, `MIN_CLEAN_RATIO`, `MIN_ENRICHED_RATIO`),
  - `WARN_REASONS`,
  - traçabilité source avec deltas et anomalies (`SOURCE_DROP_WARN_PCT`),
  - persistance `reports/run_summary_*.json`.

### B. Transparence nettoyage

- `src/e1/pipeline.py`
  - catégorisation des rejets de nettoyage (`cleaning_rejects`),
  - échantillons explicatifs (`cleaning_reject_examples`).

### C. Cockpit Streamlit (observabilité)

- `src/streamlit/_cockpit_helpers.py`
  - `latest_run_summary_reports()`,
  - `run_summary_history()`,
  - rendu rapport d'exécution compact.
- `src/streamlit/page_modules/pipeline.py`
  - vue dernier run summary, historique et anomalies quality gate.
- `src/streamlit/page_modules/flux.py`
  - simplification UX (headers communs, analyse avancée repliée).
- `src/streamlit/page_modules/monitoring.py`
  - regroupement des panneaux techniques.

### D. Auth INSEE et volumes de collecte

- `src/e1/core.py`
  - auth INSEE adaptée APIM/OAuth suivant `.env`,
  - endpoints INSEE + SIREN configurables.
- `.env` / `.env.example`
  - ajout des paramètres INSEE et limites de collecte RSS/Reddit/Trustpilot/MonAvis.

---

## 1) Architecture globale (vision opérationnelle)

Flux principal :

1. **Collecte E1**  
   Entrée : `main.py`  
   Coeur : `src/e1/pipeline.py` + `src/e1/core.py`

2. **Transformation des données**  
   Zones : RAW -> SILVER -> GOLD (+ GoldAI consolidé)

3. **Stockage et exposition**  
   - SQLite (`datasens.db`) comme socle opérationnel,
   - Parquet pour échange, analyse et IA,
   - API FastAPI E2 (`run_e2_api.py`, `src/e2/api/`)

4. **Usage produit**  
   - Cockpit Streamlit (`src/streamlit/app.py`),
   - Monitoring Prometheus/Grafana/Uptime via `monitoring/`.

---

## 2) Fichiers critiques par ordre d'importance

## Niveau 0 - Démarrage / coeur métier
- `main.py` : point d'entrée pipeline E1.
- `src/e1/pipeline.py` : orchestration extraction -> nettoyage -> enrichissement -> export.
- `src/e1/core.py` : extracteurs, transformeurs, logique source.
- `src/e1/repository.py` : accès DB E1.
- `run_e2_api.py` : lancement API FastAPI E2.
- `src/e2/api/main.py` : app API.
- `src/streamlit/app.py` : cockpit principal.
- `src/config.py` : configuration centrale environnement/ports/chemins.
- `sources_config.json` : activation et paramètres des sources.
- `.env.example` : modèle de configuration.

## Niveau 1 - Données, enrichissement, qualité
- `src/collection_report.py` : rapport de collecte de session.
- `src/dashboard.py` : synthèse enrichissement.
- `src/metrics.py` : métriques Prometheus pipeline.
- `src/ml/inference/sentiment.py` : inférence sentiment.
- `src/e3/mistral/service.py` : intégration Mistral.
- `scripts/db_state_report.py` : état/cohérence DB.
- `scripts/merge_parquet_goldai.py` : fusion GOLD -> GoldAI.
- `scripts/create_ia_copy.py` : préparation datasets IA.
- `scripts/ai_benchmark.py` : benchmark modèles.
- `scripts/finetune_sentiment.py` : fine-tuning.

## Niveau 2 - Plateforme, exploitation, qualité logicielle
- `docker-compose.yml` : stack services.
- `monitoring/prometheus.yml` + `monitoring/grafana/**` : supervision.
- `.github/workflows/*.yml` : CI/CD.
- `tests/*.py` : non-régression et validation.
- `requirements.txt`, `pyproject.toml`, `pytest.ini`, `pyrightconfig.json`.

---

## 3) Arborescence utile (qui fait quoi)

- `src/e1/` : pipeline collecte/transformation/export.
- `src/e2/api/` : API REST sécurisée (JWT, RBAC, routes/services/schemas).
- `src/e3/` : orchestration IA (Mistral).
- `src/ml/inference/` : services modèles HF.
- `src/streamlit/` : cockpit.
- `src/spark/` : traitements distribués.
- `src/storage/` : Mongo/GridFS.
- `scripts/` : opérations (maintenance, benchmark, QA, exports, users).
- `tests/` : tests automatisés.
- `monitoring/` : Prometheus + Grafana.
- `docs/` : documentation fonctionnelle/technique.

---

## 4) Mode d'emploi scripts (par cas d'usage)

## A. Exécution quotidienne

1. Lancer pipeline :
```bash
python main.py
```

2. Vérifier état DB :
```bash
python scripts/db_state_report.py
```

3. Consolider GoldAI :
```bash
python scripts/merge_parquet_goldai.py
```

## B. API et cockpit

- API :
```bash
python run_e2_api.py
```

- Cockpit :
```bash
streamlit run src/streamlit/app.py
```

## C. IA / modèles

- Benchmark rapide :
```bash
python scripts/ai_benchmark.py --max-samples 200
```

- Benchmark complet :
```bash
python scripts/ai_benchmark.py
```

- Fine-tuning :
```bash
python scripts/finetune_sentiment.py --model sentiment_fr --epochs 3
```

- Préparer copie IA :
```bash
python scripts/create_ia_copy.py
```

## D. Maintenance données

- Régénérer exports :
```bash
python scripts/regenerate_exports.py
```

- Nettoyer buffer SQLite :
```bash
python scripts/cleanup_sqlite_buffer.py
```

- Sauvegarder Parquet vers Mongo :
```bash
python scripts/backup_parquet_to_mongo.py
```

## E. Utilisateurs / auth

- Créer utilisateur :
```bash
python scripts/create_user.py
```

- Initialiser profils :
```bash
python scripts/init_profils_table.py
```

## F. Qualité / tests

- Tests API E2 :
```bash
python scripts/run_e2_tests.py
```

- Pytest global :
```bash
python -m pytest tests/ -v
```

- Validation projet E1 :
```bash
python scripts/validate_e1_project.py
```

---

## 5) Lancements Windows recommandés

- `start_full.bat` : API + cockpit.
- `lancer_tout.bat` : stack élargie.
- `start_prometheus.bat`, `start_grafana.bat`, `start_mongo.bat`.

Ces scripts sont la voie la plus simple pour usage quotidien local.

---

## 6) Fichiers optionnels / contextuels

À utiliser seulement selon besoin :
- `scripts/_archive/activate_zzdb_source.py`, `scripts/_archive/test_zzdb.py` (sandbox ZZDB, archivés),
- `scripts/list_mongo_parquet.py`, `scripts/backup_parquet_to_mongo.py` (Mongo / GridFS),
- `scripts/_archive/demo_*.py`, `scripts/_archive/dossier_e1_examples.py` (démonstration historique, archivés),
- `src/spark/*` (usage Spark/distribué),
- `notebooks/*` (exploration pédagogique).

---

## 7) Ce qu'il ne faut pas prendre comme source de vérité

- Fichiers one-shot historiques (`fix_ruff_unicode.py`, `_fix_unicode_prometheus.py`) : obsolètes.
- Duplications legacy (`src/` racine vs `src/e1/`) : privilégier `src/e1/` pour le run pipeline.
- Toute donnée locale ignorée Git (`data/`, `exports/`, `*.db`, `logs/`) : dépend de la machine.

---

## 8) Checklist "je reprends le projet en 10 minutes"

1. Lire `README.md`.
2. Vérifier `.env` (copier depuis `.env.example` si besoin).
3. Contrôler `sources_config.json`.
4. Lancer `python main.py`.
5. Lancer `python scripts/db_state_report.py`.
6. Lancer API (`python run_e2_api.py`) puis cockpit (`streamlit run src/streamlit/app.py`).
7. Vérifier monitoring si nécessaire (Prometheus/Grafana).

---

## 9) Références croisées utiles

- `README.md` : vue produit et démarrage.
- `archive/legacy_docs/` : vues d'inventaire historiques (référence non opérationnelle).
- `scripts/README.md` + `scripts/SCRIPTS_LIST.md` : détails scripts.
- `docs/ARCHITECTURE.md` : architecture approfondie.
- `docs/AUDIT_CODE_NETTOYAGE.md` : plan de nettoyage et inventaire des candidats à archivage.

---

Si tu veux, je peux te faire une version "ultra courte 1 page" de ce guide pour la garder ouverte en permanence pendant que tu travailles.
