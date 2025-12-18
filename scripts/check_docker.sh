#!/bin/bash
# Script de vérification Docker (pour Linux/Mac)
# Pour Windows, utiliser check_docker.ps1

echo "=========================================="
echo "VERIFICATION DOCKER - DataSens E1"
echo "=========================================="
echo ""

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker n'est pas installe"
    exit 1
fi
echo "[OK] Docker installe"

# Vérifier Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] Docker Compose n'est pas installe"
    exit 1
fi
echo "[OK] Docker Compose installe"

# Test syntaxe docker-compose.yml
echo ""
echo "[TEST] Verification syntaxe docker-compose.yml..."
docker-compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "[OK] docker-compose.yml syntaxe valide"
else
    echo "[ERROR] docker-compose.yml a des erreurs"
    docker-compose config
    exit 1
fi

# Test build (sans lancer)
echo ""
echo "[TEST] Test build Dockerfile..."
docker build -t datasens-e1:test . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "[OK] Dockerfile build reussi"
    docker rmi datasens-e1:test > /dev/null 2>&1
else
    echo "[ERROR] Dockerfile build echoue"
    exit 1
fi

echo ""
echo "=========================================="
echo "[OK] TOUS LES TESTS DOCKER PASSENT"
echo "=========================================="

