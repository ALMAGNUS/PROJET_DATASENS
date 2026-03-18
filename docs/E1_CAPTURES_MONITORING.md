# Captures d'écran — Monitoring & API

**Retour professeur** : Ajouter des images de Grafana, Uptime Kuma, Prometheus et la ReDoc OpenAPI de l'API.

---

## URLs à capturer

| Composant | URL | Commande pour démarrer |
|-----------|-----|------------------------|
| **ReDoc (OpenAPI)** | http://localhost:8001/redoc | `python run_e2_api.py` (API sur 8001) |
| **Swagger UI** | http://localhost:8001/docs | Idem |
| **OpenAPI JSON** | http://localhost:8001/openapi.json | Idem |
| **Prometheus** | http://localhost:9090 | `start_prometheus.bat` ou `docker-compose up prometheus` |
| **Grafana** | http://localhost:3000 | `start_grafana.bat` ou `docker-compose up grafana` |
| **Uptime Kuma** | http://localhost:3001 (Docker Compose) ou 3002 (standalone) | `docker-compose up uptime-kuma` ou `start_uptime_kuma.bat` |

---

## Captures à réaliser

### 1. ReDoc (OpenAPI) — **prioritaire**

1. Lancer l'API : `python run_e2_api.py`
2. Ouvrir **http://localhost:8001/redoc**
3. Faire une capture d'écran de la page ReDoc (documentation interactive de l'API)
4. Sauvegarder dans `docs/images/redoc_api.png`

### 2. Prometheus

1. Lancer Prometheus : `start_prometheus.bat` ou `docker-compose up -d prometheus`
2. Ouvrir **http://localhost:9090**
3. Aller dans **Status → Targets** : capture des cibles (UP/DOWN)
4. Optionnel : **Graph** avec une requête (ex: `datasens_e2_api_requests_total`)
5. Sauvegarder dans `docs/images/prometheus_targets.png`

### 3. Grafana

1. Lancer Grafana : `start_grafana.bat` ou `docker-compose up -d grafana`
2. Ouvrir **http://localhost:3000** (ou 3001 selon config)
3. Login : **admin** / **admin**
4. Aller dans **Dashboards** → importer `monitoring/grafana/dashboards/datasens-full.json` si besoin
5. Faire une capture du dashboard DataSens
6. Sauvegarder dans `docs/images/grafana_dashboard.png`

### 4. Uptime Kuma

1. Lancer : `docker-compose up -d uptime-kuma`
2. Ouvrir **http://localhost:3001**
3. Premier accès : créer un compte admin
4. Ajouter des monitors : API (8001), Prometheus (9090), Grafana (3000)
5. Faire une capture du tableau de bord
6. Sauvegarder dans `docs/images/uptime_kuma.png`

---

## Dossier des images

Placer les captures dans **`docs/images/`** :

```
docs/images/
├── redoc_api.png          # ReDoc OpenAPI (prioritaire)
├── prometheus_targets.png # Prometheus Targets
├── grafana_dashboard.png  # Dashboard Grafana
└── uptime_kuma.png        # Uptime Kuma
```

---

## Intégration dans le dossier E1

Pour inclure les images dans la documentation :

```markdown
## ReDoc OpenAPI

![ReDoc API](images/redoc_api.png)

L'API E2 expose une documentation OpenAPI interactive : http://localhost:8001/redoc
```

---

## Démarrage rapide (tout le stack)

```bash
# 1. API E2 (ReDoc)
python run_e2_api.py

# 2. Prometheus + Grafana + Uptime Kuma (Docker)
docker-compose up -d prometheus grafana uptime-kuma

# 3. Métriques E1 (optionnel, pour que Prometheus ait des données)
python scripts/run_e1_metrics.py
```

Puis ouvrir les URLs et faire les captures.
