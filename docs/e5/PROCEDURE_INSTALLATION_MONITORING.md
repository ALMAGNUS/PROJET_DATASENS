# Procédure d'installation et de configuration du monitoring — DataSens E5

**Critère C20** — Documenter le monitorage et les procédures d'installation et de configuration

---

## 1. Prérequis

- **Python 3.10+** avec dépendances (`pip install -r requirements.txt`)
- **Docker** (recommandé pour Prometheus, Grafana, Uptime Kuma)
- **API E2** démarrée (`python run_e2_api.py`)

---

## 2. Installation Prometheus

### Option A : Script batch (Windows)

```batch
start_prometheus.bat
```

### Option B : Ligne de commande

```bash
prometheus --config.file=monitoring/prometheus.local.yml --web.enable-lifecycle
```

### Option C : Docker

```bash
docker run -d --name prometheus -p 9090:9090 \
  -v "%cd%\monitoring\prometheus.local.yml:/etc/prometheus/prometheus.yml" \
  -v "%cd%\monitoring\prometheus_rules.yml:/etc/prometheus/rules.yml" \
  prom/prometheus
```

### Vérification

- URL : http://localhost:9090
- Status → Targets : cible `localhost:8001` doit être UP
- Graph : requête `datasens_e2_api_requests_total`

---

## 3. Installation Grafana

### Option A : Script batch (Windows)

```batch
start_grafana.bat
```

### Option B : Docker

```bash
docker run -d --name grafana -p 3000:3000 \
  -v "%cd%\monitoring\grafana\provisioning:/etc/grafana/provisioning" \
  -v "%cd%\monitoring\grafana\dashboards:/var/lib/grafana/dashboards" \
  -e "GF_PATHS_PROVISIONING=/etc/grafana/provisioning" \
  grafana/grafana
```

### Configuration

1. Premier accès : http://localhost:3000 — login **admin** / **admin**
2. Datasource Prometheus : provisionnée automatiquement (`monitoring/grafana/provisioning/datasources/prometheus.yml`)
3. Dashboards : provisionnés depuis `monitoring/grafana/dashboards/` — couvrent toutes les routes API, drift, latence et surveillance des logs
4. Import manuel si besoin : Dashboards → Import → `monitoring/grafana/dashboards/datasens-full.json`

---

## 4. Installation Uptime Kuma

### Option A : Docker Compose (port 3001)

```bash
docker-compose up -d uptime-kuma
```

### Option B : Standalone (port 3002)

```batch
start_uptime_kuma.bat
```

### Configuration

**Port** : 3001 (Docker Compose) ou 3002 (standalone)

1. Premier accès : http://localhost:3001 (ou 3002)
2. Créer un compte admin
3. Ajouter des monitors :
   - **API E2** : HTTP(s) — http://localhost:8001/health
   - **Prometheus** : HTTP(s) — http://localhost:9090/-/healthy
   - **Grafana** : HTTP(s) — http://localhost:3000/api/health

---

## 5. Ordre de démarrage recommandé

### Option A : Docker Compose (tout-en-un)

```bash
docker-compose up -d
```

Démarre : `datasens-e1-metrics` (8000), `datasens-e2-api` (8001), Prometheus (9090), Grafana (3000), Uptime Kuma (3001).

### Option B : Local (sans Docker)

1. `python scripts/run_e1_metrics.py` (port 8000 — métriques E1 en continu)
2. `python run_e2_api.py` (port 8001)
3. `start_prometheus.bat` (port 9090)
4. `start_grafana.bat` (port 3000)
5. `start_uptime_kuma.bat` (port 3002, standalone)

---

## 6. Métriques E1 (pipeline)

Pour que Prometheus collecte les métriques du pipeline E1 (`datasens_pipeline_errors_total`, `datasens_articles_in_database`, etc.) :

- **Docker** : le service `datasens-e1-metrics` est démarré automatiquement par `docker-compose up -d`
- **Local** : lancer `python scripts/run_e1_metrics.py` pour exposer `/metrics` sur le port 8000

---

## 7. Fichiers de configuration

| Fichier | Rôle |
|---------|------|
| `monitoring/prometheus.local.yml` | Config Prometheus (mode local) |
| `monitoring/prometheus.yml` | Config Prometheus (Docker Compose) |
| `monitoring/prometheus_rules.yml` | Règles d'alertes |
| `monitoring/grafana/provisioning/datasources/prometheus.yml` | Datasource Grafana |
| `monitoring/grafana/provisioning/dashboards/dashboard.yml` | Provisioning dashboards |
| `monitoring/grafana/dashboards/datasens-full.json` | Dashboard API + drift |

---

## 8. Références

- **Métriques et seuils** : `docs/METRIQUES_SEUILS_ALERTES.md`
- **Monitoring API E2** : `docs/MONITORING_E2_API.md`
- **Guide Grafana** : `monitoring/README_GRAFANA.md`
- **Captures** : `docs/E1_CAPTURES_MONITORING.md`
