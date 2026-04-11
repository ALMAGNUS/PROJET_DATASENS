# État des lieux — RUN, routes API, stockage (SQLite, fichiers, MongoDB, logs)

Document de synthèse pour présentation (jury, démo, onboarding).  
**Racine projet** : le dossier du clone Git (ex. `C:\Users\Utilisateur\Desktop\PROJET_DATASENS`). Les chemins relatifs partent de ce répertoire si tu lances les commandes depuis la racine du repo.

### Stockage : trois niveaux (à présenter clairement)

| Niveau | Technologie | Rôle |
|--------|-------------|------|
| **Opérationnel** | SQLite (`datasens.db`) | Ingestion, dédup, tagging, API E1/E2 sur les données « chaudes » |
| **Analytique / travail** | Parquet sur disque (`data/gold`, `data/goldai`, etc.) | GOLD, GoldAI, ML, Spark, figures |
| **Long terme** | **MongoDB GridFS** | **Archivage durable** des jeux Parquet (et artefacts associés) : sauvegarde centralisée, hors dépendance au seul disque du poste |

Le pipeline E1 **tourne sans MongoDB** (SQLite + Parquet suffisent pour un run). **MongoDB n’est pas « secondaire » au sens métier** : c’est le **stockage long terme prévu** du projet ; il est **activé** quand l’infra est up (Docker) et qu’on lance le script de push (`backup_parquet_to_mongo.py`) / réglages `.env`. Dire « optionnel » côté code = *le run ne l’exige pas* ; dire « long terme » côté archi = *c’est bien là que les Parquet vivent pour la durée*.

---

## 1. API E2 (FastAPI)

| Élément | Valeur par défaut |
|--------|-------------------|
| Préfixe API | `/api/v1` (`api_v1_prefix` dans `src/config.py`) |
| Port HTTP | `8001` (`fastapi_port`) |
| Base locale | `http://127.0.0.1:8001` |
| Documentation | `http://127.0.0.1:8001/docs` |
| OpenAPI JSON | `http://127.0.0.1:8001/openapi.json` |

**Hors préfixe `/api/v1`**

| Méthode | Chemin | Rôle |
|--------|--------|------|
| GET | `/health` | Santé du service |
| GET | `/metrics` | Métriques Prometheus (texte brut) |

**Sous `/api/v1`** (JWT requis sauf login — selon endpoint)

| Zone | Préfixe | Exemples |
|------|---------|----------|
| Authentification | `/auth` | `POST /api/v1/auth/login` |
| RAW (lecture) | `/raw` | `GET /api/v1/raw/articles`, `GET /api/v1/raw/articles/{id}` |
| SILVER | `/silver` | `GET /api/v1/silver/articles`, `GET /api/v1/silver/articles/{id}` — écriture exposée mais **501** (E2 ne modifie pas E1) |
| GOLD | `/gold` | `GET /api/v1/gold/articles`, `GET /api/v1/gold/articles/{id}`, `GET /api/v1/gold/stats` |
| Sources | `/sources` | CRUD `GET/POST/PUT/DELETE` sous `/api/v1/sources` |
| Analytics (Spark / Parquet) | `/analytics` | `.../sentiment/distribution`, `.../source/aggregation`, `.../statistics`, `.../available-dates`, `.../drift-metrics` |
| IA | `/ai` | `GET .../ai/status`, `POST .../ai/chat`, `.../summarize`, `.../sentiment`, `GET .../ai/ml/sentiment-goldai`, `POST .../ai/predict`, `POST .../ai/insight` |

Implémentation : `src/e2/api/main.py` et `src/e2/api/routes/`.

---

## 2. Chaîne RUN typique et fichiers produits

Commandes souvent enchaînées après le pipeline :

```text
python main.py
python scripts/merge_parquet_goldai.py
python scripts/build_gold_branches.py
python scripts/create_ia_copy.py
python scripts/backup_parquet_to_mongo.py   ← archivage long terme GridFS (voir prérequis ci-dessous)
python scripts/veille_digest.py
```

**Backup MongoDB** : lancer **après** `create_ia_copy.py` (le script envoie GOLD, GoldAI fusionné, jeux IA `train`/`val`/`test`, `gold_app_input`, prédictions si présentes, etc.). Prérequis : service Mongo up (ex. Docker `mongodb`) et **`MONGO_STORE_PARQUET=true`** dans `.env`. Sans Mongo, soit tu acceptes l’échec de cette étape (et tu arrêtes la chaîne si tu utilises `exit` sur erreur), soit tu entoures cette commande d’un avertissement sans `exit` pour enchaîner quand même la veille.

**Script tout-en-un (recommandé)** : depuis la racine du repo, `.\scripts\run_daily_pipeline.ps1` (paramètres `-SkipMongo`, `-SkipVeille`, `-TopicsFilter "finance,politique,meteo"` si besoin).

### 2.1 `python main.py` (E1)

- **SQLite** : insertion / mise à jour des articles et métadonnées (voir §3).
- **Exports fichier** (`src/e1/exporter.py`) :

| Couche | Emplacement |
|--------|-------------|
| RAW (snapshot CSV) | `exports/raw.csv` |
| SILVER | `data/silver/date=YYYY-MM-DD/silver_articles.parquet` (+ `.csv` si données) |
| GOLD | `data/gold/date=YYYY-MM-DD/articles.parquet` (+ `articles.csv`) |
| GOLD (sous-partitions ZZDB si présentes) | `data/gold/date=.../source=zzdb_synthetic/`, `source=zzdb_csv/` |

- **Métriques Prometheus (E1)** : port **8000** (`metrics_port` dans les settings) — message console en fin de run.
- **Logs** : §5.

### 2.2 `python scripts/merge_parquet_goldai.py`

Lit `data/gold/date=*`, alimente **GoldAI** (`goldai_base_path`, défaut `data/goldai`) :

| Fichier / dossier | Rôle |
|-------------------|------|
| `data/goldai/date=YYYY-MM-DD/goldai.parquet` | Partition journalière GoldAI |
| `data/goldai/merged_all_dates.parquet` | Fusion globale |
| `data/goldai/metadata.json` | Dates incluses, version, totaux |
| `data/goldai/merged_all_dates_vN.parquet` | Sauvegardes de version (si générées) |

### 2.3 `python scripts/build_gold_branches.py`

| Sortie | Rôle |
|--------|------|
| `data/goldai/app/gold_app_input.parquet` | Entrée **app / inférence** |
| `data/goldai/ia/gold_ia_labelled.parquet` | Jeu **labelisé** pour ML |

### 2.4 `python scripts/create_ia_copy.py`

| Sortie | Rôle |
|--------|------|
| `data/goldai/ia/merged_all_dates_annotated.parquet` | Copie annotée |
| `data/goldai/ia/train.parquet`, `val.parquet`, `test.parquet` | Splits entraînement / validation / test |

### 2.5 `python scripts/veille_digest.py`

| Sortie | Rôle |
|--------|------|
| `docs/veille/veille_YYYY-MM-DD.md` | Digest lisible |
| `docs/veille/veille_YYYY-MM-DD.json` | Snapshot structuré |

### 2.6 Inférence ML (hors chaîne ci-dessus, quand exécutée)

Exemple de convention :

```text
data/goldai/predictions/date=YYYY-MM-DD/run=*/predictions.parquet
```

Exports optionnels liés à Mistral (selon scripts lancés) : `data/goldai/mistral_input.json`, `data/goldai/mistral_insights.json`.

---

## 3. SQLite (`datasens.db`)

| Sujet | Détail |
|-------|--------|
| **Chemin par défaut (Windows)** | `%USERPROFILE%\datasens_project\datasens.db` (ex. `C:\Users\Utilisateur\datasens_project\datasens.db`) |
| **Surcharge** | Variable d’environnement **`DB_PATH`** (E1, E2 `DataService`, routes `sources`, middleware d’audit) |
| **Rôle** | Source de vérité **opérationnelle** E1 : sources, articles bruts, tagging, sorties modèles légers, profils utilisateurs, journal d’actions API si table présente |
| **Note** | Un `datasens.db` à la racine du repo peut exister mais n’est pas forcément la base « réelle » du run quotidien ; vérifier `DB_PATH` |

---

## 4. MongoDB — stockage long terme (GridFS)

| Sujet | Détail |
|-------|--------|
| **Rôle métier** | **Tier d’archivage long terme** : les Parquet (GOLD, GoldAI, jeux IA, prédictions sauvegardées, etc.) sont poussés dans **GridFS** pour durabilité, centralisation et restauration — complément du disque local, pas un simple « gadget » |
| **Rôle technique** | Le run E1 **n’écrit pas** dans Mongo tout seul ; l’archivage se fait via **`scripts/backup_parquet_to_mongo.py`** (et config `.env`). Tant que ce n’est pas lancé / Mongo est arrêté, seuls SQLite + Parquet locaux sont à jour |
| **Variables** | `MONGO_URI` (défaut `mongodb://localhost:27017`), `MONGO_DB` (défaut `datasens`), `MONGO_GRIDFS_BUCKET` (défaut `parquet_fs`), `MONGO_STORE_PARQUET` |
| **Scripts** | `scripts/backup_parquet_to_mongo.py` (upload), `scripts/list_mongo_parquet.py` (inventaire) |
| **Docker** | Service `mongodb` dans `docker-compose.yml`, volume persistant **`mongodb-data`** |
| **ZZDB** | Certaines sources peuvent **lire** Mongo en acquisition ; distinct du rôle **GridFS** pour l’archivage Parquet |

---

## 5. Logs

| Élément | Emplacement / comportement |
|---------|------------------------------|
| Fichier principal | `logs/datasens.log` (à la racine du projet, rotation ~10 Mo, rétention ~7 jours) |
| Configuration | `src/logging_config.py`, `log_file` / `log_level` dans `src/config.py` |
| Console | Sortie standard avec format horodaté (Loguru) |

---

## 6. Formulation courte (oral)

> Le run **E1** alimente **SQLite** (opérationnel) et produit des **Parquet/CSV** (couche analytique sur disque). **merge_parquet_goldai** consolide vers **GoldAI**, **build_gold_branches** sépare **app** et **IA**, **create_ia_copy** prépare **train/val/test**. L’**API E2** expose **RAW / SILVER / GOLD**, l’**analytics** sur Parquet et l’**IA** sous `/api/v1/ai`, avec **`/health`** et **`/metrics`**. **MongoDB GridFS** est le **stockage long terme** des Parquet (archivage), activé par script et infra Docker. Les **logs** sont dans **`logs/datasens.log`**.

---

*Dernière mise à jour : généré pour le dépôt DataSens (documentation projet).*
