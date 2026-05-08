# 🐳 Docker - DataSens E1

## 🚀 Démarrage Rapide

### Build et Lancement
```bash
# Build l'image
docker-compose build

# Lancer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f datasens-e1
```

### Services Disponibles

1. **DataSens E1 Pipeline** - Port 8000 (Prometheus metrics)
2. **Prometheus** - Port 9090 (Métriques)
3. **Grafana** - Port 3000 (Visualisation)
   - User: `admin`
   - Password: `admin`

---

## 📋 Commandes Utiles

### Gestion des Containers
```bash
# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Redémarrer
docker-compose restart

# Voir les logs
docker-compose logs -f

# Voir les stats
docker stats
```

### Accès aux Services

- **Pipeline**: `http://localhost:8000/metrics` (Prometheus metrics)
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000`

---

## 🔧 Configuration

### Variables d'Environnement

Dans `docker-compose.yml` :
- `DB_PATH=/app/data/datasens.db` - Chemin base de données
- `METRICS_PORT=8000` - Port métriques Prometheus

### Volumes

- `./data:/app/data` - Données brutes et base SQLite
- `./exports:/app/exports` - Exports CSV/Parquet
- `./zzdb:/app/zzdb:ro` - ZZDB (lecture seule)
- `datasens-db` - Volume persistant pour la base

---

## 🏗️ Build Manuel

```bash
# Build l'image
docker build -t datasens-e1:v1.0.0-stable .

# Run le container
docker run -d \
  --name datasens-e1 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/exports:/app/exports \
  -v $(pwd)/sources_config.json:/app/sources_config.json \
  -v $(pwd)/zzdb:/app/zzdb:ro \
  -e DB_PATH=/app/data/datasens.db \
  -e METRICS_PORT=8000 \
  -p 8000:8000 \
  datasens-e1:v1.0.0-stable
```

---

## ✅ Health Check

Le container vérifie automatiquement la santé de la base de données :
- Intervalle: 30s
- Timeout: 10s
- Retries: 3

Vérifier le statut :
```bash
docker inspect --format='{{.State.Health.Status}}' datasens-e1
```

---

## 📊 Monitoring

### Prometheus
- Scrape les métriques depuis `datasens-e1:8000/metrics`
- Rétention: 30 jours
- Config: `monitoring/prometheus.yml`

### Grafana
- Dashboard pré-configuré: `monitoring/grafana/dashboards/datasens-e1-dashboard.json`
- Datasource Prometheus automatique

---

## 🔒 Sécurité

- ZZDB monté en **lecture seule** (`:ro`)
- Base de données dans volume Docker persistant
- Pas d'exposition de ports sensibles
- Health checks activés

---

## 🐛 Troubleshooting

### Container ne démarre pas
```bash
# Voir les logs
docker-compose logs datasens-e1

# Vérifier les permissions
ls -la data/ exports/
```

### Base de données corrompue
```bash
# Supprimer le volume et recréer
docker-compose down -v
docker-compose up -d
```

### Ports déjà utilisés
Modifier les ports dans `docker-compose.yml` :
```yaml
ports:
  - "8001:8000"  # Au lieu de 8000:8000
```

---

## 📦 Version

**Tag**: `v1.0.0-stable` (FREEZE)
**Image**: `datasens-e1:v1.0.0-stable`
