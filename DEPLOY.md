# 🚀 Guide de Déploiement - DataSens E1

## ✅ Prérequis

- **Docker** 20.10+ installé
- **Docker Compose** 2.0+ installé
- **4GB RAM** minimum
- **10GB espace disque** libre

### Vérifier l'installation

```bash
# Windows PowerShell
docker --version
docker-compose --version
```

---

## 🎯 Déploiement Local (Docker Compose)

### 1. Configuration

Vérifiez que `sources_config.json` est configuré :

```bash
# Vérifier le fichier
cat sources_config.json
```

### 2. Lancer le déploiement

```bash
# Build et démarrage de tous les services
docker-compose up -d --build

# Vérifier que tout fonctionne
docker-compose ps
```

### 3. Accéder aux services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Pipeline E1** | http://localhost:8000/metrics | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | `admin` / `admin` |

⚠️ **Important** : Changez le mot de passe Grafana au premier login !

### 4. Voir les logs

```bash
# Logs du pipeline
docker-compose logs -f datasens-e1

# Logs de tous les services
docker-compose logs -f
```

### 5. Arrêter les services

```bash
# Arrêter (garder les données)
docker-compose stop

# Arrêter et supprimer les conteneurs (garder les volumes)
docker-compose down

# Tout supprimer (y compris les volumes)
docker-compose down -v
```

---

## 🐳 Déploiement avec Docker uniquement

### Build l'image

```bash
docker build -t datasens-e1:latest .
```

### Lancer le conteneur

```bash
docker run -d \
  --name datasens-e1 \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/exports:/app/exports \
  -v $(pwd)/sources_config.json:/app/sources_config.json \
  -e DB_PATH=/app/data/datasens.db \
  -e METRICS_PORT=8000 \
  datasens-e1:latest
```

### Vérifier

```bash
# Voir les logs
docker logs -f datasens-e1

# Vérifier les métriques
curl http://localhost:8000/metrics
```

---

## ☁️ Déploiement Production

### Option 1: Serveur avec Docker

1. **Cloner le projet sur le serveur**

```bash
git clone <votre-repo> /opt/datasens
cd /opt/datasens
```

2. **Configurer les variables d'environnement**

Créez un fichier `.env` :

```bash
DB_PATH=/app/data/datasens.db
METRICS_PORT=8000
GRAFANA_ADMIN_PASSWORD=votre_mot_de_passe_securise
```

3. **Lancer avec docker-compose**

```bash
docker-compose -f docker-compose.yml up -d --build
```

4. **Configurer un reverse proxy (Nginx)**

Exemple de configuration Nginx :

```nginx
server {
    listen 80;
    server_name datasens.example.com;

    location /metrics {
        proxy_pass http://localhost:8000;
    }

    location /prometheus {
        proxy_pass http://localhost:9090;
    }

    location / {
        proxy_pass http://localhost:3000;
    }
}
```

### Option 2: Cloud (AWS, GCP, Azure)

#### AWS ECS / Fargate

1. Push l'image vers ECR
2. Créer un task definition
3. Lancer le service

#### Google Cloud Run

```bash
# Build et push
gcloud builds submit --tag gcr.io/PROJECT_ID/datasens-e1

# Déployer
gcloud run deploy datasens-e1 \
  --image gcr.io/PROJECT_ID/datasens-e1 \
  --platform managed \
  --port 8000
```

#### Azure Container Instances

```bash
az container create \
  --resource-group datasens-rg \
  --name datasens-e1 \
  --image datasens-e1:latest \
  --ports 8000
```

---

## 🔄 CI/CD avec GitHub Actions

Le workflow CI/CD est déjà configuré dans `.github/workflows/ci-cd.yml`.

### Déploiement automatique

1. Push sur `main` → Build automatique
2. Image Docker poussée vers GitHub Container Registry
3. Déploiement automatique (à configurer selon votre infrastructure)

### Déploiement manuel

```bash
# Build l'image
docker build -t datasens-e1:latest .

# Tag pour le registry
docker tag datasens-e1:latest ghcr.io/USERNAME/datasens-e1:latest

# Push
docker push ghcr.io/USERNAME/datasens-e1:latest
```

---

## 📊 Monitoring

### Métriques Prometheus

Accédez à http://localhost:9090 et explorez les métriques :

- `datasens_pipeline_runs_total` : Nombre d'exécutions
- `datasens_articles_extracted_total` : Articles extraits
- `datasens_articles_analyzed_total` : Articles analysés
- `datasens_pipeline_duration_seconds` : Durée d'exécution

### Dashboards Grafana

1. Connectez-vous à http://localhost:3000
2. Le dashboard `DataSens E1` est déjà provisionné
3. Visualisez les métriques en temps réel

---

## 🔧 Maintenance

### Mettre à jour le code

```bash
# Rebuild l'image
docker-compose build datasens-e1

# Redémarrer
docker-compose restart datasens-e1
```

### Sauvegarder les données

```bash
# Sauvegarder la base de données
docker-compose exec datasens-e1 cp /app/data/datasens.db /app/data/datasens.db.backup

# Sauvegarder les exports
docker-compose exec datasens-e1 tar -czf /app/exports/backup.tar.gz /app/exports/*.csv /app/exports/*.parquet
```

### Restaurer les données

```bash
# Restaurer la base de données
docker-compose exec datasens-e1 cp /app/data/datasens.db.backup /app/data/datasens.db
```

---

## 🐛 Troubleshooting

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

# Vérifier la configuration
docker-compose exec grafana cat /etc/grafana/provisioning/dashboards/dashboard.yml
```

### Problème de permissions

```bash
# Donner les permissions au répertoire data
chmod -R 755 data/
chmod -R 755 exports/
```

---

## ✅ Checklist Production

Avant de déployer en production :

- [ ] Changer le mot de passe Grafana par défaut
- [ ] Configurer les alertes Prometheus (email/Slack)
- [ ] Configurer les sauvegardes automatiques
- [ ] Configurer les logs rotation
- [ ] Configurer HTTPS (reverse proxy)
- [ ] Configurer l'authentification Grafana
- [ ] Monitorer l'utilisation des ressources
- [ ] Documenter les procédures de rollback
- [ ] Tester la restauration des sauvegardes

---

## 📞 Support

Pour toute question :

1. Vérifier les logs : `docker-compose logs`
2. Vérifier les métriques : http://localhost:9090
3. Consulter la documentation : `docs/DEPLOYMENT.md`

---

**C'est tout ! Votre pipeline E1 est prêt à être déployé.** 🎉
