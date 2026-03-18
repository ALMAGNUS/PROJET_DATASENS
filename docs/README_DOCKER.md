# 🐳 DataSens E1 - Docker & Monitoring

## Architecture Production

DataSens E1 est maintenant un **monolithe production-ready** avec :
- ✅ Docker containerisation
- ✅ Prometheus monitoring
- ✅ Grafana dashboards
- ✅ CI/CD automatisé

## Quick Start

```bash
# 1. Lancer tous les services
docker-compose up -d

# 2. Vérifier les services
docker-compose ps

# 3. Accéder aux interfaces
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
# - Metrics: http://localhost:8000/metrics
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| `datasens-e1` | 8000 | Pipeline principal + métriques |
| `prometheus` | 9090 | Collecte de métriques |
| `grafana` | 3000 | Visualisation |

## Métriques Prometheus

Le pipeline expose automatiquement :
- Nombre d'articles collectés/chargés/taggés
- Durée d'exécution par étape
- Taux d'enrichissement
- Erreurs par source

## CI/CD

Le pipeline GitHub Actions :
1. Teste le code (lint + tests)
2. Build l'image Docker
3. Push vers GitHub Container Registry
4. Déploie automatiquement (si sur `main`)

Voir `.github/workflows/ci-cd.yml` pour plus de détails.

## Documentation Complète

Voir `docs/DEPLOYMENT.md` pour la documentation complète de déploiement.

