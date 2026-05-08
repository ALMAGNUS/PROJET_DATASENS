# DataSens

> Pipeline d'opinion publique française, de bout en bout. Scraping multi-sources →
> SQLite versionné → Parquet partitionné → API REST authentifiée → cockpit Streamlit →
> modèle de sentiment fine-tuné. Tout est tracé, tout est vérifiable par les chiffres.

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square)
![Tests](https://img.shields.io/badge/pytest-52%20passed-brightgreen?style=flat-square)
![Lint](https://img.shields.io/badge/ruff-0%20issues-brightgreen?style=flat-square)
![Coherence](https://img.shields.io/badge/db_state-OK-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

---

## TL;DR — ce qu'il y a dans la boîte (run du 8 mai 2026)

| Mesure | Valeur |
|---|---|
| Articles collectés (`raw_data`) | **51 495** sur 12 sources actives |
| Volume SQLite | 96 Mo, source de vérité unique |
| Liaisons `document_topic` | 90 562 |
| Prédictions ML stockées (`model_output`) | 105 127 |
| GoldAI consolidé | **87 659** lignes sur **66 dates** (16 déc 2025 → 8 mai 2026) |
| Splits IA (`train/val/test`) | 70 127 / 8 765 / 8 767, 0 fuite, 0 doublon, ≥ 30 caractères |
| Cohérence DB | **OK** (`scripts/db_state_report.py`, exécuté quotidiennement, archivé) |
| Drift sentiment | **OK** (`neutre 52.1 % · négatif 35.6 % · positif 12.4 %`) |
| Tests | **52 passed**, 0 failed (hors `test_spark_integration.py`) |
| Ruff | **0 issue** sur `src/` et `scripts/` |
| LOC `src/` | ~17 600 lignes Python |

Le rapport `db_state_*.{md,json}` est versionné dans [`reports/`](reports/) à chaque run. Le dernier en date :
[`reports/db_state_2026-05-08T073503Z.md`](reports/db_state_2026-05-08T073503Z.md).

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

Détail complet : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/dev/FLOW_DONNEES.md`](docs/dev/FLOW_DONNEES.md).

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

| Source | Type | Volume cumulé (8 mai) |
|---|---|---|
| `kaggle_french_opinions` | dataset (fondation) | 38 327 |
| `yahoo_finance` | RSS | 3 430 |
| `google_news_rss` | RSS | 3 251 |
| `rss_french_news` | RSS | 1 614 |
| `reddit_france` | API | 1 464 |
| `zzdb_csv` | CSV interne | 980 |
| `trustpilot_reviews` | scraping HTTP | 974 |
| `datagouv_datasets` | dataset | 735 |
| `openweather_api` | API | 465 |
| `GDELT_Last15_English` | bigdata | 185 |
| `insee_indicators` | API + fallback HTML | 36 |
| `agora_consultations` | API | 19 |
| `monavis_citoyen` | scraping Botasaurus | 14 |

Configuration unique : [`sources_config.json`](sources_config.json).
Sources `active: false` (Kaggle stopwords, lexicons, ifop annuel, zzdb_synthetic) gardées comme paliers de bascule.

---

## Garanties techniques

- **Tests** — `pytest tests/ --ignore=tests/test_spark_integration.py` → **52 passed, 0 failed**.
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
- **RBAC** — par zone : `viewer` (GOLD), `analyst` (SILVER + GOLD), `admin` (RAW + SILVER + GOLD). Test couvert (`tests/test_e2_api.py::TestPermissions`).
- **OWASP Top 10** — couverture documentée dans `docs/e2/`.
- **Isolation** — E1 / E2 / E3 séparés par interfaces. L'API E2 ne mute pas SILVER : HTTP 501 par design, message explicite (*"is not supported (E1 isolation by design)"*).
- **RGPD** — registre des traitements, procédure de tri des données personnelles (`docs/e4/`).
- **Gestion comptes** — `python scripts/change_password.py --list` puis `python scripts/change_password.py <email>`. Pas d'API de gestion utilisateurs (volontaire).

---

## Couverture compétences E1 – E5

| Bloc | Périmètre | Entrées dossier |
|---|---|---|
| **E1** | Extraction · transformation · stockage | [`docs/AUDIT_E1_COMPETENCES.md`](docs/AUDIT_E1_COMPETENCES.md), [`docs/Dossier_E1_preuves.md`](docs/Dossier_E1_preuves.md) |
| **E2** | API REST · sécurité · MLOps fine-tuning | [`docs/AUDIT_E2_COMPETENCES.md`](docs/AUDIT_E2_COMPETENCES.md), [`docs/Dossier_E2_A3_C6_C7_C8_FINAL.md`](docs/Dossier_E2_A3_C6_C7_C8_FINAL.md), [`docs/e2/`](docs/e2/) |
| **E3** | Distribué · orchestration IA Mistral | [`docs/AUDIT_E3_COMPETENCES.md`](docs/AUDIT_E3_COMPETENCES.md), [`docs/e3/`](docs/e3/) |
| **E4** | Gouvernance · RGPD · éthique | [`docs/AUDIT_E4_ECART.md`](docs/AUDIT_E4_ECART.md) |
| **E5** | Monitoring · MCO · incidents | [`docs/AUDIT_E5_COMPETENCES.md`](docs/AUDIT_E5_COMPETENCES.md), [`docs/e5/`](docs/e5/) |

Index docs : [`docs/README.md`](docs/README.md).

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
reports/                # db_state · run_summary · pipeline_proof (versionnés)
models/                 # checkpoints fine-tunés + trainer_state (gitignored)
notebooks/              # E1 pédagogique + Colab fine-tuning
scripts/                # 46 utilitaires actifs (post-audit) + scripts/_archive/
tests/                  # 16 fichiers, 52 tests verts
docs/                   # E1-E5 + dev/ (LOGGING, DOCKER_RUNTIME, FLOW_DONNEES)
monitoring/             # config Prometheus + Grafana + provisioning
archive/legacy_docs/    # docs obsolètes archivées (audit code)
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
- **130 lignes GoldAI** seulement portent un `raw_data_id` (les 87 529 autres sont historiques pré-traçabilité). Le rapport `db_state` le signale (`non_comparable_legacy_rows_without_raw_data_id`) et propose la métrique alternative correcte.
- **Distribution sentiment déséquilibrée** (52 / 36 / 12). Compensée à l'entraînement par `class_weight="balanced"` dans `scripts/finetune_sentiment.py`.

---

## Liens secs

- [`RUNBOOK.md`](RUNBOOK.md) — toutes les commandes pour lancer la stack.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — standards code, ruff, tests, conventions de commit.
- [`CHANGELOG.md`](CHANGELOG.md) — historique technique détaillé.
- [`DEPLOY.md`](DEPLOY.md) — déploiement.
- [`docs/dev/`](docs/dev/) — `LOGGING.md`, `DOCKER_RUNTIME.md`, `FLOW_DONNEES.md`.
- [`docs/AUDIT_CODE_NETTOYAGE.md`](docs/AUDIT_CODE_NETTOYAGE.md) — audit récent (7 étapes, ~2 000 lignes mortes retirées).
- [`reports/`](reports/) — état de la base, pour chaque run, archivé.

---

## Licence

MIT — voir [`LICENSE.md`](LICENSE.md).

---

*Dernière mise à jour : 8 mai 2026 (run du jour, 51 495 articles, cohérence OK, 52 tests verts, 0 ruff issue).*
