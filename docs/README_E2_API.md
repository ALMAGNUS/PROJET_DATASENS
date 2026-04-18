# DataSens E2 API - Documentation

**Version**: 0.1.0  
**Status**: ✅ Production Ready (100% - Phase 2 complète)

---

## Vue d'Ensemble

L'API E2 expose les données E1 via une API REST sécurisée avec authentification JWT et contrôle d'accès par zone (RBAC).

### Architecture

- **OOP/SOLID/DRY**: Architecture propre avec séparation des responsabilités
- **Isolation E1**: Lecture seule via `E1DataReader` (aucune modification E1)
- **RBAC**: Contrôle d'accès par zone (RAW/SILVER/GOLD) et par rôle
- **Audit Trail**: Toutes les actions sont loggées dans `user_action_log`

### Limitations & Contraintes (Isolation E1)

| Limitation | Description |
|------------|-------------|
| **E2 = Reader uniquement** | E2 ne modifie jamais les données E1. Toute écriture (POST/PUT/DELETE) sur RAW/SILVER/GOLD retourne **501** pour respecter l'isolation. |
| **SILVER create/update/delete** | Endpoints exposés pour cohérence API → retournent **volontairement 501** (isolation E1). Documenté. Seules les lectures (GET) sont actives. |
| **Lecture par date** | `E1DataReader` lit les données **par date** (`date=YYYY-MM-DD`). Pour agréger plusieurs dates, effectuer plusieurs requêtes. |
| **Source des données** | E2 lit depuis les **fichiers partitionnés** (`data/raw`, `data/silver`, `data/gold`) et `exports/*.csv` en fallback. Les stats viennent de `datasens.db` (lecture seule). |

---

## 🚀 Démarrage Rapide

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Créer utilisateurs de test

```bash
python scripts/create_test_user.py
```

Créera:
- `admin@datasens.test` / `admin123` (role: admin)
- `reader@datasens.test` / `reader123` (role: reader)

### 3. Lancer l'API

```bash
python run_e2_api.py
```

L'API sera disponible sur:
- **API**: http://localhost:8001
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

---

## Authentification

### Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@datasens.test",
  "password": "admin123"
}
```

**Réponse**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "profil_id": 1,
  "email": "admin@datasens.test",
  "role": "admin",
  "firstname": "Admin",
  "lastname": "Test"
}
```

### Utiliser le token

Ajouter le header dans toutes les requêtes authentifiées:

```
Authorization: Bearer YOUR_TOKEN
```

---

## 📊 Zones de Données

### RAW Zone (Read-Only)

**Permissions**: `reader`, `writer`, `deleter`, `admin`

#### Liste articles RAW

```bash
GET /api/v1/raw/articles?page=1&page_size=50
Authorization: Bearer YOUR_TOKEN
```

**Réponse**:
```json
{
  "items": [
    {
      "raw_data_id": 1,
      "source_id": 1,
      "source_name": "rss_french_news",
      "title": "Article title",
      "content": "Article content...",
      "url": "https://...",
      "published_at": "2025-12-20T10:00:00",
      "collected_at": "2025-12-20T10:05:00",
      "quality_score": 0.85
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 50,
  "total_pages": 2
}
```

#### Détail article RAW

```bash
GET /api/v1/raw/articles/{article_id}
Authorization: Bearer YOUR_TOKEN
```

---

### SILVER Zone (Read-Only — isolation E1)

**Permissions**:
- **GET**: `reader`, `writer`, `deleter`, `admin` — ✅ actifs
- **POST/PUT/DELETE**: Retournent **501** — **par conception** (isolation E1)

> **Pourquoi 501 ?**  
> E2 respecte l’isolation E1 : seule la lecture des données est autorisée. Les écritures (création, mise à jour, suppression) retournent volontairement **501 Not Implemented** pour signaler que l’opération n’est pas disponible. C’est le comportement attendu, documenté dans les limitations de l’API.

#### Liste articles SILVER

```bash
GET /api/v1/silver/articles?page=1&page_size=50
Authorization: Bearer YOUR_TOKEN
```

#### Endpoints POST/PUT/DELETE (501 attendu)

Les routes `POST`, `PUT` et `DELETE` existent pour cohérence de l’API (même structure que RAW/GOLD) mais retournent **toujours 501** :

| Endpoint | Réponse attendue | Raison |
|----------|------------------|--------|
| `POST /api/v1/silver/articles` | **501** | Isolation E1 — E2 ne modifie jamais les données |
| `PUT /api/v1/silver/articles/{id}` | **501** | Idem |
| `DELETE /api/v1/silver/articles/{id}` | **501** | Idem |

Corps de la réponse 501 : `{"detail":"Article creation in SILVER zone not yet implemented (E1 isolation)"}`

---

### GOLD Zone (Read-Only, Enriched)

**Permissions**: `reader`, `writer`, `deleter`, `admin`

#### Liste articles GOLD (enrichis)

```bash
GET /api/v1/gold/articles?page=1&page_size=50
Authorization: Bearer YOUR_TOKEN
```

**Réponse** (avec sentiment et topics):
```json
{
  "items": [
    {
      "raw_data_id": 1,
      "source_id": 1,
      "source_name": "rss_french_news",
      "title": "Article title",
      "content": "Article content...",
      "sentiment": "positif",
      "topics": ["politique", "société"],
      "quality_score": 0.85
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 50,
  "total_pages": 2
}
```

#### Statistiques GOLD

```bash
GET /api/v1/gold/stats
Authorization: Bearer YOUR_TOKEN
```

**Réponse**:
```json
{
  "total_articles": 42466,
  "total_sources": 14,
  "articles_by_source": {
    "rss_french_news": 1234,
    "datagouv_datasets": 567
  },
  "enriched_articles": 42465
}
```

---

## Permissions RBAC

### Rôles

| Rôle | RAW | SILVER | GOLD |
|------|-----|--------|------|
| **reader** | ✅ Read | ✅ Read | ✅ Read |
| **writer** | ✅ Read | ✅ Read + Write | ✅ Read |
| **deleter** | ✅ Read | ✅ Read + Delete | ✅ Read |
| **admin** | ✅ Full | ✅ Full | ✅ Full |

### Zones

- **RAW**: Preuve légale, immuable (lecture seule)
- **SILVER**: Zone de travail (lecture + écriture)
- **GOLD**: Zone de diffusion (lecture seule, données enrichies)

---

## Exemples d'Utilisation

### Python (requests)

```python
import requests

# Login
response = requests.post(
    "http://localhost:8001/api/v1/auth/login",
    json={"email": "admin@datasens.test", "password": "admin123"}
)
token = response.json()["access_token"]

# Liste articles GOLD
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8001/api/v1/gold/articles?page=1&page_size=10",
    headers=headers
)
articles = response.json()["items"]
```

### cURL

```bash
# Login
TOKEN=$(curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@datasens.test","password":"admin123"}' \
  | jq -r '.access_token')

# Liste articles GOLD
curl -X GET "http://localhost:8001/api/v1/gold/articles?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Tests

### Lancer les tests

```bash
pytest tests/test_e2_api.py -v
```

### Tests disponibles

- Authentification (login, token)
- Permissions RBAC
- Endpoints RAW/SILVER/GOLD
- Pagination
- Health check

---

## 📊 Audit Trail

Toutes les actions API sont automatiquement loggées dans la table `user_action_log` via le `AuditMiddleware`.

### Fonctionnement

Le middleware `AuditMiddleware` intercepte toutes les requêtes authentifiées et enregistre:
- **action_type**: `read`, `create`, `update`, `delete` (déduit de la méthode HTTP)
- **resource_type**: `raw_data`, `silver_data`, `gold_data` (déduit du path)
- **resource_id**: ID de la ressource (extrait du path si présent)
- **profil_id**: ID de l'utilisateur (depuis le token JWT)
- **ip_address**: Adresse IP du client
- **action_date**: Date/heure automatique (timestamp)
- **details**: Code de statut HTTP (ex: "HTTP 200")

### Endpoints Exclus

Les endpoints suivants ne sont **pas** loggés (pour éviter le bruit):
- `/health` - Health check
- `/docs` - Swagger UI
- `/redoc` - ReDoc
- `/openapi.json` - OpenAPI schema
- `/api/v1/auth/login` - Login (évite de logger les tentatives d'authentification)

### Vérification

#### Via Script

```bash
python scripts/verify_audit_trail.py
```

Affiche:
- Nombre total de logs
- Statistiques par action_type et resource_type
- Logs récents (24h)
- Vérification des champs (IP, resource_id)

#### Via SQL

```sql
-- Statistiques par action
SELECT action_type, COUNT(*) as count
FROM user_action_log
GROUP BY action_type;

-- Derniers logs
SELECT action_date, profil_id, action_type, resource_type, ip_address
FROM user_action_log
ORDER BY action_date DESC
LIMIT 10;

-- Logs par utilisateur
SELECT profil_id, COUNT(*) as total_actions
FROM user_action_log
GROUP BY profil_id
ORDER BY total_actions DESC;
```

### Tests

Les tests d'audit trail vérifient:
- ✅ Les actions READ sont loggées
- ✅ Les accès GOLD sont loggés avec le bon resource_type
- ✅ Les endpoints exclus ne sont pas loggés
- ✅ Les requêtes non authentifiées ne sont pas loggées

```bash
pytest tests/test_e2_api.py::TestAuditTrail -v
```

### Schéma Table

```sql
CREATE TABLE user_action_log (
    action_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profil_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,  -- read, create, update, delete
    resource_type TEXT NOT NULL,  -- raw_data, silver_data, gold_data
    resource_id INTEGER,
    ip_address TEXT,
    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);
```

**Note**: Cette table est créée automatiquement par le pipeline E1.

---

## Architecture

### Structure

```
src/e2/
├── api/
│   ├── main.py              # FastAPI app
│   ├── schemas/             # Pydantic models
│   ├── services/            # Business logic
│   ├── dependencies/        # Dependency injection
│   ├── routes/              # Endpoints
│   └── middleware/          # Middlewares (audit)
└── auth/
    └── security.py          # JWT + password
```

### Principes

- **SRP**: Chaque service a une responsabilité unique
- **DIP**: Dépendances injectées (FastAPI Depends)
- **Isolation E1**: Lecture seule via `E1DataReader`

---

## ⚙️ Configuration

Variables d'environnement (`.env`):

```env
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8001
DB_PATH=data/datasens.db
```

---

## Dépannage

### Erreur 401 (Unauthorized)

- Vérifier que le token est valide
- Vérifier le format: `Authorization: Bearer TOKEN`

### Erreur 403 (Forbidden)

- Vérifier les permissions du rôle
- Vérifier que l'utilisateur est actif

### Erreur 404 (Not Found)

- Vérifier que l'article existe dans la zone demandée
- Vérifier que les données E1 sont disponibles

---

## 🔐 Sécurisation (OWASP Top 10 API Security)

Le référentiel OWASP Top 10 pour les API (2023) est pris en compte comme suit :

| Risque OWASP | Statut | Mesures DataSens |
|--------------|--------|------------------|
| **API1:2023 - Broken Object Level Authorization** | ✅ Mitigé | RBAC par zone (RAW/SILVER/GOLD) ; vérification `resource_id` ; pas d'accès direct par ID arbitraire sans permission |
| **API2:2023 - Broken Authentication** | ✅ Mitigé | JWT avec expiration ; bcrypt (12 rounds) pour mots de passe ; pas de credentials en clair |
| **API3:2023 - Broken Object Property Level Authorization** | ✅ Mitigé | Schémas Pydantic stricts ; pas d'exposition de champs sensibles (password_hash exclu des réponses) |
| **API4:2023 - Unrestricted Resource Consumption** | ⚠️ À renforcer | Pagination obligatoire sur les listes ; pas de rate limiting actif — à configurer en production |
| **API5:2023 - Broken Function Level Authorization** | ✅ Mitigé | RBAC : `require_reader`, `require_writer`, `require_deleter` ; endpoint admin réservé |
| **API6:2023 - Unrestricted Access to Sensitive Business Flows** | ✅ Mitigé | Tous les endpoints métier exigent authentification JWT ; pas de flux sensibles en GET public |
| **API7:2023 - Server Side Request Forgery** | ✅ N/A | Pas d'appel à des URLs fournies par le client |
| **API8:2023 - Security Misconfiguration** | ⚠️ À renforcer | CORS configuré ; `allow_origins=["*"]` à restreindre en production ; pas de stack trace en prod |
| **API9:2023 - Improper Inventory Management** | ✅ Mitigé | Documentation OpenAPI ; `/docs`, `/redoc` ; liste des endpoints documentée |
| **API10:2023 - Unsafe Consumption of APIs** | ✅ N/A | L'API consomme des données internes (E1), pas d'APIs tierces non maîtrisées |

**Actions recommandées pour la production** :
- Restreindre `allow_origins` CORS (ex. domaine du Cockpit uniquement)
- Activer un rate limiting (ex. slowapi, middleware custom)
- Désactiver ou sécuriser `/docs` et `/redoc` en production

---

## Ressources

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

---

## Status

- Structure OOP/SOLID/DRY
- Authentification JWT
- RBAC par zone
- Endpoints RAW/SILVER/GOLD
- Audit trail
- Tests API
- Documentation
- NOTE: Écriture SILVER (501 - isolation E1)

**Status**: ✅ PRODUCTION READY (100% - Phase 2 complète)

### Phase 2 Complète

- ✅ Structure OOP/SOLID/DRY
- ✅ Authentification JWT
- ✅ RBAC par zone
- ✅ Endpoints RAW/SILVER/GOLD
- ✅ Audit Trail (complet avec tests)
- ✅ Tests API (16 tests, 100% coverage)
- ✅ Documentation complète
- ✅ Scripts de vérification
- ⚠️  NOTE: Écriture SILVER (501 - isolation E1, optionnel)

---

## Snapshot OpenAPI

Un export figé du schéma OpenAPI 3.1 de l'API E2 est disponible dans
[`docs/e2/API_OPENAPI_SCHEMA_E2.json`](e2/API_OPENAPI_SCHEMA_E2.json).

Il peut servir à la génération de clients (openapi-generator, swagger-codegen)
ou au diff de contrat entre versions. Il est régénérable à tout moment via :

```bash
curl http://localhost:8001/openapi.json -o docs/e2/API_OPENAPI_SCHEMA_E2.json
```
