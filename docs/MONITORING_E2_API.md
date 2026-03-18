# Monitoring Prometheus - API E2

## Vue d'ensemble

L'API E2 expose des métriques Prometheus pour le monitoring en production.

## Endpoint Métriques

**URL**: `http://localhost:8001/metrics`

**Format**: Prometheus text format

**Exemple**:
```bash
curl http://localhost:8001/metrics
```

## Métriques Disponibles

### Counters (Total events)

#### `datasens_e2_api_requests_total`
Nombre total de requêtes API
- Labels: `method`, `endpoint`, `status_code`
- Exemple: `datasens_e2_api_requests_total{method="GET",endpoint="/api/v1/raw/articles",status_code="200"}`

#### `datasens_e2_api_authentications_total`
Nombre total de tentatives d'authentification
- Labels: `status` (success, failed)
- Exemple: `datasens_e2_api_authentications_total{status="success"}`

#### `datasens_e2_api_zone_access_total`
Nombre total d'accès par zone
- Labels: `zone` (raw, silver, gold), `method`
- Exemple: `datasens_e2_api_zone_access_total{zone="gold",method="GET"}`

#### `datasens_e2_api_errors_total`
Nombre total d'erreurs API
- Labels: `status_code`, `endpoint`
- Exemple: `datasens_e2_api_errors_total{status_code="401",endpoint="/api/v1/raw/articles"}`

### Histograms (Duration)

#### `datasens_e2_api_request_duration_seconds`
Durée des requêtes API en secondes
- Labels: `method`, `endpoint`
- Buckets: 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0
- Exemple: `datasens_e2_api_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/gold/articles",le="0.1"}`

### Gauges (Current state)

#### `datasens_e2_api_active_connections`
Nombre actuel de connexions actives
- Exemple: `datasens_e2_api_active_connections 5`

#### `datasens_e2_api_active_users`
Nombre actuel d'utilisateurs authentifiés actifs
- Exemple: `datasens_e2_api_active_users 3`

## Configuration Prometheus

### Scrape Configuration

Dans `monitoring/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'datasens-e2-api'
    static_configs:
      - targets: ['datasens-e2-api:8001']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s
```

### Docker Compose

Le service `datasens-e2-api` est configuré dans `docker-compose.yml`:

```yaml
datasens-e2-api:
  container_name: datasens-e2-api
  ports:
    - "8001:8001"
  networks:
    - datasens-network
```

## Utilisation

### 1. Lancer l'API E2

```bash
python run_e2_api.py
```

### 2. Vérifier les métriques

```bash
curl http://localhost:8001/metrics
```

### 3. Prometheus scrape automatique

Si Prometheus est lancé via Docker Compose, il scrape automatiquement l'API E2 toutes les 10 secondes.

### 4. Visualisation Grafana

Les métriques sont disponibles dans Grafana (http://localhost:3000) via Prometheus.

## Requêtes PromQL Exemples

### Taux de requêtes par seconde

```promql
rate(datasens_e2_api_requests_total[5m])
```

### Latence moyenne (p50)

```promql
histogram_quantile(0.5, rate(datasens_e2_api_request_duration_seconds_bucket[5m]))
```

### Taux d'erreurs

```promql
rate(datasens_e2_api_errors_total[5m])
```

### Taux de succès authentification

```promql
rate(datasens_e2_api_authentications_total{status="success"}[5m])
```

### Accès par zone

```promql
sum by (zone) (rate(datasens_e2_api_zone_access_total[5m]))
```

## Choix techniques (outillage du monitorage)

### Pourquoi Prometheus ?

- **Standard industriel** : Format texte écossable, adoption large, intégration avec Grafana
- **Pull model** : Prometheus scrape les endpoints ; pas de push depuis l'application (simplicité)
- **Métriques temporelles** : Idéal pour séries temporelles (requêtes, latence, drift)
- **Écosystème** : Alertmanager, règles d'alerte, requêtes PromQL puissantes
- **Faible coût** : Pas de licence, déploiement local ou cloud

### Pourquoi Grafana ?

- **Visualisation** : Dashboards interactifs, graphiques, tableaux
- **Multi-sources** : Prometheus, mais aussi autres backends si évolution
- **Provisioning** : Dashboards et datasources en fichier (versionnables)
- **Alertes** : Notifications (email, Slack) possibles en complément de Prometheus

### Architecture monitoring

```
Application (E2 API, E1 Pipeline)
    ↓ expose /metrics
Prometheus (collecteur)
    ↓ scrape périodique
    ↓ évalue les règles (prometheus_rules.yml)
Alertmanager (optionnel) → Notifications
Grafana ← Prometheus (source de données)
    ↓ dashboards
Utilisateur
```

---

## Architecture

### Middleware Prometheus

Le middleware `PrometheusMiddleware` est ajouté en première position dans `src/e2/api/main.py` pour capturer toutes les requêtes.

### Endpoint /metrics

L'endpoint `/metrics` utilise `prometheus_client.generate_latest()` pour exposer les métriques au format Prometheus.

### Métriques Business

Les métriques business (authentification, zones) sont enregistrées dans les routes correspondantes:
- `src/e2/api/routes/auth.py`: `record_auth_success()`, `record_auth_failure()`
- Middleware: métriques automatiques par zone

## Notes

- Les endpoints `/metrics`, `/health`, `/docs`, `/redoc`, `/openapi.json` sont exclus du tracking pour éviter le bruit
- Les paths avec IDs sont normalisés (ex: `/api/v1/raw/articles/123` → `/api/v1/raw/articles/{id}`)
- Le registry Prometheus est séparé de celui d'E1 pour éviter les conflits
