# 🏗️ FastAPI - Architecture Unifiée (SQLite + PySpark + RBAC)

## 🎯 Objectif

**FastAPI comme couche API unique** pour accéder à :
- ✅ **SQLite (E1)** : Données structurées, CRUD
- ✅ **PySpark (E2)** : Big Data processing, analytics
- ✅ **RBAC** : Permissions par zone (RAW/SILVER/GOLD)

---

## 📊 Architecture Complète

### **Vue d'Ensemble**

```
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI (Couche API)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Authentication & Authorization (RBAC)                │   │
│  │  - JWT Tokens                                        │   │
│  │  - Role-based permissions (reader/writer/deleter/admin)│   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  RAW Endpoints   │         │  SILVER Endpoints│         │
│  │  (Read-only)    │         │  (Read/Write)    │         │
│  └──────────────────┘         └──────────────────┘         │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  GOLD Endpoints  │         │  PYSPARK Endpoints│        │
│  │  (Read-only)    │         │  (Analytics)     │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
           │                              │
           │                              │
    ┌──────▼──────┐              ┌───────▼────────┐
    │   SQLite    │              │   PySpark      │
    │  (datasens.db)│              │  (Big Data)    │
    │             │              │                │
    │  - RAW      │              │  - Analytics   │
    │  - SILVER   │              │  - Aggregations│
    │  - GOLD     │              │  - ML Pipeline │
    └─────────────┘              └────────────────┘
           │                              │
           │                              │
    ┌──────▼──────────────────────────────▼──────┐
    │         Parquet Buffer (data/gold/)         │
    │         (Connexion E1 → E2)                 │
    └─────────────────────────────────────────────┘
```

---

## 🔄 Flux de Données

### **1. Accès SQLite (E1) via FastAPI**

```
Client → FastAPI → Repository → SQLite
         (RBAC)    (Pattern)   (datasens.db)
```

**Endpoints** :
- `GET /api/v1/raw/articles` → SQLite `raw_data`
- `GET /api/v1/silver/articles` → SQLite `raw_data` + `document_topic`
- `GET /api/v1/gold/articles` → SQLite `raw_data` + `document_topic` + `model_output`

---

### **2. Accès PySpark (E2) via FastAPI**

```
Client → FastAPI → PySpark Adapter → Parquet → Analytics
         (RBAC)    (GoldParquetReader) (data/gold/)
```

**Endpoints** :
- `GET /api/v1/analytics/sentiment-distribution` → PySpark aggregation
- `GET /api/v1/analytics/topics-trends` → PySpark time series
- `POST /api/v1/analytics/custom-query` → PySpark SQL

---

### **3. RBAC Appliqué Partout**

```
Request → JWT Token → Role Check → Permission Check → Data Access
```

**Exemple** :
- `reader` → `GET /api/v1/raw/articles` → ✅ Autorisé
- `writer` → `PUT /api/v1/silver/articles/{id}` → ✅ Autorisé
- `writer` → `PUT /api/v1/raw/articles/{id}` → ❌ Interdit (RAW = read-only)

---

## 🏗️ Structure FastAPI Proposée

### **Organisation des Modules**

```
src/
  api/
    __init__.py
    main.py                    # FastAPI app principal
    dependencies.py            # Dépendances (auth, DB, Spark)
    config.py                  # Configuration centralisée
    
    auth/
      __init__.py
      security.py              # JWT, password hashing
      dependencies.py          # get_current_user, get_current_active_user
      models.py                # User, Token
    
    endpoints/
      __init__.py
      raw.py                   # RAW endpoints (read-only)
      silver.py                # SILVER endpoints (read/write)
      gold.py                  # GOLD endpoints (read-only)
      analytics.py             # PySpark endpoints (analytics)
      auth.py                  # Login, register
      users.py                 # User management (admin)
    
    services/
      __init__.py
      repository_service.py    # Service SQLite (Repository pattern)
      spark_service.py         # Service PySpark (SparkSession)
      permission_service.py   # RBAC logic
    
    schemas/
      __init__.py
      article.py               # Pydantic models (Article, ArticleCreate, etc.)
      user.py                  # Pydantic models (User, UserCreate, etc.)
      analytics.py             # Pydantic models (AnalyticsResponse, etc.)
```

---

## 🔐 RBAC : Permissions par Zone

### **Tableau des Permissions**

| Endpoint | Zone | Reader | Writer | Deleter | Admin | **Source** |
|----------|------|--------|--------|---------|-------|------------|
| `GET /api/v1/raw/articles` | RAW | ✅ | ✅ | ✅ | ✅ | **SQLite** |
| `PUT /api/v1/raw/articles/{id}` | RAW | ❌ | ❌ | ❌ | ⚠️* | **SQLite** |
| `GET /api/v1/silver/articles` | SILVER | ✅ | ✅ | ✅ | ✅ | **SQLite** |
| `PUT /api/v1/silver/articles/{id}` | SILVER | ❌ | ✅ | ✅ | ✅ | **SQLite** |
| `DELETE /api/v1/silver/articles/{id}` | SILVER | ❌ | ❌ | ✅ | ✅ | **SQLite** |
| `GET /api/v1/gold/articles` | GOLD | ✅ | ✅ | ✅ | ✅ | **SQLite** |
| `PUT /api/v1/gold/articles/{id}` | GOLD | ❌ | ❌ | ❌ | ⚠️* | **SQLite** |
| `GET /api/v1/analytics/sentiment` | Analytics | ✅ | ✅ | ✅ | ✅ | **PySpark** |
| `POST /api/v1/analytics/custom-query` | Analytics | ✅ | ✅ | ✅ | ✅ | **PySpark** |

*⚠️ Admin uniquement en cas d'erreur critique documentée

---

## 💻 Implémentation (Stratégie)

### **1. FastAPI App Principal**

```python
# src/api/main.py (STRATÉGIE)
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from src.api.endpoints import raw, silver, gold, analytics, auth, users
from src.api.dependencies import get_db, get_spark_session

app = FastAPI(
    title="DataSens API",
    description="API unifiée SQLite + PySpark avec RBAC",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(raw.router, prefix="/api/v1/raw", tags=["raw"])
app.include_router(silver.router, prefix="/api/v1/silver", tags=["silver"])
app.include_router(gold.router, prefix="/api/v1/gold", tags=["gold"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
```

---

### **2. Dépendances (DB + Spark)**

```python
# src/api/dependencies.py (STRATÉGIE)
from functools import lru_cache
from src.repository import Repository
from src.spark.session import get_spark_session

# SQLite dependency
@lru_cache()
def get_repository() -> Repository:
    """Singleton Repository (SQLite)"""
    return Repository("datasens.db")

# PySpark dependency
def get_spark():
    """SparkSession dependency"""
    return get_spark_session()
```

---

### **3. RBAC Permission Decorator**

```python
# src/api/services/permission_service.py (STRATÉGIE)
from enum import Enum
from fastapi import HTTPException, status
from src.api.auth.dependencies import get_current_user

class Zone(str, Enum):
    RAW = "raw"
    SILVER = "silver"
    GOLD = "gold"
    ANALYTICS = "analytics"

class Action(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"

def check_permission(zone: Zone, action: Action):
    """Decorator pour vérifier permissions RBAC"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user') or await get_current_user()
            
            # Règles RBAC par zone
            if zone == Zone.RAW:
                if action == Action.WRITE or action == Action.DELETE:
                    if current_user.role != "admin":
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="RAW zone: Read-only (admin exception only)"
                        )
            
            elif zone == Zone.SILVER:
                if action == Action.WRITE and current_user.role not in ["writer", "deleter", "admin"]:
                    raise HTTPException(status_code=403, detail="SILVER: Write requires writer role")
                if action == Action.DELETE and current_user.role not in ["deleter", "admin"]:
                    raise HTTPException(status_code=403, detail="SILVER: Delete requires deleter role")
            
            elif zone == Zone.GOLD:
                if action == Action.WRITE or action == Action.DELETE:
                    if current_user.role != "admin":
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="GOLD zone: Read-only (admin exception only)"
                        )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

### **4. Endpoint RAW (SQLite)**

```python
# src/api/endpoints/raw.py (STRATÉGIE)
from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import get_repository
from src.api.services.permission_service import check_permission, Zone, Action
from src.api.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/articles")
@check_permission(zone=Zone.RAW, action=Action.READ)
async def get_raw_articles(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    repo: Repository = Depends(get_repository)
):
    """GET /api/v1/raw/articles - Lecture RAW (SQLite)"""
    # Repository pattern : accès SQLite
    articles = repo.get_raw_articles(skip=skip, limit=limit)
    return articles

@router.put("/articles/{article_id}")
@check_permission(zone=Zone.RAW, action=Action.WRITE)
async def update_raw_article(
    article_id: int,
    article_update: ArticleUpdate,
    justification: str,  # Requis pour admin exception
    current_user = Depends(get_current_user),
    repo: Repository = Depends(get_repository)
):
    """PUT /api/v1/raw/articles/{id} - Modification RAW (Admin uniquement, erreur critique)"""
    if current_user.role != "admin":
        raise HTTPException(403, "RAW: Admin only for critical errors")
    
    # Log dans user_action_log
    repo.log_user_action(
        user_id=current_user.id,
        action="UPDATE_RAW",
        resource_type="raw_data",
        resource_id=article_id,
        details=f"Admin correction: {justification}"
    )
    
    # Update article
    updated = repo.update_raw_article(article_id, article_update)
    return updated
```

---

### **5. Endpoint SILVER (SQLite)**

```python
# src/api/endpoints/silver.py (STRATÉGIE)
from fastapi import APIRouter, Depends
from src.api.dependencies import get_repository
from src.api.services.permission_service import check_permission, Zone, Action

router = APIRouter()

@router.get("/articles")
@check_permission(zone=Zone.SILVER, action=Action.READ)
async def get_silver_articles(
    skip: int = 0,
    limit: int = 100,
    repo: Repository = Depends(get_repository)
):
    """GET /api/v1/silver/articles - Lecture SILVER (SQLite)"""
    articles = repo.get_silver_articles(skip=skip, limit=limit)
    return articles

@router.put("/articles/{article_id}")
@check_permission(zone=Zone.SILVER, action=Action.WRITE)
async def update_silver_article(
    article_id: int,
    article_update: ArticleUpdate,
    repo: Repository = Depends(get_repository)
):
    """PUT /api/v1/silver/articles/{id} - Modification SILVER (Writer/Admin)"""
    # Writer peut modifier SILVER
    updated = repo.update_silver_article(article_id, article_update)
    return updated

@router.delete("/articles/{article_id}")
@check_permission(zone=Zone.SILVER, action=Action.DELETE)
async def delete_silver_article(
    article_id: int,
    repo: Repository = Depends(get_repository)
):
    """DELETE /api/v1/silver/articles/{id} - Suppression SILVER (Deleter/Admin)"""
    deleted = repo.delete_silver_article(article_id)
    return deleted
```

---

### **6. Endpoint GOLD (SQLite)**

```python
# src/api/endpoints/gold.py (STRATÉGIE)
from fastapi import APIRouter, Depends
from src.api.dependencies import get_repository
from src.api.services.permission_service import check_permission, Zone, Action

router = APIRouter()

@router.get("/articles")
@check_permission(zone=Zone.GOLD, action=Action.READ)
async def get_gold_articles(
    skip: int = 0,
    limit: int = 100,
    repo: Repository = Depends(get_repository)
):
    """GET /api/v1/gold/articles - Lecture GOLD (SQLite)"""
    articles = repo.get_gold_articles(skip=skip, limit=limit)
    return articles
```

---

### **7. Endpoint Analytics (PySpark)**

```python
# src/api/endpoints/analytics.py (STRATÉGIE)
from fastapi import APIRouter, Depends
from src.api.dependencies import get_spark
from src.spark.adapters.gold_parquet_reader import GoldParquetReader
from src.spark.processors.gold_processor import GoldDataProcessor
from src.api.services.permission_service import check_permission, Zone, Action

router = APIRouter()

@router.get("/sentiment-distribution")
@check_permission(zone=Zone.ANALYTICS, action=Action.READ)
async def get_sentiment_distribution(
    spark = Depends(get_spark)
):
    """GET /api/v1/analytics/sentiment-distribution - Analytics PySpark"""
    # Lecture Parquet via PySpark
    reader = GoldParquetReader()
    df = reader.read_gold()  # Lit data/gold/date=*/articles.parquet
    
    # Traitement PySpark
    processor = GoldDataProcessor()
    result = processor.aggregate_by_sentiment(df)
    
    # Conversion en dict pour JSON response
    return result.toPandas().to_dict('records')

@router.post("/custom-query")
@check_permission(zone=Zone.ANALYTICS, action=Action.READ)
async def execute_custom_query(
    query: str,
    spark = Depends(get_spark)
):
    """POST /api/v1/analytics/custom-query - SQL sur Parquet via PySpark"""
    reader = GoldParquetReader()
    df = reader.read_gold()
    
    # Créer vue temporaire
    df.createOrReplaceTempView("gold_data")
    
    # Exécuter requête SQL
    result = spark.sql(query)
    
    return result.toPandas().to_dict('records')
```

---

## 🔄 Connexion SQLite ↔ PySpark

### **Principe : Parquet comme Buffer**

```
SQLite (E1) → GoldExporter → Parquet (data/gold/) → PySpark (E2)
     ↑              ↑              ↑                    ↑
  Source        Export E1      Buffer              Lecture seule
```

**Pas de connexion directe** : PySpark lit uniquement Parquet, jamais SQLite.

---

## ✅ Avantages de cette Architecture

### **1. Unification**
- ✅ **Une seule API** : FastAPI pour SQLite + PySpark
- ✅ **RBAC centralisé** : Permissions gérées au niveau API
- ✅ **Cohérence** : Même authentification pour tous les endpoints

### **2. Isolation**
- ✅ **SQLite isolé** : Accès via Repository pattern
- ✅ **PySpark isolé** : Accès via Adapter pattern
- ✅ **Pas de couplage** : E1 et E2 indépendants

### **3. Sécurité**
- ✅ **RBAC strict** : Permissions par zone (RAW/SILVER/GOLD)
- ✅ **Audit trail** : Toutes actions loggées
- ✅ **JWT** : Authentification sécurisée

### **4. Scalabilité**
- ✅ **SQLite** : Données structurées, CRUD rapide
- ✅ **PySpark** : Big Data, analytics complexes
- ✅ **Parquet** : Format optimisé pour les deux

---

## 📋 Checklist Implémentation

### **Phase 1 : FastAPI + SQLite**
- [ ] Setup FastAPI app
- [ ] Authentication (JWT)
- [ ] RBAC permissions
- [ ] RAW endpoints (SQLite)
- [ ] SILVER endpoints (SQLite)
- [ ] GOLD endpoints (SQLite)

### **Phase 2 : PySpark Integration**
- [ ] PySpark Adapter (GoldParquetReader)
- [ ] Analytics endpoints (PySpark)
- [ ] Custom query endpoint

### **Phase 3 : Tests & Documentation**
- [ ] Tests unitaires
- [ ] Tests d'intégration
- [ ] Documentation OpenAPI (Swagger)

---

## 🎯 Résumé

### **Architecture Unifiée**

```
FastAPI (Couche API Unique)
    ├── Authentication (JWT)
    ├── Authorization (RBAC)
    │
    ├── SQLite Endpoints (E1)
    │   ├── RAW (read-only)
    │   ├── SILVER (read/write)
    │   └── GOLD (read-only)
    │
    └── PySpark Endpoints (E2)
        └── Analytics (read-only)
```

### **RBAC Appliqué**

- ✅ **RAW** : Read-only (admin exception)
- ✅ **SILVER** : Read/Write/Delete selon rôle
- ✅ **GOLD** : Read-only (admin exception)
- ✅ **Analytics** : Read-only (tous)

### **Connexion E1 ↔ E2**

- ✅ **SQLite → Parquet** : Export E1 (GoldExporter)
- ✅ **Parquet → PySpark** : Lecture E2 (GoldParquetReader)
- ✅ **Pas de connexion directe** : Isolation complète

---

**Status** : 📋 **STRATÉGIE DÉFINIE - PRÊT POUR IMPLÉMENTATION**
