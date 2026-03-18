# Métriques, seuils et alertes — DataSens

**Critère C20** — Documentation des métriques et valeurs d'alerte pour le monitorage de l'application IA

---

## 1. Métriques API E2

| Métrique | Type | Description | Seuil d'alerte | Niveau | Référence |
|----------|------|-------------|----------------|--------|-----------|
| `datasens_e2_api_requests_total` | Counter | Requêtes API totales | — | — | Indicateur de volume |
| `datasens_e2_api_errors_total` | Counter | Erreurs API (4xx, 5xx) | Taux > 5 % req/min | warning | Voir PromQL ci-dessous |
| `datasens_e2_api_request_duration_seconds` | Histogram | Latence des requêtes | p95 > 5 s pendant 5 min | warning | Latence excessive |
| `datasens_e2_api_authentications_total{status="failed"}` | Counter | Échecs d'authentification | Pic > 10/min | warning | Tentatives brute-force |
| `datasens_e2_api_active_connections` | Gauge | Connexions actives | > 100 | warning | Saturation possible |
| `datasens_drift_sentiment_entropy` | Gauge | Entropie sentiment | < 0.5 | warning | Drift distribution |
| `datasens_drift_topic_dominance` | Gauge | Dominance topic | > 0.8 | warning | Drift thématique |
| `datasens_drift_score` | Gauge | Score drift composite | > 0.7 | warning | Drift global |

---

## 2. Métriques pipeline E1 (si serveur métriques lancé)

| Métrique | Type | Description | Seuil d'alerte | Niveau | Fichier règle |
|----------|------|-------------|----------------|--------|---------------|
| `datasens_pipeline_errors_total` | Counter | Erreurs pipeline | rate > 0.1/s pendant 5 min | warning | prometheus_rules.yml |
| `datasens_source_errors_total` | Counter | Erreurs par source | rate > 0.05/s pendant 5 min | warning | prometheus_rules.yml |
| `datasens_enrichment_rate` | Gauge | Taux d'enrichissement | < 0.5 pendant 10 min | warning | prometheus_rules.yml |
| `datasens_articles_extracted_total` | Counter | Articles extraits | rate == 0 sur 1 h | critical | prometheus_rules.yml |
| `datasens_articles_in_database` | Gauge | Croissance BDD | rate < 1/h pendant 2 h | warning | prometheus_rules.yml |

---

## 3. Alertes configurées (prometheus_rules.yml)

| Alerte | Expression | Durée | Sévérité |
|--------|------------|-------|----------|
| PipelineHighErrorRate | `rate(datasens_pipeline_errors_total[5m]) > 0.1` | 5 min | warning |
| SourceExtractionFailure | `rate(datasens_source_errors_total[5m]) > 0.05` | 5 min | warning |
| LowEnrichmentRate | `datasens_enrichment_rate < 0.5` | 10 min | warning |
| NoArticlesCollected | `rate(datasens_articles_extracted_total[1h]) == 0` | 1 h | critical |
| DatabaseGrowthStalled | `rate(datasens_articles_in_database[1h]) < 1` | 2 h | warning |

---

## 4. Actions recommandées en cas d'alerte

| Alerte | Action |
|--------|--------|
| PipelineHighErrorRate | Vérifier les logs (`sync_log`), sources en échec, connectivité |
| SourceExtractionFailure | Identifier la source (`source` label), tester l'URL, vérifier quotas API |
| LowEnrichmentRate | Vérifier le tagger/analyzer, données d'entrée |
| NoArticlesCollected | Vérifier que le pipeline tourne, toutes les sources actives |
| DatabaseGrowthStalled | Vérifier ingestion, espace disque, verrous DB |
| Erreurs API élevées | Vérifier logs FastAPI, santé BDD, dépendances |
| Latence élevée | Vérifier charge, requêtes lentes, index DB |

---

## 5. Références

- **Prometheus** : `monitoring/prometheus.local.yml`, `monitoring/prometheus.yml`
- **Règles** : `monitoring/prometheus_rules.yml`
- **Doc détaillée** : `docs/MONITORING_E2_API.md`, `monitoring/README_GRAFANA.md`
