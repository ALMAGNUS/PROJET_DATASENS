# RUNBOOK — DataSens

> Document opérationnel unique. Tout ce qu'il faut pour **lancer**, **dépanner**,
> **sauvegarder**, **mettre à jour** et **sécuriser** la plateforme. Lecture en 10
> minutes, exploitation au quotidien.
>
> Public cible : développeur ou ops qui doit faire tourner la stack. Le **README**
> répond à *« qu'est-ce que c'est ? »*, ce RUNBOOK répond à *« comment je
> l'opère ? »*. Pas de redite : le RUNBOOK détaille, le README résume.
>
> Toutes les commandes s'exécutent depuis la **racine du projet** (dossier
> contenant `main.py`, `docker-compose.yml`, `start_full.bat`).

---

## Sommaire

1. [Inventaire des services](#1-inventaire-des-services)
2. [Premier démarrage — clone → stack opérationnelle](#2-premier-démarrage--clone--stack-opérationnelle)
3. [Lancement quotidien](#3-lancement-quotidien)
4. [Scénarios standardisés](#4-scénarios-standardisés)
5. [URLs et accès](#5-urls-et-accès)
6. [Comptes et accès cockpit](#6-comptes-et-accès-cockpit)
7. [MongoDB — local natif vs container](#7-mongodb--local-natif-vs-container)
8. [Backup et restauration](#8-backup-et-restauration)
9. [Mise à jour du projet](#9-mise-à-jour-du-projet)
10. [Logs et incidents](#10-logs-et-incidents)
11. [Tests, qualité, CI](#11-tests-qualité-ci)
12. [Sécurité opérationnelle (RGPD inclus)](#12-sécurité-opérationnelle-rgpd-inclus)
13. [Performance et tuning](#13-performance-et-tuning)
14. [Dépannage par symptôme](#14-dépannage-par-symptôme)
15. [Références](#15-références)

---

## 1. Inventaire des services

| Service | Port | Rôle | Lancement | Dépendances |
|---|---|---|---|---|
| **Pipeline E1** | — (batch) | Extraction → SILVER → GOLD → GoldAI | `python main.py` | SQLite |
| **Métriques E1 (Prometheus)** | 8000 | Exporter `e1_*` (runs, deltas, durations) | `python scripts/run_e1_metrics.py` | SQLite |
| **API E2 (FastAPI)** | 8001 | REST authentifié JWT/RBAC sur RAW/SILVER/GOLD | `python run_e2_api.py` | SQLite (`profils`) |
| **Métriques E2 (Prometheus)** | 8001/metrics | Exporter `http_*`, `auth_*`, `db_*` | (intégré API) | API E2 active |
| **Cockpit Streamlit** | 8501 | UI : run, lineage, démo, IA | `streamlit run src/streamlit/app.py` ou `start_cockpit.bat` | API E2 |
| **MongoDB** | 27017 | GridFS backup parquet + sync_log | `docker compose up -d mongodb` *ou* service Windows natif (cf. § 7) | — |
| **Prometheus** | 9090 | Scrape métriques E1 + E2 | `start_prometheus.bat` ou `docker compose up -d prometheus` | E1/E2 metrics actifs |
| **Grafana** | 3000 | Dashboards | `start_grafana.bat` ou `docker compose up -d grafana` | Prometheus |
| **Uptime Kuma** | 3001 | Monitoring externe | `docker compose up -d uptime-kuma` | — |

**Note sur les 2 endpoints metrics** : l'**E1** expose un serveur dédié sur `:8000`
(géré par `prometheus_client`), l'**E2** intègre les métriques directement dans
l'app FastAPI (`:8001/metrics`). Prometheus scrape les deux séparément.

---

## 2. Premier démarrage — clone → stack opérationnelle

À faire **une seule fois** sur un poste neuf. Compte ~15 minutes (sans modèle HuggingFace).

### 2.1 Cloner et installer

```bat
git clone https://github.com/ALMAGNUS/PROJET_DATASENS.git
cd PROJET_DATASENS
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2.2 Configurer `.env`

```bat
copy .env.example .env
```

Éditer `.env` et remplir au minimum :

```env
DB_PATH=C:/Users/<TON_NOM>/datasens_project/datasens.db
MISTRAL_API_KEY=<ta_clé>            # facultatif, sinon E3 désactivé
HUGGINGFACE_API_KEY=<ta_clé>        # facultatif
OPENWEATHERMAP_API_KEY=<ta_clé>     # sinon fallback Open-Meteo
INSEE_CLIENT_ID=...                 # facultatif, sinon fallback HTML public
INSEE_CLIENT_SECRET=...
```

`.env` est ignoré par Git (cf. `.gitignore` : `.env*` sauf `.env.example`).

### 2.3 Initialiser la base SQLite

```bat
python scripts/setup_with_sql.py
python scripts/init_profils_table.py
```

### 2.4 Créer ton compte admin

```bat
python scripts/create_user.py admin@datasens.fr "<MotDePasseFort>" --role admin
```

### 2.5 Première exécution du pipeline

```bat
python main.py
```

Durée typique : 60-120 s. Génère `data/raw/`, `data/silver/`, `data/gold/`,
`data/goldai/`, et alimente la table `raw_data` (~50-200 articles selon les
flux).

### 2.6 Vérifier la stack

```bat
python scripts/db_state_report.py
```

Le rapport `reports/db_state_*.{md,json}` doit afficher `coherence: OK`.

### 2.7 Démarrer cockpit + API

```bat
lancer_tout.bat
```

→ http://localhost:8501. Connexion avec le compte de § 2.4.

---

## 3. Lancement quotidien

Pour un poste **déjà installé** :

```bat
lancer_tout.bat
```

Démarre :
1. Prometheus + Grafana via Docker (si Docker Desktop répond),
2. terminal dédié pour l'API E2,
3. terminal dédié pour le cockpit Streamlit.

→ http://localhost:8501. Tout le reste est en background.

Pour un run pipeline manuel : `python main.py` (sans tout relancer).

### 3.1 Publication quotidienne des rapports sur GitHub

Les fichiers `reports/db_state_*` et `reports/run_summary_*` doivent être **commités et poussés**
pour que le jury voie les preuves à jour (GitHub trie le dossier par nom de fichier, pas par date :
le plus récent est en bas de la liste, ex. `db_state_2026-05-18T062650Z.md`).

**Une commande (pipeline + rapport + push)** :

```bat
scripts\daily_pipeline_and_publish.bat
```

**Ou après un run déjà fait** :

```bat
python scripts\db_state_report.py --publish-git
```

```bat
scripts\publish_reports_git.bat
```

**Planificateur de tâches Windows** (ex. tous les jours à 07:00) :

1. Action : `C:\Users\Utilisateur\Desktop\PROJET_DATASENS\scripts\daily_pipeline_and_publish.bat`
2. Démarrer dans : racine du projet
3. Compte avec accès Git (credentials GitHub déjà configurés : `git push` sans mot de passe interactif)

Prérequis : `.venv` activable, `git` en PATH, branche `main` suivie par `origin`.

### 3.2 CI GitHub Actions — erreurs fréquentes

| Message | Cause | Action |
|---------|--------|--------|
| `could not read Username for 'https://github.com'` | Token / permissions checkout | Corrigé dans les workflows (`permissions: contents: read`, `github.token`). |
| `Too Many Requests` / `Failed to resolve action download info` | Limite interne GitHub (téléchargement des actions) | Attendre **15–60 min**, **Re-run** le job. Les pushes qui ne touchent que `reports/` ou `docs/` **ne déclenchent plus** la CI (paths-ignore). |
| CI rouge mais dépôt OK pour le jury | La soutenance ne dépend pas d’Actions vertes | Les liens `src/`, `docs/`, `reports/` sur GitHub restent valides. |

Relancer manuellement : onglet **Actions** → workflow **DataSens E1 CI/CD Pipeline** → **Run workflow**.

---

## 4. Scénarios standardisés

### Scénario A — Stack complète via Docker Compose

**Prérequis** : Docker Desktop installé et `docker info` répond.

```bat
docker compose up -d
```

Démarre 7 services : `datasens-e1`, `datasens-e1-metrics`, `datasens-e2-api`,
`datasens-mongodb`, `datasens-prometheus`, `datasens-grafana`,
`datasens-uptime-kuma`.

Hors compose (UI locales) :
- `streamlit run src/streamlit/app.py` → http://localhost:8501

**Vérifications post-démarrage** :
- API : `curl http://localhost:8001/health`
- Métriques : `curl http://localhost:8001/metrics`
- Prometheus targets : http://localhost:9090/targets (toutes UP)
- Grafana : http://localhost:3000 (admin / admin)
- MongoDB : `docker exec datasens-mongodb mongosh --quiet --eval "db.adminCommand({ping: 1})"` → `{ ok: 1 }`

### Scénario B — Local sans Docker

Un terminal par service :

```bat
.venv\Scripts\activate.bat
python scripts/run_e1_metrics.py     :: optionnel
python run_e2_api.py
streamlit run src/streamlit/app.py
```

Monitoring local : `start_prometheus.bat` (binaire local), `start_grafana.bat`
(Docker requis pour Grafana). MongoDB → cf. § 7.

### Scénario C — Pipeline E1 seul (run quotidien batch)

```bat
python main.py
```

Variantes :
- `python main.py --keep-metrics` : garde le serveur de métriques actif après
- `python scripts/run_e1_metrics.py` (en parallèle, indépendant du run)
- `run_daily.ps1` (PowerShell scheduled task pour cron Windows)

### Scénario D — Fine-tuning local (CamemBERT / sentiment_fr)

```bat
scripts\run_training_loop_e2.bat               :: rapide (1 epoch, ~3000 train)
scripts\run_training_loop_e2.bat --full        :: complet (3 epochs, dataset complet)
```

Le wrapper enchaîne : copie IA train/val/test → fine-tuning → benchmark → figures.

Sorties (cf. § 11.5 « Tracking des entraînements ») :
- modèle final : `models/sentiment_fr-sentiment-finetuned/`
- métriques run : `docs/e2/TRAINING_RESULTS.json`
- benchmark multi-modèles : `docs/e2/AI_BENCHMARK_RESULTS.json`
- courbes : `docs/e2/figures/e2_training_<mode>_*.png`
- état HuggingFace Trainer : `models/.../trainer_state.json` (loss / eval par step)

Alternative GPU gratuite : `notebooks/colab_finetune_sentiment.ipynb`
(courbes loss / F1 visibles inline via TensorBoard, cf. § 11.5).
**Chemins des données / zip / réinjection** : sous-section **« Colab (Google) »** juste après ce scénario.

Réinjection du modèle Colab dans le pipeline local :

```bat
python scripts/install_colab_model.py <archive_telechargee.zip>
```

### Colab (Google) — fichiers d’entrée, artefacts et inférence locale

Notebook : `notebooks/colab_finetune_sentiment.ipynb`. Résumé des chemins pour une réponse orale ou une démo reproductible.

#### Ce qui est **produit en local** avant Colab

Après fusion GoldAI et split IA (`python scripts/create_ia_copy.py`), avec le défaut
`goldai_base_path=data/goldai` (`src/config.py`) :

| Fichier | Rôle |
|---|---|
| `data/goldai/ia/train.parquet` | Jeu d’entraînement |
| `data/goldai/ia/val.parquet` | Validation pendant le training |
| `data/goldai/ia/test.parquet` | Évaluation finale (hors training) |
| `data/goldai/ia/merged_all_dates_annotated.parquet` | Copie annotée après filtres (même run) |

Source du split : `data/goldai/ia/gold_ia_labelled.parquet` si présent, sinon
`data/goldai/merged_all_dates.parquet` (cf. script).

#### Ce que tu **uploades dans Colab**

Un **zip** contenant **à la racine du zip** les trois Parquet (noms exacts) :

- `train.parquet`
- `val.parquet`
- `test.parquet`

Le notebook les extrait sous `./data/` puis lit `data/train.parquet`, etc. Le nom du zip est libre ; la doc du notebook parle de `colab_bundle.zip`. Tu peux fabriquer l’archive à la main ou avec PowerShell depuis la racine du projet :

```powershell
Compress-Archive -Force -Path `
  data\goldai\ia\train.parquet, `
  data\goldai\ia\val.parquet, `
  data\goldai\ia\test.parquet `
  -DestinationPath exports\colab_bundle.zip
```

Le dossier `exports/` est **gitignored** : pratique pour les zip, pas versionné Git.

#### Ce que **génère Colab** (runtime notebook)

| Élément | Chemin côté Colab | Contenu |
|---|---|---|
| Modèle fine-tuné | `models/sentiment_fr-finetuned-colab/` | `config.json`, tokenizer, `model.safetensors` ou `pytorch_model.bin`, checkpoints éventuels |
| TensorBoard | `models/sentiment_fr-finetuned-colab/runs/` | Events HF (`report_to='tensorboard'`) |
| Métriques test | `models/sentiment_fr-finetuned-colab/test_metrics.json` | JSON écrit en cellule d’évaluation |
| Archive téléchargée | **`sentiment_fr_finetuned_colab.zip`** (racine Colab) | Zip du dossier `OUT_DIR` (cellule `make_archive` + `files.download`) |

#### Après téléchargement — **réinjection** et **inférence**

```bat
python scripts\install_colab_model.py chemin\vers\sentiment_fr_finetuned_colab.zip
```

Comportement par défaut du script :

- extraction vers `models/sentiment_fr-finetuned-colab/`
- mise à jour de `.env` : `SENTIMENT_FINETUNED_MODEL_PATH=models/sentiment_fr-finetuned-colab`

L’API et le cockpit chargent ce modèle via **`SENTIMENT_FINETUNED_MODEL_PATH`**
(`src/ml/inference/local_hf_service.py`). Redémarrer l’API après changement de `.env`.

**TensorBoard en local** (après réinjection) : voir § 11.5 ; en pratique
`tensorboard --logdir models/sentiment_fr-finetuned-colab/runs`.

**Historique run local (sans Colab)** : `docs/e2/TRAINING_RESULTS.json` — distinct du zip Colab.

#### Workflow bout en bout — **modèle HF** vs **Mistral** (clarification des rôles)

**À distinguer absolument** :

| Besoin | Technologie | Où c’est branché |
|---|---|---|
| Score de sentiment (ton fine-tune CamemBERT/HF) | **Hugging Face local** (`LocalHFService`) | `.env` → `SENTIMENT_FINETUNED_MODEL_PATH` → dossier sous `models/` |
| Chat, résumé, assistant insight | **Mistral** (API cloud) | `.env` → `MISTRAL_API_KEY` — **aucun fichier modèle** Mistral dans le dépôt |

Mistral **ne lit pas** `models/sentiment_fr-finetuned-colab/` : c’est un LLM génératif ; il reçoit du **texte de contexte** construit côté API (`src/e2/api/routes/ai.py`, fonction `_build_data_context`).

**Ce qu’on « réinjecte » après Colab** : uniquement l’**archive du modèle HF** (`install_colab_model.py`). Les Parquet `train/val/test` ne sont **pas** réimportés — ils étaient déjà produits localement (`data/goldai/ia/`) avant l’upload vers Colab.

**Inférence en masse** (pour alimenter les stats que Mistral résume) :

1. Après réinjection du modèle et redémarrage API, lancer le batch :
   ```bat
   python scripts\run_inference_pipeline.py
   ```
2. Sortie typique : `data/goldai/predictions/date=*/run=*/predictions.parquet`
3. L’endpoint `POST /api/v1/ai/insight` préfère fusionner `data/goldai/app/gold_app_input.parquet` avec le **dernier** `predictions.parquet` ; sinon repli sur `data/goldai/merged_all_dates.parquet`.

Schéma synthétique :

```
Pipeline E1 → GOLD / GoldAI
       │
       ├─ create_ia_copy.py → data/goldai/ia/{train,val,test}.parquet ──zip──► Colab (train)
       │
       ◄──────────────── sentiment_fr_finetuned_colab.zip ────────────────
       │
       └─ install_colab_model.py → models/sentiment_fr-finetuned-colab/ + .env

run_inference_pipeline.py (batch) → data/goldai/predictions/.../predictions.parquet
                                              │
_build_data_context (résumé texte des Parquet) │
                                              ▼
                                    prompt ──► Mistral (insight)

POST /ai/predict (texte seul) ──► LocalHF (même SENTIMENT_FINETUNED_MODEL_PATH) — sans Mistral
```

**Phrases courtes (oral)** :

- *« Le fine-tune produit des poids Hugging Face ; Mistral ne les voit pas — il reçoit un résumé statistique issu des Parquet, enrichi si on a lancé l’inférence batch. »*
- *« L’inférence « temps réel » sur une phrase passe par `/predict` ; l’insight Mistral s’appuie sur les agrégats construits depuis GoldAI + prédictions batch. »*

### Scénario E — Cockpit + API uniquement (démo rapide)

```bat
start_full.bat
```

Démarre l'API et le cockpit dans deux terminaux dédiés. Ne touche **pas**
Docker, MongoDB, ni le monitoring. Idéal pour démonstration locale.

---

## 5. URLs et accès

| Service | URL | Authentification |
|---|---|---|
| Cockpit | http://localhost:8501 | comptes SQLite `profils` (cf. § 6) |
| API E2 (Swagger) | http://localhost:8001/docs | bearer token via `POST /auth/login` |
| API E2 (health) | http://localhost:8001/health | — |
| Métriques E1 | http://localhost:8000/metrics | — |
| Métriques E2 | http://localhost:8001/metrics | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | `admin / admin` (à changer en prod) |
| Uptime Kuma | http://localhost:3001 | initialisé au premier login |

---

## 6. Comptes et accès cockpit

### 6.1 Inventaire des comptes seedés

| Email | Rôle | Origine | Sort |
|---|---|---|---|
| `admin@datasens.fr` | `admin` | Créé manuellement via `scripts/create_user.py` | **ton compte d'usage** |
| `reader@datasens.test` | `reader` | Démo RBAC documentée dans `docs/README_E2_API.md` | optionnel, gardé pour démo |
| `test@example.com` | `reader` | **Recréé à chaque run pytest** par `tests/test_e2_api.py` | **NE PAS SUPPRIMER** (sinon CI rouge) |

### 6.2 Lister les comptes

```bat
python scripts/change_password.py --list
```

Sortie : email, rôle, statut actif, dernier login. Aucun mot de passe affiché
(bcrypt = irréversible).

### 6.3 Changer un mot de passe

```bat
python scripts/change_password.py admin@datasens.fr
```

Le script demande la nouvelle valeur **deux fois** en saisie masquée. Met à
jour `password_hash` (bcrypt) et `updated_at`.

> **Important — saisie masquée** : pendant la frappe, **rien ne s'affiche**
> (pas de point, pas d'astérisque). C'est le comportement standard de `getpass`.
> Tape ton mot de passe au clavier puis Entrée.

> **Si le terminal ne répond pas** (cas Cursor / VSCode integrated, certains
> conteneurs Docker) : `getpass` peut bloquer car le terminal n'est pas un
> vrai TTY. **Solution** : ouvrir un PowerShell séparé (`Win+R` → `powershell`),
> activer le venv, relancer la commande.

### 6.4 Créer un nouveau compte

```bat
python scripts/create_user.py <email> <password> --role admin
```

Rôles disponibles : `reader`, `writer`, `deleter`, `admin` (cf. CHECK constraint
de la table `profils`). Le `username` est dérivé automatiquement de l'email
(partie avant `@`).

> **Évite de mettre le mot de passe en argument CLI** (apparaît dans
> l'historique PowerShell). Préférer `python scripts/create_user.py <email>`
> sans argument → saisie masquée.

### 6.5 Désactiver un compte (sans le supprimer)

```bat
python -c "import sqlite3; from src.config import get_settings; conn=sqlite3.connect(get_settings().db_path); conn.execute('UPDATE profils SET active=0 WHERE email=?', ('user@example.com',)); conn.commit()"
```

Conserve l'historique d'audit (`user_action_log`) tout en bloquant la connexion.

### 6.6 Rôles RBAC

| Rôle | RAW | SILVER | GOLD | Endpoint admin |
|---|---|---|---|---|
| `reader` | — | — | lecture | — |
| `writer` | — | lecture + écriture | lecture | — |
| `deleter` | — | lecture + écriture + suppression | lecture | — |
| `admin` | lecture | lecture + écriture + suppression | lecture | accès complet |

L'**API E2 ne mute jamais SILVER** (HTTP 501 par design, isolation E1).
L'écriture SILVER passe exclusivement par le pipeline E1.

---

## 7. MongoDB — local natif vs container

`docker-compose.yml` orchestre `mongo:7` comme livrable production. Sur poste
de dev Windows, deux options selon l'état de Docker Desktop :

**Container Docker** :

```bat
docker compose up -d mongodb
docker exec datasens-mongodb mongosh --quiet --eval "db.adminCommand({ping: 1})"
```

**Service Windows natif** (fallback fiable si Docker Desktop instable) :

```powershell
winget install MongoDB.Server -v 7.0.28 -e --accept-source-agreements --accept-package-agreements
Start-Service MongoDB
```

Dans les deux cas l'URI reste `mongodb://localhost:27017`. Le cockpit et le
code applicatif ne voient pas la différence.

**Credentials** (si activés dans `.env`) : `MONGO_USER`, `MONGO_PASSWORD`,
`MONGO_AUTH_SOURCE`. La méthode `_build_mongo_uri_from_env` les injecte
automatiquement dans l'URI côté code.

---

## 8. Backup et restauration

### 8.1 Quoi sauvegarder ? Criticité

| Artefact | Chemin | Criticité | Reproductible ? |
|---|---|---|---|
| **SQLite** (source de vérité buffer) | `~/datasens_project/datasens.db` | **critique** | non (perdrait l'historique RAW) |
| **Comptes utilisateurs** | table `profils` (dans SQLite) | **critique** | non |
| **Audit trail** | table `user_action_log` (dans SQLite) | **critique** | non |
| **Parquet GoldAI consolidé** | `data/goldai/merged_all_dates.parquet` | sensible | oui via main.py mais long (~5 min/date) |
| **Splits IA train/val/test** | `data/goldai/ia/{train,val,test}.parquet` | sensible | oui via `scripts/create_ia_copy.py` |
| **Modèles fine-tunés** | `models/finetuned/` | sensible | oui via `scripts\run_training_loop_e2.bat` |
| **Tracking entraînements** | `docs/e2/TRAINING_RESULTS.json` + `AI_BENCHMARK_RESULTS.json` (versionnés Git) | utile | oui via Git |
| **Rapports d'audit** | `reports/db_state_*`, `run_summary_*` | utile | non |
| **GridFS MongoDB** | `mongodb://.../parquet_fs` | utile (backup) | oui |

### 8.2 Backup Parquet → GridFS (long terme)

```bat
python scripts/backup_parquet_to_mongo.py
```

Sauvegarde tous les Parquet GOLD quotidiens, GoldAI consolidé, splits IA et
prédictions vers MongoDB GridFS. Idempotent (skip les fingerprints déjà
présents). Log : `logs/backup_mongo_<timestamp>.log`.

### 8.3 Restauration depuis GridFS

```bat
python scripts/download_from_mongo_gridfs.py <fingerprint_ou_nom_logique>
```

Exemple :

```bat
python scripts/download_from_mongo_gridfs.py goldai_merged
python scripts/download_from_mongo_gridfs.py gold_articles_2026-05-08
```

Récupère le Parquet et le rend disponible localement.

### 8.4 Backup SQLite ad-hoc

SQLite a une commande native, atomique, hot-copy :

```bat
sqlite3 %USERPROFILE%\datasens_project\datasens.db ".backup datasens_backup_%DATE%.db"
```

Restauration : remplacer le fichier `datasens.db` (cockpit et API arrêtés).

---

## 9. Mise à jour du projet

```bat
git pull
.venv\Scripts\activate
pip install -r requirements.txt
```

**Si conflit NumPy / bottleneck / scipy** après `pip install` :

```bat
scripts\fix_venv.bat
```

(Ferme Cursor et tous les terminaux avant : Windows verrouille les `.dll` chargés.)

**Migrations de schéma SQLite** : aucune migration automatique, le projet
applique les `CREATE TABLE IF NOT EXISTS` au démarrage. Si une nouvelle table
apparaît dans `scripts/setup_with_sql.py`, relancer le script.

**Vérification post-update** :

```bat
pytest tests/ --ignore=tests/test_spark_integration.py
ruff check src/ scripts/
python scripts/db_state_report.py
```

Attendu : 52 tests passed, 0 ruff issue, coherence OK.

---

## 10. Logs et incidents

### 10.1 Où chercher quand ça plante ?

| Symptôme | Fichier à consulter |
|---|---|
| Pipeline E1 plante / ne ramène rien | `logs/datasens.log` (dernier `==== Pipeline run ====`) |
| Cockpit ou Streamlit error | `error_logs/` (si activé) puis console qui tourne `streamlit run` |
| API E2 plante | console qui tourne `python run_e2_api.py` (uvicorn stack trace) |
| Backup MongoDB échoue | `logs/backup_mongo_<ts>.log` |
| MongoDB native install échoue | `logs/mongodb_install*.log` |
| Entraînement fine-tuning | `models/<run>/trainer_state.json` (loss/eval/step), `docs/e2/TRAINING_RESULTS.json` (résultats finaux), `docs/e2/figures/` (courbes PNG) |
| Run pipeline résumé | `reports/run_summary_<ts>.json` (statut PASS/WARN/FAIL) |
| Cohérence base | `reports/db_state_<ts>.{md,json}` |

### 10.2 Premier réflexe en incident

1. **Identifier la couche** : pipeline / API / cockpit / monitoring / DB ?
2. **Logs récents** : `Get-Content logs/datasens.log -Tail 100` (PowerShell).
3. **Health checks** :
   - `curl http://localhost:8001/health` → API
   - `curl http://localhost:8001/metrics` → exporter
   - Cockpit sidebar → indicateurs API ON / OFF
4. **Si Docker en cause** : `docker compose ps`, `docker compose logs -f <service>`.
5. **Si DB en cause** : `python scripts/db_state_report.py` (cohérence).
6. **Restart isolé** plutôt que tout redémarrer : un service à la fois.

### 10.3 Configuration logging

`loguru` configuré dans `src/__init__.py`. Détails : [`docs/dev/LOGGING.md`](docs/dev/LOGGING.md).

---

## 11. Tests, qualité, CI

### 11.1 Tests locaux

```bat
pytest tests/ -v                                       :: full
pytest tests/ --ignore=tests/test_spark_integration.py :: hors Spark integration
pytest tests/test_e2_api.py -v                         :: ciblé
```

Attendu : **52 passed, 0 failed** (hors test_spark_integration qui requiert
un cluster externe).

### 11.2 Lint

```bat
ruff check src/ scripts/
ruff check --fix src/ scripts/                  :: auto-fix safe
ruff check --fix --unsafe-fixes src/ scripts/   :: auto-fix agressif
run_ruff.bat                                    :: wrapper Windows
```

Attendu : **0 issue**. Configuration dans `pyproject.toml` (RUF002 ignoré pour
typographie française).

### 11.3 Quality gate E3

```bat
python scripts/run_e3_quality_gate.py
```

Vérifie cohérence Spark / Mistral / dataset structure.

### 11.4 Drift modèle — rafraîchissement automatique

Le drift est calculé par `GET /api/v1/analytics/drift-metrics` (zone Gold + fallback
pandas si Spark down) et **alimente 4 gauges Prometheus** : `datasens_drift_score`,
`datasens_drift_sentiment_entropy`, `datasens_drift_topic_dominance`,
`datasens_drift_articles_total`. L'alerte `DriftScoreHigh` (cf.
`monitoring/prometheus_rules.yml`) se déclenche si `drift_score > 0.7` pendant 15 min.

**Sans déclencheur, les gauges restent à 0** : Prometheus scrape les valeurs
exposées, mais l'endpoint ne se calcule qu'à la demande. 3 mécanismes alimentent
les gauges automatiquement :

#### 11.4.1 Setup une fois — compte de service

```bat
python scripts/setup_drift_refresh_account.py
```

Crée le compte `drift-refresh@datasens.local` (rôle `reader`), génère un mot de
passe aléatoire et l'écrit dans `.env` (clés `DRIFT_REFRESH_EMAIL` et
`DRIFT_REFRESH_PASSWORD`). Voir `scripts/setup_drift_refresh_account.py --help`
pour `--regenerate` (rotation) ou `--password` (mdp explicite).

Test :

```bat
python scripts/refresh_drift_metrics.py
:: → [drift-refresh] OK — drift_score=0.43 entropy=0.92 dominance=0.31 articles=51495
```

Si l'API E2 est down, le script log et sort en 0 (best-effort, ne casse rien).

#### 11.4.2 Mécanisme 1 — fin de pipeline (`main.py`)

Modifié pour appeler automatiquement `scripts/refresh_drift_metrics.py --quiet`
après chaque run pipeline réussi, **uniquement si `DRIFT_REFRESH_PASSWORD`** est
défini dans `.env`. Timeout 20 s, jamais bloquant.

Vérification :

```bat
python main.py
:: ... pipeline log ...
type logs\datasens.log | findstr "Drift gauges"
:: → INFO   - Drift gauges Prometheus rafraîchies (API E2)
```

#### 11.4.3 Mécanisme 2 — cockpit (auto au chargement)

L'onglet **Pilotage & Ops** contient un panneau "Drift modèle (Prometheus +
Grafana)" qui :

- appelle `/drift-metrics` à l'ouverture (cache TTL 60 s pour ne pas spam) ;
- affiche les 4 valeurs avec un statut couleur (🟢 / 🟠 / 🔴 selon le score) ;
- propose un bouton "Rafraîchir maintenant" pour forcer ;
- pointe vers le dashboard Grafana correspondant.

Le cockpit utilise le token JWT de l'utilisateur connecté (pas le compte de
service). Aucune configuration supplémentaire requise.

#### 11.4.4 Mécanisme 3 — manuel (curl ou Swagger)

Pour debug ou démo flash :

```bat
:: 1. login
curl -X POST http://localhost:8001/auth/login ^
  -d "username=admin@datasens.fr&password=<MOT_DE_PASSE>"
:: → recupere "access_token": "eyJ..."

:: 2. drift refresh
curl -H "Authorization: Bearer <TOKEN>" ^
  "http://localhost:8001/api/v1/analytics/drift-metrics?target_date=2026-05-08"
```

Ou via Swagger : http://localhost:8001/docs → `POST /auth/login` → "Authorize" →
`GET /api/v1/analytics/drift-metrics`.

#### 11.4.5 Vérifier que Grafana voit le drift

```bat
:: 1. la stack monitoring tourne
docker compose up -d prometheus grafana

:: 2. forcer un refresh (un des 3 mecanismes ci-dessus)

:: 3. verifier l'expo Prometheus
curl http://localhost:8001/metrics | findstr datasens_drift
:: → datasens_drift_score 0.4321
:: → datasens_drift_sentiment_entropy 0.9214
:: → ...

:: 4. ouvrir Grafana
:: → http://localhost:3000 (admin/admin)
:: → Dossier "DataSens" → "DataSens – Metriques & Drift"
```

Le panneau "Drift – Score composite" doit afficher la dernière valeur, et la
courbe "Courbes de drift" se remplit après plusieurs scrapes Prometheus
(intervalle 15 s par défaut).

#### 11.4.6 Que faire si drift_score ≥ 0.7

L'alerte Prometheus `DriftScoreHigh` se déclenche. Procédure :

1. **Vérifier la cause** : ouvrir le cockpit, onglet Pilotage → panneau Drift.
   Regarder l'entropy (descend = sentiment uniforme) et la dominance (monte =
   un topic écrase les autres).
2. **Si une seule classe domine** (ex. tout en `negatif`) : vérifier
   `data/goldai/merged_all_dates.parquet` — anomalie de scraping ou source qui
   a basculé.
3. **Si la distribution est cohérente mais éloignée du training** : c'est un
   vrai drift, lancer un fine-tuning :

```bat
scripts\run_training_loop_e2.bat --full
```

4. **Recharger** le nouveau modèle dans `.env` (`SENTIMENT_FINETUNED_MODEL_PATH`)
   et redémarrer l'API.

### 11.5 Tracking des entraînements (ML)

**Choix architectural** : pas de MLflow. Le projet est mono-poste, sans serveur de
tracking dédié à maintenir. Le tracking se fait via **JSON versionnés Git** + état
HuggingFace Trainer + TensorBoard côté Colab.

| Source | Contenu | Lieu | Versionné Git |
|---|---|---|---|
| `docs/e2/TRAINING_RESULTS.json` | dernier run : loss train/eval, accuracy, F1 macro, F1 par classe, runtime, rebalance pos/neg | `docs/e2/` | oui |
| `docs/e2/AI_BENCHMARK_RESULTS.json` | benchmark multi-modèles (BERT multilingual, sentiment_fr, fine-tuned local, fine-tuned Colab) avec precision/recall/F1 par classe + latence | `docs/e2/` | oui |
| `docs/e2/figures/e2_training_<mode>_*.png` | courbes loss/F1 (matplotlib via `scripts/plot_e2_results.py`) | `docs/e2/figures/` | oui |
| `models/<run>/trainer_state.json` | log_history HF Trainer (loss + eval par step) | `models/` | non (gitignored) |
| `models/<run>/checkpoint-*/` | checkpoints intermédiaires HF | `models/` | non |
| Notebook Colab : `<OUT_DIR>/runs/` | events TensorBoard (loss / eval_loss / lr / accuracy / F1 par step) | dans le zip téléchargé | non |

**Visualiser les courbes Colab** :
- inline pendant le run (Cellule 6 du notebook) : `%tensorboard --logdir <OUT_DIR>/runs`
- en local après réinjection du zip : `tensorboard --logdir models/sentiment_fr-finetuned-colab/runs`

**Visualiser les courbes locales** : `docs/e2/figures/e2_training_*.png` (générés par
`scripts/plot_e2_results.py`, déjà appelés par `run_training_loop_e2.bat`).

**Quand passer à MLflow** (déclencheurs futurs, pas aujourd'hui) :
- > 1 personne entraîne en parallèle (besoin de comparer)
- besoin d'un Model Registry centralisé pour le déploiement
- comparaison fine de >10 runs (le JSON devient ingérable)

`mlflow==3.7.0` reste dans `requirements.txt` pour ne pas casser un environnement
existant, mais aucun code applicatif n'y logge. `mlruns/` est gitignored et inutile.

### 11.6 CI GitHub Actions

| Workflow | Déclencheur | Rôle |
|---|---|---|
| `.github/workflows/test.yml` | push + PR | pytest (E1 isolation / complet selon job) |
| `.github/workflows/ci-cd.yml` | push + PR | pytest + build/push image Docker `ghcr.io` |
| `.github/workflows/e3-quality-gate.yml` | push + PR | Quality gate E3 (`test_e3_quality_gate.py`) |

Statut consultable sur https://github.com/ALMAGNUS/PROJET_DATASENS/actions.

---

## 12. Sécurité opérationnelle (RGPD inclus)

### 12.1 Secrets — règles immuables

- **Jamais commiter `.env` ni `.env.freeze`**. `.gitignore` couvre `.env*`
  sauf `.env.example` (modèle sans secrets).
- **Vérification avant commit** :
  ```bat
  git ls-files | findstr /R "^\.env"
  ```
  Attendu : seulement `.env.example`.
- **Si fuite accidentelle** : rotation immédiate des clés concernées
  (Mistral, INSEE, HuggingFace, OpenWeather), `git filter-repo` pour purger
  l'historique, `git push --force` (avec validation explicite).

### 12.2 Rotation des secrets

| Secret | Procédure | Délai recommandé |
|---|---|---|
| `MISTRAL_API_KEY` | Console Mistral → générer nouvelle clé → mettre à jour `.env` → redémarrer API | trimestriel |
| `INSEE_CLIENT_SECRET` | Portail INSEE → renouveler → `.env` → redémarrer | annuel |
| `HUGGINGFACE_API_KEY` | Settings HuggingFace → revoke + new → `.env` | trimestriel |
| `MONGO_PASSWORD` | Voir § 12.3 | annuel |
| `JWT_SECRET_KEY` | `.env` → redémarrer API (invalide tous les tokens) | annuel ou sur incident |
| Mots de passe utilisateurs | `python scripts/change_password.py` | sur demande |

### 12.3 Rotation MongoDB password

```javascript
// docker exec -it datasens-mongodb mongosh
use admin
db.changeUserPassword("root", "<nouveau_mot_de_passe>")
```

Puis mettre à jour `MONGO_PASSWORD` dans `.env` et redémarrer cockpit + API.

### 12.4 Audit trail

Toutes les actions API authentifiées sont tracées dans `user_action_log`
(profil_id, action_type, resource_type, action_date, ip_address).

Consultation :

```bat
python -c "import sqlite3; from src.config import get_settings; conn=sqlite3.connect(get_settings().db_path); print(*(r for r in conn.execute('SELECT action_date, profil_id, action_type, resource_type FROM user_action_log ORDER BY action_date DESC LIMIT 50')), sep='\\n')"
```

### 12.5 RGPD — suppression d'un utilisateur

Pour supprimer toutes les traces d'un utilisateur (droit à l'oubli) :

```sql
-- Désactiver d'abord
UPDATE profils SET active=0 WHERE email='user@example.com';

-- Anonymiser dans l'audit (préserve l'historique légal sans identifier)
UPDATE user_action_log SET ip_address=NULL WHERE profil_id IN (
  SELECT profil_id FROM profils WHERE email='user@example.com'
);

-- Supprimer le profil après période de rétention
DELETE FROM profils WHERE email='user@example.com';
-- (CASCADE supprime user_action_log lié)
```

Procédure complète : [`docs/AUDIT_E4_ECART.md`](docs/AUDIT_E4_ECART.md).

---

## 13. Performance et tuning

### 13.1 Verrou NumPy

`numpy>=2.1,<2.2` (cf. `requirements.txt`). `bottleneck`, `numexpr`, `scipy`
plus anciens cassent en 2.2.x. Si `pip install` propose une mise à jour vers
2.2 : refuser ou utiliser `scripts\fix_venv.bat`.

### 13.2 Spark sur Windows

`HADOOP_HOME` pointe sur `hadoop/` à la racine (`winutils.exe` inclus).
Configuration dans `src/spark/session.py`. Ne pas supprimer le dossier
`hadoop/`.

Pour passage en cluster : externaliser `HADOOP_HOME` et adapter
`SparkSession.builder.master(...)` vers le master du cluster.

### 13.3 Inférence batch

Variables `.env` :

```env
TORCH_NUM_THREADS=8         # CPU torch threads
INFERENCE_BATCH_SIZE=8      # batch tokenizer + forward
INFERENCE_MAX_LENGTH=256    # tronquage texte
TOKENIZERS_PARALLELISM=false  # anti-deadlock Windows tokenizers HF
```

`INFERENCE_BATCH_SIZE` : monter à 16 ou 32 si > 16 Go RAM, redescendre à 4
sur portable.

### 13.4 Quality gates

Seuils dans `.env`, déclenchent un statut `WARN` ou `FAIL` du run :

```env
MIN_LOADED_THRESHOLD=20         # nb minimum d'articles ingérés
MIN_CLEAN_RATIO=0.90            # ratio acceptable après nettoyage
MIN_ENRICHED_RATIO=0.95         # ratio acceptable après enrichissement
SOURCE_DROP_WARN_PCT=80         # % chute par source avant WARN
```

Résumé du run dans `reports/run_summary_<ts>.json`.

---

## 14. Dépannage par symptôme

### NumPy / bottleneck / scipy

> *« A module that was compiled using NumPy 1.x cannot be run in NumPy 2.2 »*

```bat
scripts\fix_venv.bat
```

Pour Docker : `docker compose build --no-cache`.

### Docker Desktop bloqué au démarrage

```powershell
taskkill /F /IM "Docker Desktop.exe" /T
wsl --shutdown
Start-Sleep -Seconds 5
& "C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker info --format "{{.ServerVersion}}"
```

Si toujours KO : basculer sur MongoDB natif (cf. § 7).

### Port déjà utilisé

Modifier le mapping dans `docker-compose.yml` :

```yaml
ports:
  - "8002:8000"   # remap externe
```

### MongoDB GridFS hors ligne dans le cockpit

1. `docker ps --filter name=datasens-mongodb` ou `Get-Service MongoDB`
2. `python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017/').admin.command('ping'))"`
3. Si OK : `python scripts/backup_parquet_to_mongo.py` pour repeupler
4. Recharger le cockpit, panneau `Vue d'ensemble → Lineage de la donnée`

### API renvoie 401 malgré login OK

1. Token expiré (durée par défaut courte) : refaire un `POST /auth/login`.
2. Mauvais rôle pour la route : vérifier le RBAC (§ 6.6).
3. Compte désactivé : `python scripts/change_password.py --list` → `ACTIF: non` ?
   → réactiver via SQL (cf. § 6.5 inversé : `active=1`).

### Cockpit ne montre aucun article

1. Pipeline jamais lancé : `python main.py`.
2. SQLite vide : `python scripts/db_state_report.py` → `articles: 0` ?
3. Mauvais `DB_PATH` dans `.env` : doit pointer sur le fichier `datasens.db`
   réel (pas le doublon vide à la racine).

### Pipeline ne ramène aucune ligne

1. Pas de connexion internet → RSS / API down.
2. Sources désactivées : `sources_config.json` → `"active": true` ?
3. Quality gate `MIN_LOADED_THRESHOLD` trop haut → run en `FAIL` mais articles bien chargés ?
   → `reports/run_summary_*.json` pour la cause exacte.

### Modèle HuggingFace non chargé

1. `SENTIMENT_FINETUNED_MODEL_PATH` dans `.env` pointe sur un dossier ou un repo HF valide ?
2. Pas internet → fallback `sentiment_keyword` (rule-based) actif. Vérifier dans
   le cockpit panneau `IA → Inférence`.
3. Réinstaller le modèle Colab : `python scripts/install_colab_model.py <archive.zip>`.

### `getpass` bloque dans terminal IDE

Sur Cursor / VSCode integrated terminal, `getpass.getpass()` peut ne pas
recevoir les frappes. Solution : ouvrir un PowerShell séparé (`Win+R` →
`powershell`), activer le venv, relancer la commande. Cf. § 6.3.

---

## 15. Références

### Carte des emplacements des fichiers (audit, soutenance)

Pour répondre à une demande du type *« montrez où se trouvent les fichiers du
projet »* : partir de la **racine** (`main.py`, `docker-compose.yml`), puis
enchaîner **données → code → preuves → config**. Pas besoin de lister 200
chemins : montrer **5 dossiers** suffit si chacun a une phrase claire.

#### Vue d’ensemble (phrase d’architecture)

> « Le flux est **RAW → SILVER → GOLD → GoldAI** sur disque, **SQLite** pour
> l’opérationnel et l’auth, **Parquet** pour l’analytique et le ML, **MongoDB /
> GridFS** pour l’archive longue durée, **FastAPI** pour l’exposition,
> **Streamlit** pour le pilotage. »

#### Tableau — où ouvrir l’explorateur / l’IDE

| Emplacement | Rôle (une phrase) |
|---|---|
| `data/raw/` | Données brutes par jour de collecte (JSON/CSV issus du pipeline E1). |
| `data/silver/` | Parquet nettoyé après validation. |
| `data/gold/date=*/` | Parquet GOLD partitionné par date. |
| `data/goldai/` | Fusion : `merged_all_dates.parquet`, partitions `date=*`, branches **`app/`** (inférence), **`ia/`** (train/val/test, `gold_ia_labelled`). |
| `data/goldai/predictions/` | Sorties batch du modèle local (`date=*/run=*/predictions.parquet`) — contexte pour l’insight Mistral. |
| **SQLite** (`DB_PATH` dans `.env`, ex. `~/datasens_project/datasens.db`) | Métier + auth : `raw_data`, `profils`, `sync_log`, audit — pas le stockage principal des gros Parquet. |
| `models/` | Poids Hugging Face (fine-tuné ou baseline) ; voir `SENTIMENT_FINETUNED_MODEL_PATH`. |
| `src/e1/` | Extraction, nettoyage, chargement pipeline. |
| `src/e2/api/` | FastAPI : routes, middleware Prometheus, audit. |
| `src/streamlit/` | Cockpit : pilotage, lineage, IA. |
| `src/ml/inference/` | Inférence locale HF (`LocalHFService`). |
| `monitoring/` | Prometheus, Grafana, règles d’alerte (MCO). |
| `reports/` | `run_summary_*.json` (contrat de run E1), `db_state_*` (cohérence). |
| `docs/` | Dossiers E2–E5, annexes, veille versionnée, schémas (`ARCHITECTURE`, `FLOW_DONNEES`). |
| `.github/workflows/` | CI : tests, quality gate, build image. |
| `notebooks/` | Notebook Colab fine-tuning (`colab_finetune_sentiment.ipynb`). |
| `presentations/` | Supports soutenance au format Marp (sources `.md`). |

#### MongoDB / GridFS (si on te le demande)

> « MongoDB sert d’**archive** : les Parquet volumineux sont envoyés dans **GridFS**
> via `scripts/backup_parquet_to_mongo.py`. Ce n’est pas la base métier du run
> quotidien : le pipeline lit surtout **disque + SQLite**. »

#### Astuce le jour J

Préparer dans l’explorateur ou l’IDE trois favoris : **`data/goldai`**, **`reports`**, **`src/e2/api`** — en moins d’une minute on couvre **données + preuves + exposition API**.

### Runtime — fichiers de configuration

- `docker-compose.yml` — orchestration cible production (7 services).
- `Dockerfile` — image API E2.
- `.env.example` — modèle de variables d'environnement.
- `pyproject.toml` — config Ruff, ignore patterns, exclude.
- `requirements.txt` — dépendances Python verrouillées.
- `pytest.ini` — config pytest, asyncio, plugins.
- `pyrightconfig.json` — typage statique.

### Documentation technique

- [`README.md`](README.md) — vue projet, public technique externe.
- [`CHANGELOG.md`](CHANGELOG.md) — historique versions.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — standards code et conventions.
- [`DEPLOY.md`](DEPLOY.md) — déploiement.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — architecture détaillée.
- [`docs/dev/LOGGING.md`](docs/dev/LOGGING.md) — `loguru` et tables d'audit.
- [`docs/dev/FLOW_DONNEES.md`](docs/dev/FLOW_DONNEES.md) — flux RAW → SILVER → GOLD → GoldAI.
- [`docs/dev/DOCKER_RUNTIME.md`](docs/dev/DOCKER_RUNTIME.md) — build, healthcheck, volumes.
- [`docs/e5/PROCEDURE_INSTALLATION_MONITORING.md`](docs/e5/PROCEDURE_INSTALLATION_MONITORING.md) — procédure monitoring détaillée.
- [`docs/AUDIT_CODE_NETTOYAGE.md`](docs/AUDIT_CODE_NETTOYAGE.md) — audit code 7 étapes (référence interne).

### Scripts critiques par usage

| Usage | Script |
|---|---|
| Init base | `scripts/setup_with_sql.py`, `scripts/init_profils_table.py` |
| Comptes | `scripts/create_user.py`, `scripts/change_password.py` |
| Pipeline run | `main.py`, `run_daily.ps1` |
| Cohérence | `scripts/db_state_report.py` |
| Backup | `scripts/backup_parquet_to_mongo.py`, `scripts/download_from_mongo_gridfs.py` |
| Entraînement | `scripts/finetune_sentiment.py`, `scripts\run_training_loop_e2.bat` |
| Modèle Colab | `scripts/install_colab_model.py` |
| Vérification E5 | `scripts/run_e5_verification.py` |
| Récupération venv | `scripts/fix_venv.bat` |

---

*Dernière mise à jour : 8 mai 2026 — RUNBOOK v2 (refonte exploitation : 15 sections ; ajout § 15 « Carte des emplacements des fichiers » pour audit / soutenance).*
