# 🚀 Déploiement Rapide - DataSens E1

## ✅ Vérification Pré-Déploiement

✅ Docker installé (version 28.5.1)  
✅ Docker Compose configuré  
✅ Dockerfile présent  
✅ docker-compose.yml présent  
✅ Configuration Prometheus/Grafana prête  
✅ CI/CD GitHub Actions configuré  

---

## 🎯 Déploiement en 3 Étapes

### Option 1: Script Automatique (Recommandé)

**Windows PowerShell:**
```powershell
.\scripts\deploy.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Option 2: Manuel

```bash
# 1. Build et démarrage
docker-compose up -d --build

# 2. Vérifier les services
docker-compose ps

# 3. Voir les logs
docker-compose logs -f datasens-e1
```

---

## 🌐 Accès aux Services

Une fois déployé, accédez à :

| Service | URL | Description |
|---------|-----|-------------|
| **Pipeline E1** | http://localhost:8000/metrics | Métriques Prometheus |
| **Prometheus** | http://localhost:9090 | Interface Prometheus |
| **Grafana** | http://localhost:3000 | Dashboards (admin/admin) |

---

## 📋 Commandes Utiles

```bash
# Voir les logs
docker-compose logs -f

# Arrêter les services
docker-compose stop

# Redémarrer
docker-compose restart

# Tout supprimer
docker-compose down -v
```

---

## 📚 Documentation Complète

- **Guide complet** : `DEPLOY.md`
- **Documentation détaillée** : `docs/DEPLOYMENT.md`
- **Architecture** : `docs/ARCHITECTURE.md`

---

**Prêt à déployer ! Lancez `.\scripts\deploy.ps1` ou `docker-compose up -d --build`** 🎉
