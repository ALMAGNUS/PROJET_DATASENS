# DataSens

> Plateforme française de collecte, d'enrichissement et de mise à disposition
> de données d'actualité et d'opinion — du scraping à l'inférence IA.

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)
![Pipeline](https://img.shields.io/badge/pipeline-daily-brightgreen?style=flat-square)
![Coherence](https://img.shields.io/badge/coherence-OK-brightgreen?style=flat-square)

---

## Ce que fait le projet

Un pipeline **end-to-end** qui :

1. **Collecte** quotidiennement 15 sources hétérogènes (RSS, API, scraping, datasets).
2. **Nettoie et structure** les données en 3 zones (RAW → SILVER → GOLD).
3. **Enrichit** chaque article avec un topic et un sentiment (règles + modèles fine-tunés CamemBERT).
4. **Expose** les données via une API REST FastAPI authentifiée (JWT + RBAC par zone).
5. **Orchestre** des insights via Mistral AI et un cockpit Streamlit.
6. **Monitore** la stack avec Prometheus / Grafana / Uptime Kuma.

---

## Chiffres — run du 18 avril 2026

| Indicateur | Valeur |
|---|---|
| Articles stockés (`raw_data`) | **48 155** |
| Articles enrichis (topic + sentiment) | **48 151** (~100 %) |
| Liaisons `document_topic` | 88 345 |
| Prédictions ML (`model_output`) | 101 787 |
| Sources configurées | 15 (12 actives par run) |
| Distribution sentiment | 50 % neutre · 37 % négatif · 13 % positif |
| Taille SQLite | 92,7 Mo |
| Cohérence du dataset | **OK** (vérifiée par `scripts/db_state_report.py`) |

Rapport quotidien versionné dans [`reports/`](reports/).

---

## Architecture

```
┌─────────────────┐
│ 15 sources      │  RSS · API · scraping · datasets · CSV
│ hétérogènes     │
└────────┬────────┘
         │ extractors (src/e1/core.py)
         ▼
┌─────────────────┐
│ RAW             │  JSON + CSV natifs, partitionnés par date
│ data/raw/       │  aucune transformation
└────────┬────────┘
         │ aggregator + quality scoring + déduplication
         ▼
┌─────────────────┐
│ SILVER          │  Parquet nettoyé, topics rule-based
│ data/silver/    │  SQLite datasens.db (source de vérité)
└────────┬────────┘
         │ enrichissement ML (sentiment HuggingFace, tagging)
         ▼
┌─────────────────┐
│ GOLD            │  Parquet prêt pour ML / BI
│ data/gold/      │  + GoldAI (dataset d'entraînement E2)
└────────┬────────┘
         │
         ├──► API E2 (FastAPI + JWT + RBAC, port 8001)
         ├──► Cockpit Streamlit (port 8501)
         ├──► Insights Mistral (E3)
         └──► Monitoring Prometheus + Grafana (ports 9090 / 3000)
```

Détail complet : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Démarrage rapide

### 1. Dépendances

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

### 2. Environnement

```bash
copy .env.example .env          # Windows
# cp .env.example .env          # Linux / macOS
```

Variables utiles :

- `DB_PATH` — chemin du SQLite (défaut : `~/datasens_project/datasens.db`).
- `OPENWEATHERMAP_API_KEY` — activation source météo (sinon fallback Open-Meteo sans clé).
- `INSEE_API_TOKEN` ou `INSEE_CONSUMER_KEY`/`INSEE_CONSUMER_SECRET` — API INSEE (sinon fallback site public).

### 3. Pipeline quotidien

```bash
python main.py
```

Exécute les 12 sources actives : extraction → nettoyage → topics → sentiment → exports RAW/SILVER/GOLD → SQLite.

### 4. Rapport de cohérence

```bash
python scripts/db_state_report.py
```

Génère `reports/db_state_<timestamp>.{md,json}` et confirme `coherence: OK`.

### 5. Stack complète (API + monitoring + cockpit)

La séquence de démarrage complète (Docker Compose + MLflow + Streamlit + monitoring) est documentée dans [`PLANCHE_LANCEMENT.md`](PLANCHE_LANCEMENT.md).

Lanceurs Windows disponibles à la racine :

- `lancer_tout.bat` — démarre toute la stack
- `start_full.bat` — API + cockpit Streamlit
- `start_prometheus.bat`, `start_grafana.bat`, `start_uptime_kuma.bat`, `start_mongo.bat` — services isolés

---

## Sources

Configuration unique dans [`sources_config.json`](sources_config.json). Les sources actives en production :

| Source | Type | Volume cumulé |
|---|---|---|
| `kaggle_french_opinions` | dataset (fondation) | 38 327 |
| `yahoo_finance` | RSS | 2 577 |
| `google_news_rss` | RSS | 2 366 |
| `rss_french_news` | RSS | 1 216 |
| `zzdb_csv` | CSV | 980 |
| `reddit_france` | API | 898 |
| `trustpilot_reviews` | scraping HTTP | 834 |
| `datagouv_datasets` | dataset | 430 |
| `openweather_api` | API | 329 |
| `GDELT_Last15_English` | bigdata | 129 |
| `insee_indicators` | API + fallback | 35 |
| `agora_consultations` | API | 19 |
| `monavis_citoyen` | scraping Botasaurus | 14 |

Sources inactives (`active: false`) : suites Kaggle (stopwords, lexicons, tweets), `ifop_barometers` (cadence annuelle), `zzdb_synthetic` (MongoDB optionnel).

---

## Couverture E1 – E5

| Bloc | Scope | Entry points documentation |
|---|---|---|
| **E1** — Extraction / transformation / stockage | pipeline `main.py`, `src/e1/` | [`docs/AUDIT_E1_COMPETENCES.md`](docs/AUDIT_E1_COMPETENCES.md), [`docs/Dossier_E1_preuves.md`](docs/Dossier_E1_preuves.md) |
| **E2** — API REST + sécurité + MLOps fine-tuning | `src/e2/api/`, `src/ml/inference/` | [`docs/AUDIT_E2_COMPETENCES.md`](docs/AUDIT_E2_COMPETENCES.md), [`docs/Dossier_E2_A3_C6_C7_C8_FINAL.md`](docs/Dossier_E2_A3_C6_C7_C8_FINAL.md), [`docs/e2/`](docs/e2/) |
| **E3** — Traitement distribué + orchestration IA | `src/spark/`, `src/e3/mistral/` | [`docs/AUDIT_E3_COMPETENCES.md`](docs/AUDIT_E3_COMPETENCES.md), [`docs/e3/DOSSIER_E3_A4_A5_C9_C10_C11_C12_C13.md`](docs/e3/DOSSIER_E3_A4_A5_C9_C10_C11_C12_C13.md) |
| **E4** — Gouvernance / RGPD / éthique | `docs/` | [`docs/AUDIT_E4_ECART.md`](docs/AUDIT_E4_ECART.md) |
| **E5** — Monitoring / MCO / incidents | `monitoring/`, `src/monitoring/` | [`docs/AUDIT_E5_COMPETENCES.md`](docs/AUDIT_E5_COMPETENCES.md), [`docs/e5/DOSSIER_E5_A9_C20_C21.md`](docs/e5/DOSSIER_E5_A9_C20_C21.md) |

Index complet : [`docs/README.md`](docs/README.md).

---

## Structure du dépôt

```
main.py                   # Point d'entrée pipeline E1
sources_config.json       # Sources configurées
requirements.txt          # Dépendances Python
pyproject.toml            # Config Ruff
docker-compose.yml        # Services conteneurisés
src/
  e1/                     # Extraction, aggregation, export, tagging
  e2/api/                 # API REST FastAPI (auth, RAW/SILVER/GOLD, analytics, AI)
  e3/mistral/             # Orchestration IA
  spark/                  # Traitements Spark
  ml/inference/           # Modèles HuggingFace (sentiment, topics)
  streamlit/              # Cockpit dashboard
  storage/                # MongoDB GridFS (backup modèles)
  monitoring/             # Métriques Prometheus
  observability/          # Lineage
  data_contracts/         # Schemas + guards
data/                     # Zones RAW/SILVER/GOLD + datasens.db (ignoré par Git)
tests/                    # Tests unitaires pytest
notebooks/                # Notebooks pédagogiques E1
scripts/                  # Utilitaires (db_state_report, manage_parquet, etc.)
docs/                     # Dossiers compétences E1–E5 + annexes + archive
reports/                  # Rapports quotidiens db_state_*.{md,json}
monitoring/               # Config Prometheus + Grafana
```

Arbre détaillé : [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Stack technique

**Langages** · Python 3.13 · SQL · Bash / PowerShell  
**Pipeline** · `main.py` (SOLID/DRY) · `loguru` · Ruff · pytest  
**Stockage** · SQLite · Parquet (pyarrow) · MongoDB GridFS (backup)  
**ML / IA** · HuggingFace Transformers · CamemBERT fine-tuné · Mistral AI · MLflow  
**Distribution** · Apache Spark (PySpark local)  
**API** · FastAPI · JWT · RBAC · OpenAPI 3.1  
**Cockpit** · Streamlit  
**Monitoring** · Prometheus · Grafana · Uptime Kuma  
**Conteneurisation** · Docker Compose (7 services)

---

## Sécurité et conformité

- Authentification JWT + RBAC par zone (RAW / SILVER / GOLD) — [`docs/README_E2_API.md`](docs/README_E2_API.md).
- Audit trail complet des requêtes API.
- Couverture OWASP Top 10 documentée — `docs/e2/`.
- Isolation stricte E1/E2/E3 via interfaces (`src/shared/interfaces.py`).
- RGPD : registre des traitements + procédure de tri data personnelle.

---

## Tests et qualité

```bash
# Tests unitaires
.venv\Scripts\python.exe -m pytest tests/ -v

# Lint
run_ruff.bat                # ou : ruff check .

# Quality gate E3
python scripts/run_e3_quality_gate.py
```

---

## Limites connues et pistes

Consigne dans [`BACKLOG.md`](BACKLOG.md) : migration OAuth2 INSEE (fallback public actif), confiance moyenne des topics structurellement basse (documentée), améliorations optionnelles du cockpit.

---

## Contributions et licence

- Processus et standards : [`CONTRIBUTING.md`](CONTRIBUTING.md).
- Historique des versions : [`CHANGELOG.md`](CHANGELOG.md).
- Licence : MIT — voir [`LICENSE.md`](LICENSE.md).

---

*Dernière mise à jour : 18 avril 2026.*
