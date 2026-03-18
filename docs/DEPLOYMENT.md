# 🚀 DataSens E1 - Déploiement Production

## Architecture Monolithique

DataSens E1 est conçu comme un **monolithe intouchable** :
- ✅ Code stable et testé
- ✅ Architecture SOLID/DRY
- ✅ Containerisé avec Docker
- ✅ Monitoring Prometheus + Grafana
- ✅ CI/CD automatisé

## Prérequis

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB espace disque

## Déploiement Rapide

### 1. Cloner le projet

```bash
git clone <repository-url>
cd PROJET_DATASENS
```

### 2. Configuration

Copier et adapter les fichiers de configuration :

```bash
cp sources_config.json.example sources_config.json
# Éditer sources_config.json avec vos sources
```

### 3. Lancer avec Docker Compose

```bash
# Build et démarrage de tous les services
docker-compose up -d --build

# Vérifier les services
docker-compose ps

# Voir les logs
docker-compose logs -f datasens-e1
```

### 4. Accéder aux services

- **Pipeline E1** : http://localhost:8000/metrics (Prometheus metrics)
- **Prometheus** : http://localhost:9090
- **Grafana** : http://localhost:3000
  - User: `admin`
  - Password: `admin` (à changer au premier login)

## Services

### DataSens E1 Pipeline

**Port** : 8000  
**Health Check** : `/metrics`  
**Métriques** : Prometheus format sur `/metrics`

**Variables d'environnement** :
- `DB_PATH` : Chemin vers la base de données (défaut: `/app/data/datasens.db`)
- `METRICS_PORT` : Port pour les métriques (défaut: `8000`)

### Prometheus

**Port** : 9090  
**Configuration** : `monitoring/prometheus.yml`  
**Règles d'alerte** : `monitoring/prometheus_rules.yml`

### Grafana

**Port** : 3000  
**Dashboards** : Provisionnés automatiquement depuis `monitoring/grafana/dashboards/`

## Métriques Disponibles

### Counters
- `datasens_pipeline_runs_total` : Nombre total d'exécutions
- `datasens_articles_extracted_total{source}` : Articles extraits par source
- `datasens_articles_loaded_total` : Articles chargés en DB
- `datasens_articles_tagged_total{topic}` : Articles taggés par topic
- `datasens_articles_analyzed_total{sentiment}` : Articles analysés par sentiment
- `datasens_articles_deduplicated_total` : Articles dédupliqués

### Histograms
- `datasens_pipeline_duration_seconds{stage}` : Durée d'exécution par étape
- `datasens_extraction_duration_seconds{source}` : Durée d'extraction par source

### Gauges
- `datasens_articles_in_database` : Nombre d'articles en DB
- `datasens_articles_enriched` : Nombre d'articles enrichis
- `datasens_enrichment_rate` : Taux d'enrichissement (0-1)
- `datasens_sources_active` : Nombre de sources actives

## Maintenance

### Mettre à jour le code

```bash
# Rebuild l'image
docker-compose build datasens-e1

# Redémarrer le service
docker-compose restart datasens-e1
```

### Sauvegarder les données

```bash
# Sauvegarder la base de données
docker-compose exec datasens-e1 cp /app/data/datasens.db /app/data/datasens.db.backup

# Sauvegarder les exports
docker-compose exec datasens-e1 tar -czf /app/exports/backup.tar.gz /app/exports/*.csv
```

### Voir les logs

```bash
# Logs du pipeline
docker-compose logs -f datasens-e1

# Logs Prometheus
docker-compose logs -f prometheus

# Logs Grafana
docker-compose logs -f grafana
```

## CI/CD

Le pipeline CI/CD est configuré dans `.github/workflows/ci-cd.yml` :

1. **Test** : Lint + Tests unitaires
2. **Build** : Construction de l'image Docker
3. **Deploy** : Déploiement automatique (si sur `main`)

### Déploiement manuel

```bash
# Build l'image
docker build -t datasens-e1:latest .

# Tag pour le registry
docker tag datasens-e1:latest ghcr.io/<user>/datasens-e1:latest

# Push
docker push ghcr.io/<user>/datasens-e1:latest
```

## Monitoring

### Alertes Prometheus

Les alertes sont configurées dans `monitoring/prometheus_rules.yml` :
- Pipeline errors élevés
- Échecs d'extraction de sources
- Taux d'enrichissement faible
- Aucun article collecté

### Dashboards Grafana

Le dashboard principal inclut :
- Statistiques globales (runs, articles, enrichissement)
- Graphiques par source
- Distribution sentiment/topics
- Taux d'erreur

## Troubleshooting

### Le pipeline ne démarre pas

```bash
# Vérifier les logs
docker-compose logs datasens-e1

# Vérifier les volumes
docker-compose exec datasens-e1 ls -la /app/data

# Vérifier la configuration
docker-compose exec datasens-e1 cat /app/sources_config.json
```

### Prometheus ne collecte pas de métriques

```bash
# Vérifier que le service expose les métriques
curl http://localhost:8000/metrics

# Vérifier la configuration Prometheus
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml
```

### Grafana ne charge pas les dashboards

```bash
# Vérifier les permissions
docker-compose exec grafana ls -la /var/lib/grafana/dashboards

# Vérifier la configuration de provisioning
docker-compose exec grafana cat /etc/grafana/provisioning/dashboards/dashboard.yml
```

## Production Checklist

- [ ] Changer le mot de passe Grafana par défaut
- [ ] Configurer les alertes Prometheus (email/Slack)
- [ ] Configurer les sauvegardes automatiques
- [ ] Configurer les logs rotation
- [ ] Configurer HTTPS (reverse proxy)
- [ ] Configurer l'authentification Grafana
- [ ] Monitorer l'utilisation des ressources
- [ ] Documenter les procédures de rollback

## Support

Pour toute question ou problème :
1. Vérifier les logs : `docker-compose logs`
2. Vérifier les métriques : http://localhost:9090
3. Consulter la documentation : `docs/`

