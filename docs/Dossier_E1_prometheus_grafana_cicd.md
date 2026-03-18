# 📋 Dossier E1 — Guide 4 : Prometheus, Grafana, CI/CD

Le projet intègre un monitoring complet basé sur Prometheus et Grafana. Prometheus collecte les métriques exposées par le pipeline E1 (articles traités, taux d’enrichissement) et par l’API E2 (requêtes, latence, authentification, drift). Grafana permet de les visualiser via des dashboards. En parallèle, une pipeline CI/CD (GitHub Actions) exécute les tests à chaque push, construit l’image Docker et prépare le déploiement. Cette combinaison assure la qualité du code, la visibilité opérationnelle et la capacité à déployer de manière fiable.

**Objectif** : Documenter la surveillance (Prometheus, Grafana) et l'intégration continue (GitHub Actions).

---

## 1. Vue d'ensemble

Le projet combine deux volets : la **surveillance** (Prometheus + Grafana) pour suivre le comportement du pipeline E1 et de l'API E2 en production, et la **CI/CD** (GitHub Actions) pour valider le code et préparer les déploiements. Prometheus scrape les métriques exposées sur des endpoints HTTP ; Grafana les visualise sous forme de graphiques. La CI exécute les tests et construit l'image Docker à chaque push.

| Composant | Port | Rôle |
|-----------|------|------|
| **Prometheus** | 9090 | Collecte des métriques (scrape) |
| **Grafana** | 3000 | Visualisation, dashboards |
| **Uptime Kuma** | 3001 | Monitoring de disponibilité (API, Prometheus, Grafana) |
| **Métriques E1** | 8000 | Pipeline (articles, enrichissement) |
| **Métriques E2** | 8001 | API (requêtes, latence, auth, drift) |

---

## 2. ReDoc / OpenAPI (documentation API E2)

L'API E2 expose une documentation OpenAPI interactive :

| URL | Description |
|-----|-------------|
| **http://localhost:8001/redoc** | ReDoc — documentation lisible, structurée |
| **http://localhost:8001/docs** | Swagger UI — interface interactive |
| **http://localhost:8001/openapi.json** | Spécification OpenAPI (JSON) |

**Démarrer l'API** : `python run_e2_api.py` puis ouvrir http://localhost:8001/redoc.

> **Captures à produire** : Voir [E1_CAPTURES_MONITORING.md](E1_CAPTURES_MONITORING.md) pour les instructions et emplacements des images. Une fois les captures réalisées, ajouter dans ce document : `![ReDoc](images/redoc_api.png)`, `![Prometheus](images/prometheus_targets.png)`, `![Grafana](images/grafana_dashboard.png)`, `![Uptime Kuma](images/uptime_kuma.png)`.

---

## 3. Prometheus

### 3.1 Cibles (scrape)

Prometheus interroge périodiquement (scrape) des endpoints HTTP qui exposent des métriques au format texte. Chaque cible correspond à un job avec une liste d'URL à surveiller. Les métriques E1 (pipeline) et E2 (API) sont exposées sur des ports distincts pour permettre un démarrage indépendant des services.

| Job | Target | Métriques |
|-----|--------|-----------|
| `datasens-e1` | localhost:8000 | `datasens_pipeline_runs_total`, `datasens_articles_*`, `datasens_enrichment_rate` |
| `datasens-e2-api` | localhost:8001 | `datasens_e2_api_requests_total`, `datasens_e2_api_request_duration_seconds`, `datasens_drift_*` |
| `prometheus` | localhost:9090 | Métriques Prometheus lui-même |

### 3.2 Démarrer Prometheus (local)

```bash
# Avec le script .bat (Windows)
start_prometheus.bat

# Ou en ligne de commande
prometheus --config.file=monitoring/prometheus.local.yml --web.enable-lifecycle
```

### 3.3 Vérifier les cibles

Ouvrir **http://localhost:9090** → **Status** → **Targets**. Les cibles doivent être "UP".

### 3.4 Fichiers de configuration

| Fichier | Usage |
|---------|-------|
| `monitoring/prometheus.local.yml` | Mode local (localhost) |
| `monitoring/prometheus.yml` | Docker Compose (noms de services) |
| `monitoring/prometheus_rules.yml` | Règles d'alertes |

---

## 4. Métriques E1 (port 8000)

### 4.1 Option A : Standalone (recommandé)

Le script `run_e1_metrics.py` démarre un petit serveur HTTP qui expose le endpoint `/metrics` et interroge la base SQLite toutes les 30 secondes pour mettre à jour les gauges. On peut l'exécuter en parallèle du pipeline sans bloquer les exécutions ponctuelles de `main.py`.

```bash
# Expose /metrics en continu, met à jour les gauges depuis la DB toutes les 30 s
python scripts/run_e1_metrics.py
```

### 4.2 Option B : Après pipeline

```bash
# Garde le processus vivant après main.py pour que Prometheus puisse scraper
python main.py --keep-metrics
```

### 4.3 Métriques E1 exposées

- `datasens_pipeline_runs_total`
- `datasens_articles_extracted_total`
- `datasens_articles_loaded_total`
- `datasens_articles_tagged_total`
- `datasens_articles_analyzed_total`
- `datasens_articles_in_database`
- `datasens_articles_enriched`
- `datasens_enrichment_rate`
- `datasens_sources_active`

---

## 5. Grafana

### 5.1 Démarrer Grafana

```bash
# Windows (Docker)
start_grafana.bat

# Ligne de commande Docker
docker run -d --name grafana -p 3000:3000 ^
  -v "%cd%\monitoring\grafana\provisioning:/etc/grafana/provisioning" ^
  grafana/grafana
```

### 5.2 Connexion

- **URL** : http://localhost:3000 (ou 3001 selon start_grafana.bat)
- **Login** : admin / admin (changement de mot de passe demandé au premier accès)

### 5.3 Datasources Prometheus

| Datasource | URL | Quand |
|------------|-----|-------|
| **Prometheus (Docker)** | `http://prometheus:9090` | Tout dans Docker Compose |
| **Prometheus (Local)** | `http://host.docker.internal:9090` | Grafana en Docker, Prometheus local |

Si les dashboards sont vides → **Configuration** → **Data sources** → **Prometheus (Local)** → **Save & test**.

### 5.4 Dashboard DataSens

- **Import** : `monitoring/grafana/dashboards/datasens-full.json`
- **Contenu** : requêtes API, latence, auth, drift, métriques E1

### 5.5 Mise à jour des gauges de drift

```http
GET http://localhost:8001/api/v1/analytics/drift-metrics
Authorization: Bearer YOUR_TOKEN
```

Appeler régulièrement (cron, tâche planifiée) pour alimenter les courbes de drift dans Grafana.

---

## 6. Uptime Kuma

Uptime Kuma surveille la disponibilité des services (API, Prometheus, Grafana). Démarrage avec Docker Compose :

```bash
docker-compose up -d uptime-kuma
```

- **URL** : http://localhost:3001
- **Premier accès** : créer un compte admin
- **Monitors** : ajouter http://localhost:8001/health (API), http://localhost:9090 (Prometheus), http://localhost:3000 (Grafana)

---

## 7. Docker Compose (stack complète)

```bash
docker-compose up -d
```

Services : `datasens-e1`, `datasens-e2-api`, `prometheus`, `grafana`, `uptime-kuma`, `mongodb` (optionnel).

---

## 8. CI/CD — GitHub Actions

### 8.1 Workflow principal (`.github/workflows/ci-cd.yml`)

| Job | Déclencheur | Rôle |
|-----|-------------|------|
| **test** | push/PR sur main, develop | Lint, pytest, validation E1 |
| **build** | après test | Build image Docker, push GHCR |
| **deploy** | push sur main | Déploiement (placeholder) |

### 8.2 Étapes de test

```yaml
- pytest tests/test_e1_isolation.py -v -m "not slow"
- python -c "from src.e1.pipeline import E1Pipeline; ..."
- python -c "from src.shared.interfaces import E1DataReader; ..."
- pytest tests/ -v (autres tests)
```

### 8.3 Build Docker

- **Image** : `ghcr.io/<repo>/<image>`
- **Tags** : branch, PR, SHA, semver
- **Cache** : GitHub Actions cache (mode=max)

### 8.4 Variables d'environnement CI

- `PYTHONPATH` : workspace + workspace/src
- `REGISTRY` : ghcr.io
- `IMAGE_NAME` : github.repository

---

## 9. Ordre de démarrage (mode local)

1. **API E2** : `python run_e2_api.py` (port 8001) — ReDoc : http://localhost:8001/redoc
2. **Métriques E1** : `python scripts/run_e1_metrics.py` (port 8000)
3. **Prometheus** : `start_prometheus.bat` ou `prometheus --config.file=monitoring/prometheus.local.yml`
4. **Grafana** : `start_grafana.bat`
5. **Uptime Kuma** : `docker-compose up -d uptime-kuma` (optionnel)
6. **Vérifier** : http://localhost:9090/targets, http://localhost:3000, http://localhost:3001

---

## 10. Résumé des scripts

| Script | Rôle |
|--------|------|
| `start_prometheus.bat` | Lance Prometheus (config locale) |
| `start_grafana.bat` | Lance Grafana (Docker) |
| `scripts/run_e1_metrics.py` | Serveur métriques E1 standalone |

| Fichier | Rôle |
|---------|------|
| `monitoring/prometheus.local.yml` | Config Prometheus locale |
| `monitoring/grafana/provisioning/datasources/prometheus.yml` | Datasources Grafana |
| `.github/workflows/ci-cd.yml` | Pipeline CI/CD |
