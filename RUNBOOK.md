# RUNBOOK — DataSens

Document opérationnel unique pour lancer la plateforme. Consolide les anciens guides `LANCER_TOUT.md` et `PLANCHE_LANCEMENT.md`.

À exécuter depuis la **racine du projet** (dossier contenant `main.py`, `docker-compose.yml`, `start_full.bat`).

---

## 1. Inventaire des services

| Service | Port | Dépendances | Lancement |
|---|---|---|---|
| **API E2 (FastAPI)** | 8001 | base SQLite `profils` | `python run_e2_api.py` |
| **Cockpit Streamlit** | 8501 | API E2 | `streamlit run src/streamlit/app.py` ou `start_cockpit.bat` |
| **Métriques E1 (Prometheus client)** | 8000 | base SQLite | `python scripts/run_e1_metrics.py` |
| **MongoDB** | 27017 | — | `docker compose up -d mongodb` ou service Windows natif (cf. § 5) |
| **Prometheus** | 9090 | API E2, métriques E1 | `start_prometheus.bat` ou `docker compose up -d prometheus` |
| **Grafana** | 3000 | Prometheus | `start_grafana.bat` ou `docker compose up -d grafana` |
| **Uptime Kuma** | 3001 | — | `docker compose up -d uptime-kuma` |
| **MLflow UI** | 5000 | `mlruns/` | `mlflow ui` |

---

## 2. Lancement rapide (1 commande)

```bat
lancer_tout.bat
```

Ce lanceur de la racine :
1. démarre Prometheus + Grafana via Docker si Docker répond,
2. ouvre un terminal dédié pour l'API E2 (`python run_e2_api.py`),
3. ouvre un terminal dédié pour le cockpit (`streamlit run src/streamlit/app.py`).

Une fois lancé, ouvrir http://localhost:8501.

---

## 3. Scénarios standardisés

### Scénario A — Stack complète via Docker Compose

**Prérequis** : Docker Desktop installé et daemon actif (`docker info` répond).

```bash
docker compose up -d
```

Démarre :
- `datasens-e1-metrics` (8000)
- `datasens-e2-api` (8001)
- `datasens-mongodb` (27017)
- `datasens-prometheus` (9090)
- `datasens-grafana` (3000)
- `datasens-uptime-kuma` (3001)

**Hors Docker** (services UI locaux) :
- `streamlit run src/streamlit/app.py` → http://localhost:8501
- `mlflow ui` → http://localhost:5000

**Vérifications post-démarrage** :
- API : http://localhost:8001/health
- Métriques : http://localhost:8001/metrics
- Prometheus targets : http://localhost:9090/targets (toutes UP)
- Grafana : http://localhost:3000 (admin / admin par défaut)
- MongoDB : `docker exec datasens-mongodb mongosh --quiet --eval "db.adminCommand({ping: 1})"` doit afficher `{ ok: 1 }`.

### Scénario B — Lancement local (sans Docker)

Ordre recommandé, un terminal par service :

```bat
:: 1. Activer venv
.venv\Scripts\activate.bat

:: 2. Métriques E1 (optionnel)
python scripts/run_e1_metrics.py

:: 3. API E2
python run_e2_api.py

:: 4. Cockpit Streamlit
streamlit run src/streamlit/app.py
```

Pour le monitoring local :
- Prometheus : `start_prometheus.bat` (binaire local)
- Grafana : `start_grafana.bat` (Docker requis pour cette brique)
- MongoDB : service Windows natif, cf. § 5

### Scénario C — Pipeline E1 seul

```bat
python main.py
```

Variantes :
- `python main.py --keep-metrics` : garde le serveur de métriques actif après exécution.
- `python scripts/run_e1_metrics.py` (en parallèle) : serveur métriques continu indépendant du run.

### Scénario D — Fine-tuning + MLflow

```bat
scripts\run_training_loop_e2.bat
```

Mode complet :

```bat
scripts\run_training_loop_e2.bat --full
```

Chaque run logge automatiquement dans `mlruns/`. Visualisation :

```bat
mlflow ui
```

→ http://localhost:5000 → expérience `datasens-sentiment`.

### Scénario E — Cockpit + API uniquement (démo rapide)

```bat
start_full.bat
```

Démarre l'API et le cockpit dans deux terminaux dédiés. Ne touche pas Docker, MongoDB, ni le monitoring.

---

## 4. URLs et identifiants par défaut

| Service | URL | Identifiants |
|---|---|---|
| Cockpit | http://localhost:8501 | comptes SQLite `profils` (cf. `scripts/change_password.py --list`) |
| API E2 (Swagger) | http://localhost:8001/docs | bearer token via `/auth/login` |
| Métriques E1 | http://localhost:8000/metrics | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin (à changer en production) |
| Uptime Kuma | http://localhost:3001 | initialisé au premier login |
| MLflow UI | http://localhost:5000 | — |

---

## 5. MongoDB — local natif vs container

Le `docker-compose.yml` orchestre MongoDB 7 (`image: mongo:7`) comme livrable production. Sur poste de dev Windows, deux options selon l'état de Docker Desktop :

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

Dans les deux cas l'URI reste `mongodb://localhost:27017`. Le cockpit et le code applicatif ne voient pas la différence.

**Backup Parquet → GridFS** :
```bat
python scripts/backup_parquet_to_mongo.py
```

---

## 6. Checklist de mise en service

- [ ] `pip install -r requirements.txt` exécuté.
- [ ] Base SQLite initialisée : `python scripts/setup_with_sql.py`.
- [ ] Données GoldAI présentes (sinon : `python main.py`).
- [ ] (Optionnel) Modèle fine-tuné : `scripts\run_training_loop_e2.bat`.
- [ ] API E2 accessible : `curl http://localhost:8001/health`.
- [ ] Cockpit accessible : http://localhost:8501.
- [ ] MongoDB répond : `mongosh --quiet --eval "db.adminCommand({ping: 1})"`.
- [ ] Backup GridFS exécuté : `python scripts/backup_parquet_to_mongo.py`.
- [ ] Prometheus targets UP (si monitoring activé).
- [ ] Grafana dashboards visibles (si monitoring activé).
- [ ] MLflow UI fonctionnel (si entraînement effectué).

---

## 7. Dépannage

### NumPy / bottleneck / scipy

> *« A module that was compiled using NumPy 1.x cannot be run in NumPy 2.2 »*

Recréer le venv (fermer Cursor et tous les terminaux avant) :

```bat
scripts\fix_venv.bat
```

Pour Docker : reconstruire l'image avec `docker compose build --no-cache`.

### Docker Desktop bloqué au démarrage

```powershell
taskkill /F /IM "Docker Desktop.exe" /T
wsl --shutdown
Start-Sleep -Seconds 5
& "C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker info --format "{{.ServerVersion}}"   # attendre la réponse
```

Si le daemon ne répond toujours pas, basculer sur MongoDB natif (cf. § 5). Le `docker-compose.yml` reste le livrable de référence pour la production.

### Port déjà utilisé

Modifier le mapping dans `docker-compose.yml` :

```yaml
ports:
  - "8002:8000"   # remap externe
```

### MongoDB GridFS hors ligne dans le cockpit

1. Vérifier le service : `docker ps --filter name=datasens-mongodb` ou `Get-Service MongoDB`.
2. Tester la connexion : `python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017/').admin.command('ping'))"`.
3. Repeupler GridFS : `python scripts/backup_parquet_to_mongo.py`.
4. Recharger le cockpit, panneau `Vue d'ensemble → Lineage de la donnée`.

---

## 8. Références

- `docker-compose.yml` — orchestration cible production.
- `docs/dev/DOCKER_RUNTIME.md` — détails build, healthcheck, volumes Docker.
- `docs/dev/LOGGING.md` — configuration `loguru` et tables d'audit.
- `docs/dev/FLOW_DONNEES.md` — flux RAW → SILVER → GOLD → GoldAI.
- `docs/e5/PROCEDURE_INSTALLATION_MONITORING.md` — procédure détaillée monitoring.
- `scripts/run_e5_verification.py` — vérifications automatisées E5.
- `scripts/change_password.py` — gestion des comptes cockpit.
