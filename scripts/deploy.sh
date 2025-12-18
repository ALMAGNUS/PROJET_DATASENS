#!/bin/bash
# Script de déploiement DataSens E1 (Linux/Mac)
# Usage: ./scripts/deploy.sh

echo ""
echo "========================================"
echo "  DataSens E1 - Déploiement"
echo "========================================"
echo ""

# Vérifier Docker
echo "[1/5] Vérification de Docker..."
if command -v docker &> /dev/null; then
    echo "  ✅ $(docker --version)"
else
    echo "  ❌ Docker n'est pas installé"
    exit 1
fi

# Vérifier Docker Compose
echo ""
echo "[2/5] Vérification de Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "  ✅ $(docker-compose --version)"
else
    echo "  ❌ Docker Compose n'est pas installé"
    exit 1
fi

# Vérifier les fichiers nécessaires
echo ""
echo "[3/5] Vérification des fichiers..."
required_files=("Dockerfile" "docker-compose.yml" "sources_config.json" "requirements.txt")
all_present=true

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file manquant"
        all_present=false
    fi
done

if [ "$all_present" = false ]; then
    echo ""
    echo "❌ Fichiers manquants. Arrêt du déploiement."
    exit 1
fi

# Build et démarrage
echo ""
echo "[4/5] Build et démarrage des services..."
echo "  ⏳ Cela peut prendre quelques minutes..."

if docker-compose up -d --build; then
    echo "  ✅ Services démarrés avec succès"
else
    echo "  ❌ Erreur lors du démarrage"
    exit 1
fi

# Vérifier les services
echo ""
echo "[5/5] Vérification des services..."
sleep 5

docker-compose ps

# Afficher les URLs
echo ""
echo "========================================"
echo "  Services disponibles:"
echo "========================================"
echo "  📊 Pipeline E1:    http://localhost:8000/metrics"
echo "  📈 Prometheus:    http://localhost:9090"
echo "  📉 Grafana:       http://localhost:3000"
echo "     (admin / admin - à changer!)"
echo ""
echo "  📋 Voir les logs: docker-compose logs -f"
echo "  🛑 Arrêter:        docker-compose down"
echo ""
