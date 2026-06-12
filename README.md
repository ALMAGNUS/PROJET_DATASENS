# DataSens

> Pipeline d'opinion publique française, de bout en bout. Scraping multi-sources →
> SQLite versionné → Parquet partitionné → API REST authentifiée → cockpit Streamlit →
> modèle de sentiment fine-tuné. Tout est tracé, tout est vérifiable par les chiffres.

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square)
![Tests](https://img.shields.io/badge/pytest-65%20passed-brightgreen?style=flat-square)
![Lint](https://img.shields.io/badge/ruff-0%20issues-brightgreen?style=flat-square)
![Coherence](https://img.shields.io/badge/db_state-OK-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

---

## TL;DR — ce qu'il y a dans la boîte (run du 12 juin 2026)

| Mesure | Valeur |
|---|---|
| Articles collectés (`raw_data`) | **56 631** sur ~13 sources actives |
| Volume SQLite | 102 Mo, source de vérité unique |
| Liaisons `document_topic` | 98 925 |
| Prédictions ML stockées (`model_output`) | 110 263 |
| GoldAI consolidé | **92 792** lignes sur **98 dates** (16 déc 2025 → 12 juin 2026) |
| Splits IA (`train/val/test`) | 19 156 / 2 394 / 2 396, 0 fuite, split temporel |
| Cohérence DB | **OK** (`scripts/db_state_report.py`, exécuté quotidiennement, archivé) |
| Drift sentiment | **OK** (`neutre 54.6 % · négatif 33.7 % · positif 11.7 %`) |
| Tests | **65 passed**, 1 skipped, 0 failed |
| Ruff | **0 issue** sur `src/` et `scripts/` |
| LOC `src/` | ~17 600 lignes Python |

Le rapport `db_state_*.{md,json}` est versionné dans [`reports/`](reports/) à chaque run. Le dernier en date :
[`reports/db_state_2026-06-12T072035Z.md`](reports/db_state_2026-06-12T072035Z.md).

---

## Ce que ça fait, ce que ça ne fait pas

**Ça fait** : extraire 12 sources hétérogènes (RSS, API officielles, scraping HTTP/Botasaurus, datasets Kaggle/GDELT, CSV ZZDB), normaliser dans un schéma unique, dédupliquer par `fingerprint`, scorer la qualité, étiqueter en topics règles + sentiment ML, exposer en API REST avec JWT/RBAC par zone, sauvegarder en GridFS MongoDB, et tout monitorer.

**Ça ne fait pas** : du temps réel, du multi-tenant, du SaaS managé. Le poste cible est un **dev unique sur Windows** avec un venv et Docker Desktop facultatif. La production tient sur un seul serveur. Les bornes sont assumées.

---

## Architecture — flux et contrats

```
                         sources_config.json (15 sources, 12 actives)
                                       │
                          ┌────────────┴────────────┐
                          ▼                         ▼
                   src/e1/extractors        src/e1/aggregator
                   (RSS · API · scrap)      (validation, fingerprint, qualité)
                          │                         │
                          ▼                         ▼
                  ┌──────────────┐          ┌──────────────┐
                  │   RAW        │          │   SILVER     │   ←── source de vérité
                  │ data/raw/    │          │ datasens.db  │       SQLite (96 Mo)
                  │ JSON natifs  │          │ Parquet par  │       quality_score, topics
                  │ (preuve)     │          │ date         │       rule-based
                  └──────────────┘          └──────┬───────┘
                                                   │
                                                   ▼
                                       src/datasets/gold_branches.py
                                       (normalisation labels, ascii-fold)
                                                   │
                          ┌────────────────────────┴────────────────────────┐
                          ▼                                                 ▼
                ┌──────────────────┐                              ┌──────────────────┐
                │ gold_app_input   │  ← inférence, sans label     │ gold_ia_labelled │  ← entraînement
                │ data/goldai/app/ │     (anti-leakage explicite) │ data/goldai/ia/  │     train/val/test
                └────────┬─────────┘                              └────────┬─────────┘
                         │                                                 │
                         ├──► API E2 (FastAPI · JWT · RBAC)                ├──► finetune CamemBERT
                         │    src/e2/api/  port 8001                       │    + Colab notebook
                         ├──► Cockpit Streamlit (port 8501)                │    + class_weight balanced
                         ├──► Insights Mistral (E3, src/e3/mistral/)       │
                         ├──► Backup GridFS (scripts/backup_parquet_to_mongo.py)
                         └──► Monitoring (Prometheus · Grafana · Uptime Kuma)
```

**Contrats internes** (pas négociables, garantis par tests et data contracts) :

- `src/data_contracts/` — `assert_no_target_leakage`, `assert_training_label_present`. Aucun `gold_app_input` ne contient de label. Aucun `gold_ia_labelled` ne perd son label en route.
- `src/shared/interfaces.py` — frontière E1 / E2 / E3. L'API E2 ne *crée* pas de données SILVER (HTTP 501 explicite, par design, documenté en docstring).
- Quality gates `.env` — `MIN_LOADED_THRESHOLD`, `MIN_CLEAN_RATIO`, `MIN_ENRICHED_RATIO`, `SOURCE_DROP_WARN_PCT`. Un run produit `PASS / WARN / FAIL` consigné dans `reports/run_summary_*.json`.
- ASCII-fold des labels (`gold_branches.normalize_sentiment_label`) : encoding-agnostic. Absorbe les corruptions Windows / Spark / CSV (`négatif`, `n�gatif`, `n\xefegatif`) → `negatif`.

Détail complet : [`docs/dev/FLOW_DONNEES.md`](docs/dev/FLOW_DONNEES.md), [`docs/CHEMIN_DONNEE.md`](docs/CHEMIN_DONNEE.md), [`RUNBOOK.md`](RUNBOOK.md) §1.

---

## Stack — versions réelles, pas du buzz

| Couche | Outil | Version |
|---|---|---|
| Langage | Python | 3.13 |
| Pipeline | `loguru` · `ruff` · `pytest` · contrat PASS/WARN/FAIL maison | — |
| Stockage chaud | SQLite | natif Py |
| Stockage analytique | Parquet (`pyarrow`) | 22.0.0 |
| Backup | MongoDB GridFS | 7.0.28 (natif) ou `mongo:7` (compose) |
| API | FastAPI · `python-jose` · `passlib[bcrypt]` | 0.111.0 |
| ORM | SQLModel · SQLAlchemy | 0.0.21 / ≥ 2.0.36 |
| Distribué | PySpark · delta-spark | 3.5.1 / 3.0.0 |
| ML | HuggingFace Transformers · CamemBERT · Mistral AI | — |
| Tracking ML | JSON versionnés Git (`docs/e2/TRAINING_RESULTS.json`, `AI_BENCHMARK_RESULTS.json`) + HF `trainer_state.json` + TensorBoard côté Colab. Pas de MLflow (mono-poste). Détails : [`RUNBOOK.md` § 11.5](RUNBOOK.md#115-tracking-des-entra%C3%AEnements-ml). | — |
| Cockpit | Streamlit | — |
| Scraping | `feedparser` · `requests` · `beautifulsoup4` · `botasaurus` | — |
| Datasets externes | `kagglehub` · GDELT · INSEE · OpenWeather · datagouv | — |
| Monitoring | Prometheus · Grafana · Uptime Kuma | docker compose |
| Conteneurs | Docker Compose (7 services) | — |

**Verrou NumPy** : `numpy>=2.1,<2.2` — `bottleneck`, `numexpr` et `scipy` n'aiment pas la 2.2.x. Verrou assumé, documenté dans `requirements.txt`.

---

## Démarrage rapide

### 1. Environnement

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Les seules variables vraiment utiles :

- `DB_PATH` — chemin SQLite (défaut `~/datasens_project/datasens.db`).
- `OPENWEATHERMAP_API_KEY` — sinon fallback Open-Meteo sans clé.
- `INSEE_API_TOKEN` ou `INSEE_CONSUMER_KEY/SECRET` — sinon fallback site public.
- `MISTRAL_API_KEY` — pour les insights E3 (sinon E3 désactivé silencieusement).
- `MIN_LOADED_THRESHOLD`, `MIN_CLEAN_RATIO`, `MIN_ENRICHED_RATIO`, `SOURCE_DROP_WARN_PCT` — quality gates.

### 2. Pipeline E1 (extraction → SILVER → GOLD → GoldAI)

```bat
python main.py
```

12 sources actives, run typique : ~ 90 secondes, +100 à +200 articles selon la cadence des flux.
Logs structurés dans `logs/datasens.log`, summary JSON dans `reports/run_summary_*.json`.

### 3. Rapport de cohérence

```bat
python scripts/db_state_report.py
```

Génère `reports/db_state_<timestamp>.{md,json}` et confirme `coherence: OK`.

### 4. Stack complète (API + cockpit)

```bat
start_full.bat
```

Démarre l'API E2 (port 8001) et le cockpit Streamlit (port 8501) dans deux terminaux dédiés.
Pour la stack monitoring (Prometheus, Grafana, Uptime Kuma) et MongoDB, voir [`RUNBOOK.md`](RUNBOOK.md).

### 5. Fine-tuning CamemBERT

```bat
scripts\run_training_loop_e2.bat --full
```

Sorties :
- modèle : `models/sentiment_fr-sentiment-finetuned/`
- métriques : `docs/e2/TRAINING_RESULTS.json` + `AI_BENCHMARK_RESULTS.json` (versionnés Git)
- courbes : `docs/e2/figures/e2_training_*.png`

Notebook Colab (GPU gratuit) en option : `notebooks/colab_finetune_sentiment.ipynb` —
courbes loss / F1 inline via TensorBoard.
Ré-injection locale du modèle entraîné : `python scripts/install_colab_model.py <archive.zip>`.

---

## Sources actives — production

| Source | Type | Volume cumulé (12 juin) |
|---|---|---|
| `kaggle_french_opinions` | dataset (fondation) | 38 327 |
| `yahoo_finance` | RSS | 4 907 |
| `google_news_rss` | RSS | 4 607 |
| `rss_french_news` | RSS | 2 380 |
| `reddit_france` | API | 2 207 |
| `datagouv_datasets` | dataset | 1 276 |
| `zzdb_csv` | CSV interne | 980 |
| `trustpilot_reviews` | scraping HTTP | 974 |
| `openweather_api` | API | 642 |
| `GDELT_Last15_English` | bigdata | 242 |
| `insee_indicators` | API + fallback HTML | 36 |
| `monavis_citoyen` | scraping Botasaurus | 33 |
| `agora_consultations` | API | 19 |

Configuration unique : [`sources_config.json`](sources_config.json).
Sources `active: false` (Kaggle stopwords, lexicons, ifop annuel, zzdb_synthetic) gardées comme paliers de bascule.

---

## Garanties techniques

- **Tests** — `pytest tests/` → **65 passed, 1 skipped, 0 failed** (`test_spark_integration.py` ignoré sur anciens snapshots GOLD).
- **Lint** — `ruff check src/ scripts/` → **0 issue**.
- **Cohérence DB** — `scripts/db_state_report.py` exécuté quotidiennement, sortie versionnée. Détecte toute incohérence `raw_data ↔ document_topic ↔ model_output ↔ GoldAI`.
- **Drift sentiment** — comparaison entre rapports successifs, statut `OK / DRIFT` consigné dans le rapport `db_state`.
- **Quality gates pipeline** — `PASS / WARN / FAIL` par run, seuils dans `.env`, motifs de rejet de nettoyage capturés (`cleaning_rejects`, `cleaning_reject_examples`).
- **Lineage par les lignes** — `src/streamlit/data_lineage.py` trace un même échantillon d'articles à travers SQLite → Parquet GOLD → GoldAI consolidé → GridFS MongoDB. Affiché dans le cockpit, panneau `Vue d'ensemble`.
- **Anti-leakage explicite** — `gold_app_input` ↔ `gold_ia_labelled` séparés en deux fichiers, vérifié par `assert_no_target_leakage`. Splits temporels (pas aléatoires).
- **Audit trail API** — toutes les requêtes API tracées (table `audit_log`).

---

## Sécurité et conformité

- **Auth** — JWT court (`python-jose`), bcrypt sur les mots de passe (`passlib`), table SQLite `profils`.
- **RBAC** — 4 rôles (`src/e2/api/dependencies/permissions.py`) : `reader` (lecture RAW/SILVER/GOLD), `writer` (création/màj), `deleter` (suppression), `admin` (tout). Lève **403** si rôle insuffisant. Test couvert (`tests/test_e2_api.py`).
- **OWASP Top 10** — couverture documentée dans `docs/e2/`.
- **Isolation** — E1 / E2 / E3 séparés par interfaces. L'API E2 ne mute pas SILVER : HTTP 501 par design, message explicite (*"is not supported (E1 isolation by design)"*).
- **RGPD** — [`docs/REGISTRE_TRAITEMENTS_RGPD.md`](docs/REGISTRE_TRAITEMENTS_RGPD.md), [`docs/PROCEDURE_TRI_DONNEES_PERSONNELLES.md`](docs/PROCEDURE_TRI_DONNEES_PERSONNELLES.md).
- **Gestion comptes** — `python scripts/change_password.py --list` puis `python scripts/change_password.py <email>`. Pas d'API de gestion utilisateurs (volontaire).

---

## Couverture compétences E1 – E5

| Bloc | Périmètre | Entrées dossier |
|---|---|---|
| **E1** | Extraction · transformation · stockage | [`main.py`](main.py), [`docs/dev/FLOW_DONNEES.md`](docs/dev/FLOW_DONNEES.md), [`docs/CHEMIN_DONNEE.md`](docs/CHEMIN_DONNEE.md), [`reports/`](reports/) |
| **E2** | API REST · sécurité · MLOps fine-tuning | [`docs/e2/`](docs/e2/), [`docs/e2/E2_FAQ.md`](docs/e2/E2_FAQ.md), [`docs/FASTAPI_RBAC_IMPLEMENTATION.md`](docs/FASTAPI_RBAC_IMPLEMENTATION.md) |
| **E3** | Distribué · orchestration IA Mistral | [`src/spark/`](src/spark/), [`src/e3/mistral/service.py`](src/e3/mistral/service.py), [`docs/MISTRAL_IA_INSIGHTS.md`](docs/MISTRAL_IA_INSIGHTS.md) |
| **E4** | Gouvernance · RGPD · éthique | [`docs/REGISTRE_TRAITEMENTS_RGPD.md`](docs/REGISTRE_TRAITEMENTS_RGPD.md), [`docs/PROCEDURE_TRI_DONNEES_PERSONNELLES.md`](docs/PROCEDURE_TRI_DONNEES_PERSONNELLES.md) |
| **E5** | Monitoring · MCO · incidents | [`docs/METRIQUES_SEUILS_ALERTES.md`](docs/METRIQUES_SEUILS_ALERTES.md), [`docs/PROCEDURE_INCIDENTS.md`](docs/PROCEDURE_INCIDENTS.md), [`docs/MONITORING_E2_API.md`](docs/MONITORING_E2_API.md) |

---

## Cartographie du dépôt

```
main.py                 # Point d'entrée pipeline E1
run_e2_api.py           # Lanceur API
sources_config.json     # 15 sources, 12 actives
docker-compose.yml      # 7 services : e1-metrics, e1, e2-api, mongodb, prometheus, grafana, uptime-kuma
RUNBOOK.md              # Doc opérationnelle unique (consolidée)

src/                    # 17 600 lignes Python
  e1/                   #   pipeline E1 (extraction, agrégation, exports, tagging, quality gates)
  e2/api/               #   FastAPI (auth, RAW/SILVER/GOLD, analytics, AI, audit)
  e3/mistral/           #   orchestration IA
  spark/                #   PySpark distribué (winutils Windows ok)
  ml/inference/         #   modèles HuggingFace (sentiment, topics, batch)
  datasets/             #   gold_branches : normalisation, ascii-fold, anti-leakage
  data_contracts/       #   schemas + assertions
  streamlit/            #   cockpit (4 onglets : Vue d'ensemble · Pipeline · IA · Pilotage)
  storage/              #   MongoDB GridFS (backup parquet)
  monitoring/           #   exporters Prometheus
  observability/        #   lineage, traces inter-couches
  shared/               #   interfaces (frontières E1/E2/E3)

data/                   # RAW · SILVER · GOLD · goldai · datasens.db (gitignored)
reports/                # db_state · run_summary (versionnés)
models/                 # checkpoints fine-tunés + trainer_state (gitignored)
notebooks/              # E1 pédagogique + Colab fine-tuning
scripts/                # 46 utilitaires actifs (post-audit) + scripts/_archive/
tests/                  # 16 fichiers, 65 tests verts (+ 1 skipped)
docs/                   # E1-E5 + dev/ (LOGGING, DOCKER_RUNTIME, FLOW_DONNEES)
monitoring/             # config Prometheus + Grafana + provisioning
```

Arbre détaillé et conventions : [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Compromis assumés

- **Windows-first**. Le poste cible est un dev Windows. Les `.bat` sont la voie officielle, les commandes Linux fonctionnent (PySpark + winutils sont pré-câblés via `HADOOP_HOME` dans `src/spark/session.py`).
- **NumPy verrouillé en 2.1.x**. `bottleneck`, `numexpr` et `scipy` plus anciens cassent en 2.2. Recréation venv documentée dans `scripts/fix_venv.bat`.
- **MongoDB optionnel**. Le pipeline tourne sans Mongo. GridFS sert au backup long terme et à la preuve de lineage. Fallback documenté : container Docker *ou* service Windows natif.
- **Spark local uniquement**. Pas de cluster. PySpark sert à valider le code distribué et à traiter les corpus Kaggle ; pour la production batch quotidienne, pandas est plus simple et plus rapide.
- **Mistral et Colab opt-in**. Les insights E3 et le fine-tuning Colab fonctionnent à la demande, pas en boucle quotidienne. La pipeline locale est self-contained.
- **Pas de SaaS, pas de cloud**. Toute la stack tient sur un poste + un compose. Migrer en cloud public est une question d'infra, pas de code.

---

## Limites connues

- **Confiance moyenne des topics** structurellement basse (rule-based, multi-labels par article). Conséquence directe du choix règles vs ML pour le tagging — assumée, pas un bug.
- **OAuth2 INSEE** non implémenté (le fallback site public est actif et testé).
- **130 lignes GoldAI** seulement portent un `raw_data_id` (les 92 662 autres sont historiques pré-traçabilité). Le rapport `db_state` le signale (`non_comparable_legacy_rows_without_raw_data_id`) et propose la métrique alternative correcte.
- **Distribution sentiment déséquilibrée** (~55 / 34 / 12 en base). Compensée à l'entraînement par `class_weight="balanced"` et sélection sur le F1 macro dans `scripts/finetune_sentiment.py`.

---

## Liens secs

- [`RUNBOOK.md`](RUNBOOK.md) — toutes les commandes pour lancer la stack.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — standards code, ruff, tests, conventions de commit.
- [`CHANGELOG.md`](CHANGELOG.md) — historique technique détaillé.
- [`DEPLOY.md`](DEPLOY.md) — déploiement.
- [`docs/dev/`](docs/dev/) — `LOGGING.md`, `DOCKER_RUNTIME.md`, `FLOW_DONNEES.md`.
- [`CHANGELOG.md`](CHANGELOG.md) — historique des évolutions et nettoyages successifs.
- [`reports/`](reports/) — état de la base, pour chaque run, archivé.

---

## Licence

MIT — voir [`LICENSE.md`](LICENSE.md).

---

*Dernière mise à jour : 12 juin 2026 (run du jour, 56 631 articles, cohérence OK, 65 tests verts, 0 ruff issue).*
