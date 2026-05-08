# DataSens — Plan de lancement complet

Guide pour lancer tous les composants du projet dans le bon ordre. À exécuter depuis la **racine du projet**.

---

## Vue d'ensemble des services

| Service | Port | Dépendances | Commande |
|---------|------|-------------|----------|
| **API E2** | 8001 | — | `python run_e2_api.py` |
| **Métriques E1** | 8000 | DB SQLite | `python scripts/run_e1_metrics.py` |
| **Cockpit Streamlit** | 8501 | API E2 | `streamlit run src\streamlit\app.py` |
| **Prometheus** | 9090 | API E2, Métriques E1 | `start_prometheus.bat` ou Docker |
| **Grafana** | 3000 | Prometheus | `start_grafana.bat` ou Docker |
| **Uptime Kuma** | 3001 / 3002 | — | `docker-compose up -d uptime-kuma` ou `start_uptime_kuma.bat` |
| **MLflow UI** | 5000 | mlruns/ (après entraînement) | `mlflow ui` |

---

## Scénario 1 : Tout avec Docker Compose (recommandé)

**Prérequis** : Docker installé.

```bash
docker-compose up -d
```

Démarre automatiquement :
- `datasens-e1-metrics` (métriques pipeline sur 8000)
- `datasens-e2-api` (API FastAPI sur 8001)
- Prometheus (9090)
- Grafana (3000)
- Uptime Kuma (3001)

**Ensuite** (hors Docker) :
1. Cockpit : `streamlit run src\streamlit\app.py` → http://localhost:8501
2. MLflow (si entraînement effectué) : `mlflow ui` → http://localhost:5000

**Vérification** :
- API : http://localhost:8001/health
- Métriques : http://localhost:8001/metrics
- Prometheus : http://localhost:9090 → Status → Targets (toutes UP)
- Grafana : http://localhost:3000 (admin/admin)
- Uptime Kuma : http://localhost:3001

---

## Scénario 2 : Local (sans Docker)

**Ordre recommandé** :

### 1. Environnement Python

```bat
.venv\Scripts\activate.bat
```

### 2. Métriques E1 (optionnel, pour Prometheus)

```bat
python scripts/run_e1_metrics.py
```

→ Expose `/metrics` sur http://localhost:8000 (garder le terminal ouvert).

### 3. API E2

```bat
python run_e2_api.py
```

→ http://localhost:8001

### 4. Prometheus (optionnel)

```bat
start_prometheus.bat
```

→ http://localhost:9090

### 5. Grafana (optionnel, nécessite Docker)

```bat
start_grafana.bat
```

→ http://localhost:3000

### 6. Cockpit Streamlit

```bat
streamlit run src\streamlit\app.py
```

→ http://localhost:8501

### 7. MLflow (après un entraînement)

```bat
mlflow ui
```

→ http://localhost:5000 — visualise les runs dans `mlruns/`

---

## Scénario 3 : Fine-tuning + MLflow

### Entraînement

```bat
scripts\run_training_loop_e2.bat
```

ou mode complet :

```bat
scripts\run_training_loop_e2.bat --full
```

Chaque run enregistre automatiquement dans MLflow (`mlruns/`).

### Consulter les runs

```bat
mlflow ui
```

Ouvrir http://localhost:5000 → expérience `datasens-sentiment`.

---

## Scénario 4 : Pipeline E1 seul

```bat
python main.py
```

Pour garder les métriques E1 à jour après le pipeline :

```bat
python main.py --keep-metrics
```

(ou lancer `python scripts/run_e1_metrics.py` en parallèle pour un serveur métriques continu)

---

## Checklist « projet terminé »

- [ ] `pip install -r requirements.txt` exécuté
- [ ] Base SQLite initialisée : `python scripts/setup_with_sql.py`
- [ ] Données GoldAI présentes (ou pipeline E1 exécuté)
- [ ] Modèle fine-tuné (optionnel) : `scripts\run_training_loop_e2.bat`
- [ ] API E2 accessible : http://localhost:8001/health
- [ ] Cockpit accessible : http://localhost:8501
- [ ] Prometheus scrape OK (Targets UP) si monitoring activé
- [ ] Grafana dashboards visibles si monitoring activé
- [ ] MLflow UI fonctionnel après entraînement : `mlflow ui`

---

## Dépannage : NumPy / bottleneck / scipy

Si vous voyez *"A module that was compiled using NumPy 1.x cannot be run in NumPy 2.2"* :

1. **Recréer le venv** (fermer Cursor et terminaux avant) :
   ```bat
   scripts\fix_venv.bat
   ```

2. **Docker** : reconstruire l’image (`docker-compose build --no-cache`).

---

## Références

- **Procédure monitoring** : `docs/e5/PROCEDURE_INSTALLATION_MONITORING.md`
- **Lancement simplifié** : `LANCER_TOUT.md`
- **Vérification E5** : `python scripts/run_e5_verification.py`
