# 🔐 FastAPI + RBAC - Guide d'Implémentation

## 📋 Vue d'Ensemble

Intégration FastAPI avec RBAC utilisant les tables **PROFILS** et **USER_ACTION_LOG** déjà créées.

---

## 🎯 Permissions par Zone

### **Logique Métier**

#### **RAW : Preuve Légale & Source de Vérité** 🔒
- **Principe** : Données brutes collectées, **IMMUABLES**
- **Raison** : Preuve légale, traçabilité, audit
- **Règle** : **PERSONNE ne peut modifier** (sauf admin en cas d'erreur critique)
- **Accès** : Lecture seule pour tous

#### **SILVER : Zone de Travail** 🔧
- **Principe** : Données nettoyées et enrichies, **ZONE DE TRAVAIL**
- **Raison** : Transformation, correction, amélioration
- **Règle** : **Écriture autorisée** pour améliorer la qualité
- **Accès** : Lecture + Écriture pour writer

#### **GOLD : Zone de Diffusion** 📊
- **Principe** : Données finales validées, **PRÊTES POUR DIFFUSION**
- **Raison** : Export, visualisation, analyse
- **Règle** : **Lecture seule** (pas de modification)
- **Accès** : Lecture seule pour tous

### **Tableau Permissions**

| Zone | Reader | Writer | Deleter | Admin | **Justification** |
|------|--------|--------|---------|-------|-------------------|
| **RAW** | ✅ Read | ❌ | ❌ | ✅ Full | 🔒 **Preuve légale** - Source de vérité immuable |
| **SILVER** | ✅ Read | ✅ Write | ✅ Delete | ✅ Full | 🔧 **Zone de travail** - Transformation autorisée |
| **GOLD** | ✅ Read | ❌ | ❌ | ✅ Full | 📊 **Zone de diffusion** - Données validées, lecture seule |

---

## 📁 Structure Proposée

```
src/
  api/
    __init__.py
    main.py                    # FastAPI app
    dependencies.py            # Auth dependencies
    security.py                # JWT, password hashing
    permissions.py             # Décorateurs permissions
    routes/
      __init__.py
      auth.py                  # Login, register, refresh
      raw.py                   # Endpoints RAW (read-only)
      silver.py                # Endpoints SILVER (read/write)
      gold.py                  # Endpoints GOLD (read-only)
      admin.py                 # Endpoints admin
    models/
      __init__.py
      user.py                  # Pydantic models
      article.py               # Pydantic models
```

---

## 🔧 Implémentation Étape par Étape

### **1. Installation Dépendances**

```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] python-multipart
```

Ajouter à `requirements.txt` :
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

---

### **2. Configuration Sécurité**

```python
# src/api/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

# Configuration JWT
SECRET_KEY = "your-secret-key-change-in-production"  # À mettre en .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash un mot de passe"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Décode un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
```

---

### **3. Dépendances Authentification**

```python
# src/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.repository import Repository
from src.api.security import decode_token
from pathlib import Path
import os

security = HTTPBearer()

def get_db() -> Repository:
    """Retourne instance Repository"""
    db_path = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))
    return Repository(db_path)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Repository = Depends(get_db)
) -> dict:
    """Vérifie token JWT et retourne utilisateur"""
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Récupérer utilisateur depuis DB
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT profil_id, email, firstname, lastname, role, active
        FROM profils
        WHERE profil_id = ? AND active = 1
    """, (user_id,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return {
        'profil_id': user[0],
        'email': user[1],
        'firstname': user[2],
        'lastname': user[3],
        'role': user[4],
        'active': user[5]
    }
```

---

### **4. Permissions (Décorateurs)**

```python
# src/api/permissions.py
from functools import wraps
from fastapi import HTTPException, status, Request
from typing import Callable

def require_reader(func: Callable) -> Callable:
    """Décorateur : Lecture RAW/SILVER/GOLD (reader, writer, deleter, admin)"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        if current_user['role'] not in ['reader', 'writer', 'deleter', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Reader access required"
            )
        return await func(*args, **kwargs)
    return wrapper

def require_writer(func: Callable) -> Callable:
    """Décorateur : Écriture SILVER (writer, admin)"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if current_user['role'] not in ['writer', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Writer access required"
            )
        return await func(*args, **kwargs)
    return wrapper

def require_deleter(func: Callable) -> Callable:
    """Décorateur : Suppression SILVER (deleter, admin)"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if current_user['role'] not in ['deleter', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Deleter access required"
            )
        return await func(*args, **kwargs)
    return wrapper

def require_admin(func: Callable) -> Callable:
    """Décorateur : Accès complet (admin uniquement)"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if current_user['role'] != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return await func(*args, **kwargs)
    return wrapper
```

---

### **5. Endpoints RAW (Read-Only)**

```python
# src/api/routes/raw.py
from fastapi import APIRouter, Depends, Request, HTTPException
from src.api.dependencies import get_current_user, get_db
from src.api.permissions import require_reader
from src.repository import Repository
from typing import List, Optional

router = APIRouter(prefix="/api/v1/raw", tags=["RAW"])

@router.get("/articles")
@require_reader
async def list_articles(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db),
    request: Request = None
):
    """Liste articles RAW (lecture seule) - Reader, Admin
    
    RAW = Preuve légale, source de vérité immuable.
    Aucune modification autorisée (sauf admin en cas d'erreur critique).
    """
    # Log action
    db.log_user_action(
        profil_id=current_user['profil_id'],
        action_type='read',
        resource_type='raw_data',
        resource_id=None,
        ip_address=request.client.host if request else None
    )
    
    # Récupérer articles
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT r.raw_data_id, r.title, r.content, r.url, r.collected_at, s.name as source
        FROM raw_data r
        JOIN source s ON r.source_id = s.source_id
        ORDER BY r.collected_at DESC
        LIMIT ? OFFSET ?
    """, (limit, skip))
    
    articles = []
    for row in cursor.fetchall():
        articles.append({
            'id': row[0],
            'title': row[1],
            'content': row[2][:500] if row[2] else '',  # Limiter contenu
            'url': row[3],
            'collected_at': row[4],
            'source': row[5]
        })
    
    return {'total': len(articles), 'articles': articles}

@router.get("/articles/{article_id}")
@require_reader
async def get_article(
    article_id: int,
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db),
    request: Request = None
):
    """Détail article RAW (lecture seule) - Reader, Admin"""
    # Log action
    db.log_user_action(
        profil_id=current_user['profil_id'],
        action_type='read',
        resource_type='raw_data',
        resource_id=article_id,
        ip_address=request.client.host if request else None
    )
    
    # Récupérer article
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT r.raw_data_id, r.title, r.content, r.url, r.collected_at, s.name as source
        FROM raw_data r
        JOIN source s ON r.source_id = s.source_id
        WHERE r.raw_data_id = ?
    """, (article_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return {
        'id': row[0],
        'title': row[1],
        'content': row[2],
        'url': row[3],
        'collected_at': row[4],
        'source': row[5]
    }
```

---

### **6. Endpoints SILVER (Read/Write)**

```python
# src/api/routes/silver.py
from fastapi import APIRouter, Depends, Request, HTTPException, Body
from src.api.dependencies import get_current_user, get_db
from src.api.permissions import require_reader, require_writer, require_deleter
from src.repository import Repository
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/silver", tags=["SILVER"])

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

@router.get("/articles")
@require_reader
async def list_articles(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db),
    request: Request = None
):
    """Liste articles SILVER (lecture) - Reader, Writer, Deleter, Admin
    
    SILVER = Zone de travail, transformation et amélioration autorisées.
    """
    db.log_user_action(
        profil_id=current_user['profil_id'],
        action_type='read',
        resource_type='silver_data',
        resource_id=None,
        ip_address=request.client.host if request else None
    )
    
    # Récupérer articles SILVER (avec topics)
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT r.raw_data_id, r.title, r.content, r.url, r.collected_at, s.name as source
        FROM raw_data r
        JOIN source s ON r.source_id = s.source_id
        WHERE EXISTS (
            SELECT 1 FROM document_topic dt WHERE dt.raw_data_id = r.raw_data_id
        )
        ORDER BY r.collected_at DESC
        LIMIT ? OFFSET ?
    """, (limit, skip))
    
    articles = []
    for row in cursor.fetchall():
        articles.append({
            'id': row[0],
            'title': row[1],
            'content': row[2][:500] if row[2] else '',
            'url': row[3],
            'collected_at': row[4],
            'source': row[5]
        })
    
    return {'total': len(articles), 'articles': articles}

@router.post("/articles")
@require_writer
async def create_article(
    article: ArticleUpdate,
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db),
    request: Request = None
):
    """Créer article SILVER (écriture) - Writer, Admin
    
    SILVER = Zone de travail : création autorisée pour améliorer la qualité.
    """
    # Note: En réalité, les articles SILVER viennent du pipeline E1
    # Cet endpoint permet de créer manuellement si nécessaire
    
    db.log_user_action(
        profil_id=current_user['profil_id'],
        action_type='create',
        resource_type='silver_data',
        resource_id=None,
        ip_address=request.client.host if request else None,
        details=f"Title: {article.title}"
    )
    
    # Implémentation création article...
    return {'message': 'Article created', 'article_id': None}

@router.put("/articles/{article_id}")
@require_writer
async def update_article(
    article_id: int,
    article: ArticleUpdate,
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db),
    request: Request = None
):
    """Modifier article SILVER (écriture) - Writer, Admin"""
    db.log_user_action(
        profil_id=current_user['profil_id'],
        action_type='update',
        resource_type='silver_data',
        resource_id=article_id,
        ip_address=request.client.host if request else None,
        details=f"Updated fields: {article.dict(exclude_unset=True)}"
    )
    
    # Implémentation mise à jour...
    return {'message': 'Article updated', 'article_id': article_id}

@router.delete("/articles/{article_id}")
@require_deleter
async def delete_article(
    article_id: int,
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db),
    request: Request = None
):
    """Supprimer article SILVER - Deleter, Admin"""
    db.log_user_action(
        profil_id=current_user['profil_id'],
        action_type='delete',
        resource_type='silver_data',
        resource_id=article_id,
        ip_address=request.client.host if request else None
    )
    
    # Implémentation suppression...
    return {'message': 'Article deleted', 'article_id': article_id}
```

---

### **7. Endpoints GOLD (Read-Only)**

```python
# src/api/routes/gold.py
from fastapi import APIRouter, Depends, Request
from src.api.dependencies import get_current_user, get_db
from src.api.permissions import require_reader
from src.repository import Repository

router = APIRouter(prefix="/api/v1/gold", tags=["GOLD"])

@router.get("/articles")
@require_reader
async def list_articles(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db),
    request: Request = None
):
    """Liste articles GOLD (lecture seule) - Reader, Admin
    
    GOLD = Zone de diffusion, données validées prêtes pour export/analyse.
    Aucune modification autorisée (lecture seule).
    """
    db.log_user_action(
        profil_id=current_user['profil_id'],
        action_type='read',
        resource_type='gold_data',
        resource_id=None,
        ip_address=request.client.host if request else None
    )
    
    # Récupérer articles GOLD (avec topics + sentiment)
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT r.raw_data_id, r.title, r.content, r.url, r.collected_at, s.name as source,
               mo.label as sentiment
        FROM raw_data r
        JOIN source s ON r.source_id = s.source_id
        JOIN model_output mo ON r.raw_data_id = mo.raw_data_id
        WHERE mo.model_name = 'sentiment_keyword'
        ORDER BY r.collected_at DESC
        LIMIT ? OFFSET ?
    """, (limit, skip))
    
    articles = []
    for row in cursor.fetchall():
        articles.append({
            'id': row[0],
            'title': row[1],
            'content': row[2][:500] if row[2] else '',
            'url': row[3],
            'collected_at': row[4],
            'source': row[5],
            'sentiment': row[6]
        })
    
    return {'total': len(articles), 'articles': articles}

@router.get("/stats")
@require_reader
async def get_stats(
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db),
    request: Request = None
):
    """Statistiques GOLD - Reader, Admin"""
    db.log_user_action(
        profil_id=current_user['profil_id'],
        action_type='read',
        resource_type='gold_stats',
        resource_id=None,
        ip_address=request.client.host if request else None
    )
    
    cursor = db.conn.cursor()
    
    # Total articles
    cursor.execute("SELECT COUNT(*) FROM raw_data")
    total = cursor.fetchone()[0]
    
    # Distribution sentiment
    cursor.execute("""
        SELECT label, COUNT(*) as count
        FROM model_output
        WHERE model_name = 'sentiment_keyword'
        GROUP BY label
    """)
    sentiments = {row[0]: row[1] for row in cursor.fetchall()}
    
    return {
        'total_articles': total,
        'sentiment_distribution': sentiments
    }
```

---

### **8. Endpoints Authentification**

```python
# src/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.api.dependencies import get_db
from src.api.security import verify_password, get_password_hash, create_access_token
from src.repository import Repository
from datetime import timedelta
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    firstname: str
    lastname: str
    role: str = "reader"  # Par défaut reader

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=Token)
async def register(
    user_data: UserRegister,
    db: Repository = Depends(get_db)
):
    """Créer un nouveau compte"""
    cursor = db.conn.cursor()
    
    # Vérifier si email existe déjà
    cursor.execute("SELECT profil_id FROM profils WHERE email = ?", (user_data.email,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Vérifier rôle valide
    if user_data.role not in ['reader', 'writer', 'deleter', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )
    
    # Créer utilisateur
    password_hash = get_password_hash(user_data.password)
    cursor.execute("""
        INSERT INTO profils (email, password_hash, firstname, lastname, role, active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (user_data.email, password_hash, user_data.firstname, user_data.lastname, user_data.role))
    db.conn.commit()
    
    user_id = cursor.lastrowid
    
    # Créer token
    access_token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(minutes=30)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Repository = Depends(get_db)
):
    """Connexion utilisateur"""
    cursor = db.conn.cursor()
    
    # Récupérer utilisateur
    cursor.execute("""
        SELECT profil_id, password_hash, role, active
        FROM profils
        WHERE email = ?
    """, (form_data.username,))
    
    user = cursor.fetchone()
    if not user or not verify_password(form_data.password, user[1]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user[3]:  # active
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Mettre à jour last_login
    cursor.execute("""
        UPDATE profils SET last_login = CURRENT_TIMESTAMP
        WHERE profil_id = ?
    """, (user[0],))
    db.conn.commit()
    
    # Log action
    db.log_user_action(
        profil_id=user[0],
        action_type='login',
        resource_type='auth',
        resource_id=None
    )
    
    # Créer token
    access_token = create_access_token(
        data={"sub": str(user[0])},
        expires_delta=timedelta(minutes=30)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
```

---

### **9. Application FastAPI Principale**

```python
# src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import auth, raw, silver, gold

app = FastAPI(
    title="DataSens API",
    description="API REST pour DataSens E1 avec RBAC",
    version="1.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(raw.router)
app.include_router(silver.router)
app.include_router(gold.router)

@app.get("/")
async def root():
    return {"message": "DataSens API v1.1.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

---

### **10. Lancement**

```python
# run_api.py (à la racine)
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8001,  # Différent de 8000 (métriques)
        reload=True
    )
```

Ou avec Docker :
```dockerfile
# Ajouter dans Dockerfile
EXPOSE 8001
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## ✅ Checklist Implémentation

- [ ] Installer dépendances FastAPI
- [ ] Créer structure `src/api/`
- [ ] Implémenter `security.py` (JWT, password)
- [ ] Implémenter `dependencies.py` (auth)
- [ ] Implémenter `permissions.py` (décorateurs)
- [ ] Créer endpoints RAW (read-only)
- [ ] Créer endpoints SILVER (read/write)
- [ ] Créer endpoints GOLD (read-only)
- [ ] Créer endpoints auth (login/register)
- [ ] Intégrer audit trail (user_action_log)
- [ ] Tests API (pytest)
- [ ] Documentation Swagger

---

**Status** : 📋 **GUIDE COMPLET - PRÊT POUR IMPLÉMENTATION**
