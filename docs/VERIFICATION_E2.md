# Vérification E2 API - Checklist Complète

## Tests Automatiques

### 1. Tests Unitaires API

```bash
# Lancer tous les tests E2
python -m pytest tests/test_e2_api.py -v

# Résultat attendu : 12/12 tests passent
```

**Tests couverts** :
- ✅ Authentification (login, token)
- ✅ Permissions RBAC (reader, writer, deleter, admin)
- ✅ Endpoints RAW/SILVER/GOLD
- ✅ Pagination
- ✅ Health check

### 2. Tests Manuels Rapides

#### A. Démarrer l'API

```bash
python run_e2_api.py
```

**Vérifier** :
- ✅ API démarre sur http://localhost:8001
- ✅ Swagger UI accessible : http://localhost:8001/docs
- ✅ Health check : http://localhost:8001/health → `{"status": "ok"}`

#### B. Test Authentification

```bash
# Login
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'

# Vérifier : Status 200, token retourné
```

#### C. Test Endpoints Protégés

```bash
# Récupérer token
TOKEN=$(curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}' \
  | jq -r '.access_token')

# Test RAW articles
curl -X GET "http://localhost:8001/api/v1/raw/articles?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# Test GOLD articles
curl -X GET "http://localhost:8001/api/v1/gold/articles?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# Test GOLD stats
curl -X GET "http://localhost:8001/api/v1/gold/stats" \
  -H "Authorization: Bearer $TOKEN"
```

**Vérifier** :
- ✅ Status 200 pour toutes les requêtes
- ✅ Données retournées (items, total, page)
- ✅ Pas d'erreur 401/403

### 3. Vérification Métriques Prometheus

```bash
# Vérifier endpoint métriques
curl http://localhost:8001/metrics

# Vérifier présence métriques :
# - datasens_e2_api_requests_total
# - datasens_e2_api_authentications_total
# - datasens_e2_api_zone_access_total
# - datasens_e2_api_request_duration_seconds
```

**Vérifier** :
- ✅ Endpoint `/metrics` accessible
- ✅ Format Prometheus valide
- ✅ Métriques présentes

### 4. Vérification Audit Trail

```python
import sqlite3
from pathlib import Path
import os

db_path = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Vérifier logs d'audit
cursor.execute("""
    SELECT COUNT(*) as total,
           action_type,
           resource_type
    FROM user_action_log
    GROUP BY action_type, resource_type
    ORDER BY total DESC
    LIMIT 10
""")

logs = cursor.fetchall()
print("Audit logs:")
for log in logs:
    print(f"  {log[1]} / {log[2]}: {log[0]} actions")

conn.close()
```

**Vérifier** :
- ✅ Table `user_action_log` contient des entrées
- ✅ Actions loggées (read, create, update, delete)
- ✅ Resource types corrects (raw_data, silver_data, gold_data)

## Checklist Complète

### Fonctionnalités Core

- [ ] API démarre sans erreur
- [ ] Swagger UI accessible
- [ ] Health check fonctionne
- [ ] Authentification JWT fonctionne
- [ ] Token valide pour requêtes protégées
- [ ] RBAC permissions respectées

### Endpoints

- [ ] `POST /api/v1/auth/login` → Token JWT
- [ ] `GET /api/v1/raw/articles` → Liste articles RAW
- [ ] `GET /api/v1/raw/articles/{id}` → Détail article RAW
- [ ] `GET /api/v1/silver/articles` → Liste articles SILVER
- [ ] `GET /api/v1/gold/articles` → Liste articles GOLD
- [ ] `GET /api/v1/gold/stats` → Statistiques GOLD

### Sécurité

- [ ] Endpoints protégés retournent 401 sans token
- [ ] Endpoints protégés retournent 403 avec mauvais rôle
- [ ] Passwords hashés (bcrypt)
- [ ] Tokens JWT valides et expirables

### Monitoring

- [ ] Endpoint `/metrics` accessible
- [ ] Métriques Prometheus valides
- [ ] Métriques business (auth, zones) fonctionnent

### Audit

- [ ] Actions loggées dans `user_action_log`
- [ ] IP addresses capturées
- [ ] Resource types corrects
- [ ] Action types corrects (read, create, update, delete)

### Isolation E1

- [ ] Aucune modification de `src/e1/`
- [ ] Lecture seule via `E1DataReader`
- [ ] Pas de dépendance bidirectionnelle

## Script de Vérification Automatique

```bash
# Vérification complète E2
python scripts/verify_e2.py
```

**Status attendu** : ✅ Tous les checks passent
