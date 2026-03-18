# 🚀 ROADMAP ÉVOLUTION DataSens E1 → E2 → E3

## 📊 ÉTAT ACTUEL (E1)

✅ **Fonctionnel** :
- Pipeline ETL complet (RAW → SILVER → GOLD)
- SQLite database (42,466 articles, 71.93 MB)
- 21 sources actives
- Tables PROFILS + USER_ACTION_LOG (prêtes pour auth)
- Exports CSV/Parquet
- Enrichissement 100% (topics + sentiment)

---

## 🎯 OBJECTIF : Architecture Production avec RBAC

### **Logique Métier des Zones**

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

### **Permissions par Zone**

| Zone | Reader | Writer | Deleter | Admin | **Justification** |
|------|--------|--------|---------|-------|-------------------|
| **RAW** | ✅ Read | ❌ | ❌ | ✅ Full | 🔒 **Preuve légale** - Source de vérité immuable |
| **SILVER** | ✅ Read | ✅ Write | ✅ Delete | ✅ Full | 🔧 **Zone de travail** - Transformation autorisée |
| **GOLD** | ✅ Read | ❌ | ❌ | ✅ Full | 📊 **Zone de diffusion** - Données validées, lecture seule |

### **Rôles Utilisateurs**

- **reader** : Lecture RAW (preuve), SILVER (travail), GOLD (diffusion)
- **writer** : Lecture + Écriture SILVER uniquement (zone de travail)
- **deleter** : Suppression SILVER uniquement (nettoyage zone de travail)
- **admin** : Accès complet (gestion exceptionnelle RAW si erreur critique)

---

## 📅 ORDRE D'IMPLÉMENTATION RECOMMANDÉ

### **PHASE 1 : Docker & CI/CD (Fondation)** ⚡ PRIORITÉ 1

**Pourquoi en premier ?**
- ✅ Isolation environnement (dev/prod)
- ✅ Reproducibilité (même environnement partout)
- ✅ CI/CD automatise tests et déploiements
- ✅ Prérequis pour FastAPI (containerisation)

**Durée estimée** : 2-3 jours

#### **1.1 Docker**
- ✅ `Dockerfile` existe déjà
- ✅ `docker-compose.yml` existe déjà
- 🔧 **À faire** :
  - Vérifier/améliorer Dockerfile
  - Tester build et run
  - Volumes pour DB et exports
  - Health checks

#### **1.2 CI/CD**
- ✅ `.github/workflows/` existe déjà
- 🔧 **À faire** :
  - Workflow tests automatiques
  - Workflow build Docker
  - Workflow déploiement (optionnel)

**Résultat** : Projet containerisé, tests automatisés

---

### **PHASE 2 : FastAPI + RBAC (API REST)** ⚡ PRIORITÉ 2

**Pourquoi en deuxième ?**
- ✅ Expose les données via API REST
- ✅ RBAC utilise tables PROFILS déjà créées
- ✅ Permet authentification avant PySpark
- ✅ Tests possibles avec Docker

**Durée estimée** : 3-5 jours

#### **2.1 FastAPI Setup**
```python
# Structure proposée
src/
  api/
    main.py              # FastAPI app
    dependencies.py      # Auth dependencies
    routes/
      raw.py            # Endpoints RAW (read-only)
      silver.py         # Endpoints SILVER (read/write)
      gold.py           # Endpoints GOLD (read-only)
      auth.py           # Login, register, refresh
```

#### **2.2 RBAC Implementation**
- ✅ Utiliser table `profils` (déjà créée)
- ✅ JWT tokens pour authentification
- ✅ Décorateurs/permissions par zone :
  - `@require_reader` : Lecture RAW/SILVER/GOLD
  - `@require_writer` : Écriture SILVER
  - `@require_admin` : Accès complet

#### **2.3 Endpoints par Zone**

**RAW** (`/api/v1/raw/`)
- `GET /articles` : Liste articles (reader, admin)
- `GET /articles/{id}` : Détail article (reader, admin)
- ❌ Pas de POST/PUT/DELETE (sauf admin)

**SILVER** (`/api/v1/silver/`)
- `GET /articles` : Liste articles (reader, writer, admin)
- `GET /articles/{id}` : Détail article (reader, writer, admin)
- `POST /articles` : Créer article (writer, admin)
- `PUT /articles/{id}` : Modifier article (writer, admin)
- `DELETE /articles/{id}` : Supprimer article (deleter, admin)

**GOLD** (`/api/v1/gold/`)
- `GET /articles` : Liste articles (reader, admin)
- `GET /articles/{id}` : Détail article (reader, admin)
- `GET /stats` : Statistiques (reader, admin)
- ❌ Pas de POST/PUT/DELETE (sauf admin)

#### **2.4 Audit Trail**
- ✅ Utiliser table `user_action_log` (déjà créée)
- ✅ Logger toutes les actions API :
  - `action_type` : 'read', 'create', 'update', 'delete'
  - `resource_type` : 'raw_data', 'silver_data', 'gold_data'
  - `resource_id` : ID de la ressource
  - `profil_id` : Utilisateur authentifié

**Résultat** : API REST sécurisée avec RBAC complet

---

### **PHASE 3 : PySpark (Big Data)** ⚡ PRIORITÉ 3

**Pourquoi en troisième ?**
- ✅ Nécessite FastAPI pour exposer données
- ✅ Traite les exports Parquet déjà générés
- ✅ Scale à 100k+ articles
- ✅ Intègre avec FastAPI (lecture Parquet)

**Durée estimée** : 4-6 jours

#### **3.1 PySpark Setup**
```python
# Structure proposée
src/
  spark/
    session.py          # SparkSession config
    processors/
      raw_processor.py    # Traitement RAW
      silver_processor.py # Traitement SILVER
      gold_processor.py   # Traitement GOLD
    queries.py          # Requêtes Spark SQL
```

#### **3.2 Intégration avec FastAPI**
- FastAPI lit depuis Parquet (via PySpark)
- PySpark traite les données en batch
- FastAPI expose résultats via API

#### **3.3 Workflow**
```
1. Pipeline E1 → Génère Parquet (déjà fait)
2. PySpark → Traite Parquet (batch processing)
3. PySpark → Écrit résultats Parquet
4. FastAPI → Lit Parquet et expose via API
```

**Résultat** : Traitement Big Data avec PySpark, exposé via FastAPI

---

### **PHASE 4 : Fine-tuning Modèles IA (FlauBERT & CamemBERT)** ⚡ PRIORITÉ 4

**Pourquoi en quatrième ?**
- ✅ Nécessite données GOLD enrichies (topics + sentiment)
- ✅ Utilise PySpark pour préparer datasets d'entraînement
- ✅ Améliore précision sentiment/topics
- ✅ Prépare données pour IA générative

**Durée estimée** : 5-7 jours

#### **4.1 Fine-tuning FlauBERT**
- ✅ Modèle : `flaubert/flaubert_base_uncased`
- ✅ Objectif : Classification sentiment (positif/neutre/négatif)
- ✅ Dataset : Articles GOLD avec sentiment ground truth
- ✅ Métriques : Accuracy, F1-score, Precision, Recall

#### **4.2 Fine-tuning CamemBERT**
- ✅ Modèle : `camembert-base`
- ✅ Objectif : Classification topics (27 topics)
- ✅ Dataset : Articles GOLD avec topics ground truth
- ✅ Métriques : Accuracy, F1-score par topic

#### **4.3 Pipeline Fine-tuning**
```python
# Structure proposée
src/
  ml/
    models/
      flaubert_sentiment.py    # Fine-tuning FlauBERT
      camembert_topics.py       # Fine-tuning CamemBERT
    training/
      prepare_dataset.py        # Préparation données
      train.py                  # Script entraînement
      evaluate.py               # Évaluation modèles
    inference/
      predict_sentiment.py      # Prédiction sentiment
      predict_topics.py         # Prédiction topics
```

#### **4.4 Intégration Pipeline**
- Pipeline E1 → Génère données GOLD
- Fine-tuning → Entraîne modèles sur GOLD
- Modèles → Améliorent enrichissement pipeline
- Boucle d'amélioration continue

**Résultat** : Modèles IA fine-tunés pour sentiment et topics

---

### **PHASE 5 : Dashboard Streamlit** ⚡ PRIORITÉ 5

**Pourquoi en cinquième ?**
- ✅ Visualise données enrichies (GOLD)
- ✅ Utilise modèles IA fine-tunés pour prédictions
- ✅ Interface utilisateur interactive
- ✅ Complète FastAPI (API) avec UI

**Durée estimée** : 3-4 jours

#### **5.1 Dashboard Principal**
- ✅ Vue d'ensemble : Statistiques globales
- ✅ Graphiques sentiment (distribution, évolution)
- ✅ Graphiques topics (distribution, corrélations)
- ✅ Filtres par source, date, sentiment, topic
- ✅ Recherche articles

#### **5.2 Visualisations**
- ✅ Graphiques interactifs (Plotly)
- ✅ Cartes de chaleur (heatmaps)
- ✅ Graphiques temporels (évolution)
- ✅ Nuages de mots (word clouds)
- ✅ Graphiques de corrélation

#### **5.3 Prédictions IA**
- ✅ Prédiction sentiment (FlauBERT)
- ✅ Prédiction topics (CamemBERT)
- ✅ Comparaison prédictions vs annotations
- ✅ Métriques de performance

#### **5.4 Structure**
```python
# Structure proposée
streamlit_app/
  main.py                    # Application principale
  pages/
    dashboard.py             # Dashboard principal
    sentiment.py             # Analyse sentiment
    topics.py                # Analyse topics
    predictions.py           # Prédictions IA
    insights.py              # Insights Mistral
  components/
    charts.py                # Composants graphiques
    filters.py               # Composants filtres
```

**Résultat** : Dashboard Streamlit interactif avec visualisations et prédictions

---

### **PHASE 6 : IA Générative Mistral (Insights)** ⚡ PRIORITÉ 6

**Pourquoi en dernier ?**
- ✅ Nécessite toutes les données enrichies (GOLD)
- ✅ Utilise modèles fine-tunés pour contexte
- ✅ Génère insights sur climat social/finance
- ✅ Résume dataset complet

**Durée estimée** : 4-5 jours

#### **6.1 Intégration API Mistral**
- ✅ API Mistral : `mistralai/mistral-7b-instruct` ou `mistral-large`
- ✅ Clé API : Variable d'environnement `MISTRAL_API_KEY`
- ✅ Rate limiting : Gestion quotas API
- ✅ Retry logic : Gestion erreurs API

#### **6.2 Prompts Spécialisés**

**Résumé Dataset**
```
Tu es un expert en analyse de données. Résume le dataset DataSens :
- Total articles : {total}
- Distribution sentiment : {sentiment_dist}
- Topics principaux : {topics}
- Période : {date_range}
- Sources : {sources}

Génère un résumé structuré (max 500 mots).
```

**Insights Climat Social**
```
Analyse le climat social français basé sur {nb_articles} articles :
- Sentiment général : {sentiment}
- Topics sociaux : {social_topics}
- Évolution temporelle : {timeline}

Génère 5 insights clés sur le climat social (max 300 mots chacun).
```

**Insights Climat Financier**
```
Analyse le climat financier français basé sur {nb_articles} articles :
- Sentiment économique : {sentiment}
- Topics finance : {finance_topics}
- Indicateurs : {indicators}

Génère 5 insights clés sur le climat financier (max 300 mots chacun).
```

#### **6.3 Structure**
```python
# Structure proposée
src/
  ai/
    mistral/
      client.py              # Client API Mistral
      prompts.py             # Templates prompts
      insights/
        summary.py           # Résumé dataset
        social_climate.py    # Insights climat social
        financial_climate.py # Insights climat financier
      cache.py               # Cache réponses (évite coûts)
```

#### **6.4 Intégration Dashboard**
- Streamlit → Affiche insights Mistral
- FastAPI → Endpoint `/api/v1/insights/mistral`
- Cache → Évite appels API répétés
- Schedule → Génération automatique quotidienne

#### **6.5 Workflow**
```
1. Pipeline E1 → Génère GOLD
2. Modèles IA → Enrichissent données
3. Mistral → Analyse GOLD et génère insights
4. Streamlit → Affiche insights
5. FastAPI → Expose insights via API
```

**Résultat** : Insights générés par IA sur climat social et financier

---

## 🔐 ARCHITECTURE RBAC DÉTAILLÉE

### **1. Authentification (JWT)**

```python
# src/api/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from src.repository import Repository

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Repository = Depends(get_db)
) -> dict:
    """Vérifie token JWT et retourne utilisateur"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        user = db.get_user_by_id(user_id)
        if not user or not user['active']:
            raise HTTPException(status_code=401, detail="User inactive")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### **2. Permissions par Zone**

```python
# src/api/permissions.py
from functools import wraps
from fastapi import HTTPException, status

def require_reader(func):
    """Décorateur : Lecture RAW/SILVER/GOLD"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = kwargs.get('current_user')
        if user['role'] not in ['reader', 'writer', 'deleter', 'admin']:
            raise HTTPException(status_code=403, detail="Reader access required")
        return await func(*args, **kwargs)
    return wrapper

def require_writer(func):
    """Décorateur : Écriture SILVER"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = kwargs.get('current_user')
        if user['role'] not in ['writer', 'admin']:
            raise HTTPException(status_code=403, detail="Writer access required")
        return await func(*args, **kwargs)
    return wrapper

def require_admin(func):
    """Décorateur : Accès complet"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = kwargs.get('current_user')
        if user['role'] != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        return await func(*args, **kwargs)
    return wrapper
```

### **3. Endpoints avec Permissions**

```python
# src/api/routes/raw.py
from fastapi import APIRouter, Depends
from src.api.dependencies import get_current_user, require_reader

router = APIRouter(prefix="/api/v1/raw", tags=["RAW"])

@router.get("/articles")
@require_reader
async def list_articles(
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db)
):
    """Liste articles RAW (lecture seule)"""
    # Log action
    db.log_user_action(
        profil_id=current_user['profil_id'],
        action_type='read',
        resource_type='raw_data',
        resource_id=None,
        ip_address=request.client.host
    )
    return db.get_all_raw_articles()

@router.get("/articles/{article_id}")
@require_reader
async def get_article(
    article_id: int,
    current_user: dict = Depends(get_current_user),
    db: Repository = Depends(get_db)
):
    """Détail article RAW (lecture seule)"""
    db.log_user_action(
        profil_id=current_user['profil_id'],
        action_type='read',
        resource_type='raw_data',
        resource_id=article_id,
        ip_address=request.client.host
    )
    return db.get_raw_article_by_id(article_id)
```

---

## 📋 CHECKLIST IMPLÉMENTATION

### **Phase 1 : Docker & CI/CD**
- [ ] Vérifier/améliorer Dockerfile
- [ ] Tester docker-compose.yml
- [ ] Configurer volumes (DB, exports)
- [ ] Ajouter health checks
- [ ] Créer workflow GitHub Actions (tests)
- [ ] Créer workflow GitHub Actions (build)
- [ ] Tester build et run en local

### **Phase 2 : FastAPI + RBAC**
- [ ] Installer FastAPI + dépendances
- [ ] Créer structure `src/api/`
- [ ] Implémenter authentification JWT
- [ ] Créer endpoints RAW (read-only)
- [ ] Créer endpoints SILVER (read/write)
- [ ] Créer endpoints GOLD (read-only)
- [ ] Implémenter permissions (décorateurs)
- [ ] Intégrer audit trail (user_action_log)
- [ ] Tests API (pytest)
- [ ] Documentation Swagger/OpenAPI

### **Phase 3 : PySpark**
- [ ] Installer PySpark
- [ ] Créer structure `src/spark/`
- [ ] Configurer SparkSession
- [ ] Lire Parquet depuis `data/gold/`
- [ ] Traitements batch (agrégations, analyses)
- [ ] Intégrer avec FastAPI (lecture résultats)
- [ ] Tests PySpark

### **Phase 4 : Fine-tuning FlauBERT & CamemBERT**
- [ ] Installer transformers, torch
- [ ] Créer structure `src/ml/`
- [ ] Préparer datasets d'entraînement (GOLD)
- [ ] Fine-tuning FlauBERT (sentiment)
- [ ] Fine-tuning CamemBERT (topics)
- [ ] Évaluation modèles (métriques)
- [ ] Intégration pipeline (prédictions)
- [ ] Tests modèles

### **Phase 5 : Dashboard Streamlit**
- [ ] Installer Streamlit
- [ ] Créer structure `streamlit_app/`
- [ ] Dashboard principal (statistiques)
- [ ] Visualisations interactives (Plotly)
- [ ] Filtres et recherche
- [ ] Intégration prédictions IA
- [ ] Tests interface

### **Phase 6 : IA Générative Mistral**
- [ ] Obtenir clé API Mistral
- [ ] Créer structure `src/ai/mistral/`
- [ ] Client API Mistral
- [ ] Templates prompts (résumé, insights)
- [ ] Génération insights climat social
- [ ] Génération insights climat financier
- [ ] Cache réponses
- [ ] Intégration Streamlit + FastAPI
- [ ] Schedule génération automatique

---

## 🎯 RECOMMANDATION FINALE

### **Ordre Optimal** :

1. **Docker & CI/CD** (2-3 jours)
   - Fondation solide
   - Tests automatisés
   - Environnement reproductible

2. **FastAPI + RBAC** (3-5 jours)
   - API REST sécurisée
   - Utilise tables PROFILS existantes
   - Audit trail complet

3. **PySpark** (4-6 jours)
   - Traitement Big Data
   - Intègre avec FastAPI
   - Scale à 100k+ articles

### **Total estimé** : 21-30 jours (6 phases)

**Détail par phase** :
- Phase 1 (Docker & CI/CD) : 2-3 jours
- Phase 2 (FastAPI + RBAC) : 3-5 jours
- Phase 3 (PySpark) : 4-6 jours
- Phase 4 (FlauBERT & CamemBERT) : 5-7 jours
- Phase 5 (Streamlit) : 3-4 jours
- Phase 6 (Mistral IA) : 4-5 jours

---

## 📚 RESSOURCES

### **Docker**
- Dockerfile existant : `Dockerfile`
- docker-compose.yml existant : `docker-compose.yml`

### **CI/CD**
- Workflows existants : `.github/workflows/`

### **Tables Auth**
- PROFILS : `src/repository.py` (méthode `_ensure_profils_table()`)
- USER_ACTION_LOG : `src/repository.py` (méthode `log_user_action()`)

### **Documentation**
- Tables auth : `docs/TABLES_PROFILS_ACTION_LOG.md`
- Flow données : `FLOW_DONNEES.md`

---

**Status** : 📋 **PLANIFICATION COMPLÈTE - PRÊT POUR IMPLÉMENTATION**
