# 🚀 Build & Deploy - DataSens E1

## ✅ Vérifications effectuées

Tous les tests passent :
- ✅ Imports Python OK
- ✅ Métriques Prometheus OK
- ✅ Fichiers présents
- ✅ Dockerfile valide
- ✅ Docker & Docker Compose installés

## 📦 Build Local

### 1. Test build Docker

```bash
# Build l'image
docker build -t datasens-e1:latest .

# Vérifier que l'image est créée
docker images | grep datasens-e1
```

### 2. Test docker-compose

```bash
# Vérifier la configuration
docker-compose config

# Build tous les services
docker-compose build

# Lancer (optionnel, pour test)
docker-compose up -d

# Voir les logs
docker-compose logs -f datasens-e1

# Arrêter
docker-compose down
```

## 🔄 Push vers GitHub

### Prérequis

1. **Repository GitHub créé**
   ```bash
   # Si pas encore fait
   git remote add origin https://github.com/<username>/<repo>.git
   ```

2. **GitHub Container Registry activé**
   - Aller dans Settings > Packages
   - Activer GitHub Container Registry

### Push du code

```bash
# 1. Ajouter tous les fichiers
git add .

# 2. Commit
git commit -m "feat: Add Docker, Prometheus, Grafana monitoring and CI/CD"

# 3. Push
git push origin main
```

### CI/CD automatique

Le pipeline GitHub Actions (`.github/workflows/ci-cd.yml`) va automatiquement :
1. ✅ Tester le code (lint + tests)
2. ✅ Build l'image Docker
3. ✅ Push vers `ghcr.io/<username>/<repo>`
4. ✅ Déployer (si sur `main`)

### Push manuel de l'image

Si vous voulez push manuellement :

```bash
# 1. Login à GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# 2. Tag l'image
docker tag datasens-e1:latest ghcr.io/<username>/<repo>:latest

# 3. Push
docker push ghcr.io/<username>/<repo>:latest
```

## 🎯 Prochaines étapes

1. **Push le code sur GitHub**
   ```bash
   git add .
   git commit -m "feat: Production-ready monolith with Docker, Prometheus, Grafana"
   git push origin main
   ```

2. **Vérifier le CI/CD**
   - Aller dans GitHub > Actions
   - Vérifier que le workflow passe

3. **Tester en production**
   ```bash
   # Pull l'image depuis GitHub
   docker pull ghcr.io/<username>/<repo>:latest
   
   # Lancer avec docker-compose
   docker-compose up -d
   ```

4. **Accéder aux services**
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)
   - Metrics: http://localhost:8000/metrics

## 📝 Notes

- Le `.gitignore` exclut les données (data/, exports/, *.db)
- Les secrets doivent être dans des variables d'environnement
- Le CI/CD nécessite un `GITHUB_TOKEN` (automatique dans Actions)

