# 🏗️ PLAN D'ACTION DÉTAILLÉ - Construction autour de E1

**Date**: 2025-12-18  
**Objectif**: Construire E2/E3 autour de E1 sans casser le pipeline existant  
**Stratégie**: Isolation complète de E1 + Interfaces claires

---

## 🔒 STRATÉGIE D'ISOLATION DE E1

### **Principe Fondamental**
> **E1 est la FONDATION IMMUABLE** - Aucune modification ne doit affecter son fonctionnement

### **3 Niveaux de Protection**

#### **1. Isolation Structurelle** 🏛️
```
PROJET_DATASENS/
├── src/
│   ├── e1/                    ← NOUVEAU: Package E1 isolé
│   │   ├── __init__.py
│   │   ├── core.py           ← Déplacé depuis src/core.py
│   │   ├── repository.py     ← Déplacé depuis src/repository.py
│   │   ├── tagger.py         ← Déplacé depuis src/tagger.py
│   │   ├── analyzer.py       ← Déplacé depuis src/analyzer.py
│   │   ├── aggregator.py     ← Déplacé depuis src/aggregator.py
│   │   ├── exporter.py       ← Déplacé depuis src/exporter.py
│   │   └── pipeline.py       ← Nouveau: E1Pipeline isolé
│   │
│   ├── e2/                    ← NOUVEAU: Package E2 (FastAPI + RBAC)
│   │   ├── __init__.py
│   │   ├── api/
│   │   ├── auth/
│   │   └── services/
│   │
│   ├── e3/                    ← NOUVEAU: Package E3 (PySpark + ML)
│   │   ├── __init__.py
│   │   ├── spark/
│   │   └── ml/
│   │
│   └── shared/                ← NOUVEAU: Code partagé (interfaces)
│       ├── __init__.py
│       ├── interfaces.py     ← Contrats entre E1/E2/E3
│       └── models.py         ← Modèles de données partagés
```

#### **2. Isolation par Interface** 🔌
**Principe**: E2/E3 ne touchent JAMAIS directement à E1, uniquement via interfaces

```python
# src/shared/interfaces.py
"""Interfaces entre E1 et E2/E3"""

class E1DataReader:
    """Interface de lecture E1 - E2/E3 utilisent uniquement cette interface"""
    
    def read_raw_data(self, date: str) -> pd.DataFrame:
        """Lit RAW depuis data/raw/ - E1 écrit, E2/E3 lisent"""
        pass
    
    def read_silver_data(self, date: str) -> pd.DataFrame:
        """Lit SILVER depuis data/silver/ - E1 écrit, E2/E3 lisent"""
        pass
    
    def read_gold_data(self, date: str) -> pd.DataFrame:
        """Lit GOLD depuis data/gold/ - E1 écrit, E2/E3 lisent"""
        pass
    
    def get_database_stats(self) -> dict:
        """Stats depuis datasens.db - Lecture seule"""
        pass
```

#### **3. Isolation par Tests** ✅
**Principe**: Tests de non-régression E1 avant chaque déploiement E2/E3

```python
# tests/test_e1_isolation.py
"""Tests garantissant qu'E1 fonctionne toujours"""

def test_e1_pipeline_complete():
    """Test complet E1 - DOIT passer à 100% avant chaque merge"""
    pipeline = E1Pipeline()
    pipeline.run()
    assert pipeline.stats['loaded'] > 0
    assert Path('data/gold/date=2025-12-18/articles.parquet').exists()

def test_e1_exports_exist():
    """Vérifie que les exports E1 existent"""
    assert Path('exports/raw.csv').exists()
    assert Path('exports/silver.csv').exists()
    assert Path('exports/gold.csv').exists()
```

---

## 📋 PLAN D'ACTION MICRO-CHANGEMENT PAR MICRO-CHANGEMENT

### **PHASE 0 : PRÉPARATION & ISOLATION E1** ⚡ PRIORITÉ 0

**Objectif**: Isoler E1 avant toute construction E2/E3  
**Durée**: 1-2 jours  
**Risque**: ⚠️ Moyen (refactoring structure)

#### **Étape 0.1 : Créer structure packages isolés**
- [ ] **Micro-étape 0.1.1**: Créer `src/e1/__init__.py`
- [ ] **Micro-étape 0.1.2**: Créer `src/e2/__init__.py`
- [ ] **Micro-étape 0.1.3**: Créer `src/e3/__init__.py`
- [ ] **Micro-étape 0.1.4**: Créer `src/shared/__init__.py`
- [ ] **Micro-étape 0.1.5**: Vérifier que tous les `__init__.py` sont créés

#### **Étape 0.2 : Déplacer code E1 vers package isolé**
- [ ] **Micro-étape 0.2.1**: Copier `src/core.py` → `src/e1/core.py`
- [ ] **Micro-étape 0.2.2**: Copier `src/repository.py` → `src/e1/repository.py`
- [ ] **Micro-étape 0.2.3**: Copier `src/tagger.py` → `src/e1/tagger.py`
- [ ] **Micro-étape 0.2.4**: Copier `src/analyzer.py` → `src/e1/analyzer.py`
- [ ] **Micro-étape 0.2.5**: Copier `src/aggregator.py` → `src/e1/aggregator.py`
- [ ] **Micro-étape 0.2.6**: Copier `src/exporter.py` → `src/e1/exporter.py`
- [ ] **Micro-étape 0.2.7**: Créer `src/e1/pipeline.py` avec classe `E1Pipeline` (déplacée depuis `main.py`)
- [ ] **Micro-étape 0.2.8**: Mettre à jour imports dans `src/e1/` (chemins relatifs)
- [ ] **Micro-étape 0.2.9**: Tester que `python -m src.e1.pipeline` fonctionne
- [ ] **Micro-étape 0.2.10**: Vérifier que tous les tests E1 passent

#### **Étape 0.3 : Créer interface de lecture E1**
- [ ] **Micro-étape 0.3.1**: Créer `src/shared/interfaces.py`
- [ ] **Micro-étape 0.3.2**: Implémenter classe `E1DataReader` avec méthode `read_raw_data()`
- [ ] **Micro-étape 0.3.3**: Implémenter méthode `read_silver_data()`
- [ ] **Micro-étape 0.3.4**: Implémenter méthode `read_gold_data()`
- [ ] **Micro-étape 0.3.5**: Implémenter méthode `get_database_stats()`
- [ ] **Micro-étape 0.3.6**: Tester `E1DataReader` avec données réelles
- [ ] **Micro-étape 0.3.7**: Documenter interface dans docstring

#### **Étape 0.4 : Adapter main.py pour utiliser E1 isolé**
- [ ] **Micro-étape 0.4.1**: Modifier `main.py` pour importer depuis `src.e1.pipeline`
- [ ] **Micro-étape 0.4.2**: Tester `python main.py` fonctionne
- [ ] **Micro-étape 0.4.3**: Vérifier que tous les exports sont générés
- [ ] **Micro-étape 0.4.4**: Vérifier que la DB est mise à jour correctement

#### **Étape 0.5 : Tests de non-régression E1**
- [ ] **Micro-étape 0.5.1**: Créer `tests/test_e1_isolation.py`
- [ ] **Micro-étape 0.5.2**: Écrire test `test_e1_pipeline_complete()`
- [ ] **Micro-étape 0.5.3**: Écrire test `test_e1_exports_exist()`
- [ ] **Micro-étape 0.5.4**: Écrire test `test_e1_database_schema()`
- [ ] **Micro-étape 0.5.5**: Lancer tous les tests E1 (doivent passer à 100%)
- [ ] **Micro-étape 0.5.6**: Ajouter tests dans CI/CD (GitHub Actions)

#### **Étape 0.6 : Documentation isolation**
- [ ] **Micro-étape 0.6.1**: Créer `docs/E1_ISOLATION.md` expliquant l'isolation
- [ ] **Micro-étape 0.6.2**: Documenter interfaces dans `docs/INTERFACES.md`
- [ ] **Micro-étape 0.6.3**: Mettre à jour `README.md` avec nouvelle structure

**✅ Validation Phase 0**: 
- [ ] Tous les tests E1 passent
- [ ] `python main.py` fonctionne
- [ ] Exports RAW/SILVER/GOLD générés
- [ ] Documentation à jour

---

### **PHASE 1 : DOCKER & CI/CD** ⚡ PRIORITÉ 1

**Objectif**: Containeriser E1 et automatiser tests  
**Durée**: 2-3 jours  
**Risque**: ⚠️ Faible (E1 isolé, pas de modification)

#### **Étape 1.1 : Vérifier Dockerfile existant**
- [ ] **Micro-étape 1.1.1**: Lire `Dockerfile` existant
- [ ] **Micro-étape 1.1.2**: Vérifier que Python 3.10+ est utilisé
- [ ] **Micro-étape 1.1.3**: Vérifier que `requirements.txt` est copié
- [ ] **Micro-étape 1.1.4**: Vérifier que `main.py` est le point d'entrée
- [ ] **Micro-étape 1.1.5**: Tester build: `docker build -t datasens-e1 .`
- [ ] **Micro-étape 1.1.6**: Vérifier que le build réussit

#### **Étape 1.2 : Améliorer Dockerfile pour E1**
- [ ] **Micro-étape 1.2.1**: Ajouter health check dans Dockerfile
- [ ] **Micro-étape 1.2.2**: Configurer volumes pour `data/` et `exports/`
- [ ] **Micro-étape 1.2.3**: Configurer volume pour `datasens.db`
- [ ] **Micro-étape 1.2.4**: Ajouter variables d'environnement (DB_PATH, etc.)
- [ ] **Micro-étape 1.2.5**: Tester build avec améliorations

#### **Étape 1.3 : Vérifier docker-compose.yml**
- [ ] **Micro-étape 1.3.1**: Lire `docker-compose.yml` existant
- [ ] **Micro-étape 1.3.2**: Vérifier service E1
- [ ] **Micro-étape 1.3.3**: Vérifier volumes montés
- [ ] **Micro-étape 1.3.4**: Tester `docker-compose up -d`
- [ ] **Micro-étape 1.3.5**: Vérifier que E1 s'exécute dans container
- [ ] **Micro-étape 1.3.6**: Vérifier que les exports sont générés dans volumes

#### **Étape 1.4 : CI/CD - Tests automatiques**
- [ ] **Micro-étape 1.4.1**: Lire `.github/workflows/test.yml`
- [ ] **Micro-étape 1.4.2**: Ajouter étape test E1 isolation
- [ ] **Micro-étape 1.4.3**: Ajouter étape test exports E1
- [ ] **Micro-étape 1.4.4**: Tester workflow localement avec `act` (optionnel)
- [ ] **Micro-étape 1.4.5**: Push et vérifier que CI passe

#### **Étape 1.5 : CI/CD - Build Docker**
- [ ] **Micro-étape 1.5.1**: Lire `.github/workflows/build.yml`
- [ ] **Micro-étape 1.5.2**: Vérifier que Docker build est configuré
- [ ] **Micro-étape 1.5.3**: Ajouter étape push vers registry (optionnel)
- [ ] **Micro-étape 1.5.4**: Tester build dans CI

**✅ Validation Phase 1**: 
- [ ] Docker build réussit
- [ ] `docker-compose up` fonctionne
- [ ] CI/CD passe tous les tests
- [ ] E1 s'exécute dans container

---

### **PHASE 2 : FASTAPI + RBAC** ⚡ PRIORITÉ 2

**Objectif**: Exposer données E1 via API REST avec RBAC  
**Durée**: 3-5 jours  
**Risque**: ⚠️ Faible (E1 isolé, E2 lit uniquement)

#### **Étape 2.1 : Setup FastAPI**
- [ ] **Micro-étape 2.1.1**: Ajouter `fastapi==0.104.1` dans `requirements.txt`
- [ ] **Micro-étape 2.1.2**: Ajouter `uvicorn[standard]==0.24.0` dans `requirements.txt`
- [ ] **Micro-étape 2.1.3**: Ajouter `python-jose[cryptography]==3.3.0` pour JWT
- [ ] **Micro-étape 2.1.4**: Ajouter `python-multipart==0.0.6` pour forms
- [ ] **Micro-étape 2.1.5**: Installer dépendances: `pip install -r requirements.txt`
- [ ] **Micro-étape 2.1.6**: Créer `src/e2/api/__init__.py`
- [ ] **Micro-étape 2.1.7**: Créer `src/e2/api/main.py` avec FastAPI app basique
- [ ] **Micro-étape 2.1.8**: Tester `uvicorn src.e2.api.main:app --reload`
- [ ] **Micro-étape 2.1.9**: Vérifier que Swagger UI s'affiche sur `http://localhost:8000/docs`

#### **Étape 2.2 : Intégrer E1DataReader dans FastAPI**
- [ ] **Micro-étape 2.2.1**: Importer `E1DataReader` depuis `src.shared.interfaces`
- [ ] **Micro-étape 2.2.2**: Créer instance `E1DataReader` dans `main.py`
- [ ] **Micro-étape 2.2.3**: Créer endpoint test `GET /api/v1/health`
- [ ] **Micro-étape 2.2.4**: Créer endpoint `GET /api/v1/stats` utilisant `E1DataReader.get_database_stats()`
- [ ] **Micro-étape 2.2.5**: Tester endpoint `/api/v1/stats` retourne stats E1
- [ ] **Micro-étape 2.2.6**: Vérifier que E1 n'est pas modifié (isolation respectée)

#### **Étape 2.3 : Authentification JWT**
- [ ] **Micro-étape 2.3.1**: Créer `src/e2/auth/__init__.py`
- [ ] **Micro-étape 2.3.2**: Créer `src/e2/auth/security.py` avec fonctions JWT
- [ ] **Micro-étape 2.3.3**: Implémenter `create_access_token()`
- [ ] **Micro-étape 2.3.4**: Implémenter `verify_token()`
- [ ] **Micro-étape 2.3.5**: Créer `src/e2/auth/dependencies.py` avec `get_current_user()`
- [ ] **Micro-étape 2.3.6**: Tester création token JWT
- [ ] **Micro-étape 2.3.7**: Tester vérification token JWT

#### **Étape 2.4 : Utiliser table PROFILS existante**
- [ ] **Micro-étape 2.4.1**: Vérifier que table `profils` existe dans DB (via E1)
- [ ] **Micro-étape 2.4.2**: Créer `src/e2/auth/repository.py` pour lire `profils`
- [ ] **Micro-étape 2.4.3**: Implémenter `get_user_by_email()` lisant depuis `profils`
- [ ] **Micro-étape 2.4.4**: Implémenter `authenticate_user()` vérifiant mot de passe
- [ ] **Micro-étape 2.4.5**: Tester authentification avec utilisateur existant
- [ ] **Micro-étape 2.4.6**: Vérifier que E1 n'est pas modifié (lecture seule DB)

#### **Étape 2.5 : Endpoint login**
- [ ] **Micro-étape 2.5.1**: Créer `src/e2/api/routes/__init__.py`
- [ ] **Micro-étape 2.5.2**: Créer `src/e2/api/routes/auth.py`
- [ ] **Micro-étape 2.5.3**: Implémenter `POST /api/v1/auth/login`
- [ ] **Micro-étape 2.5.4**: Tester login avec credentials valides
- [ ] **Micro-étape 2.5.5**: Tester login avec credentials invalides
- [ ] **Micro-étape 2.5.6**: Vérifier que token JWT est retourné

#### **Étape 2.6 : Permissions par zone (décorateurs)**
- [ ] **Micro-étape 2.6.1**: Créer `src/e2/api/permissions.py`
- [ ] **Micro-étape 2.6.2**: Implémenter décorateur `@require_reader`
- [ ] **Micro-étape 2.6.3**: Implémenter décorateur `@require_writer`
- [ ] **Micro-étape 2.6.4**: Implémenter décorateur `@require_deleter`
- [ ] **Micro-étape 2.6.5**: Implémenter décorateur `@require_admin`
- [ ] **Micro-étape 2.6.6**: Tester chaque décorateur avec différents rôles

#### **Étape 2.7 : Endpoints RAW (read-only)**
- [ ] **Micro-étape 2.7.1**: Créer `src/e2/api/routes/raw.py`
- [ ] **Micro-étape 2.7.2**: Implémenter `GET /api/v1/raw/articles` avec `@require_reader`
- [ ] **Micro-étape 2.7.3**: Utiliser `E1DataReader.read_raw_data()` pour lire données
- [ ] **Micro-étape 2.7.4**: Implémenter `GET /api/v1/raw/articles/{id}`
- [ ] **Micro-étape 2.7.5**: Tester endpoints avec token reader
- [ ] **Micro-étape 2.7.6**: Tester que writer ne peut pas écrire RAW (403)
- [ ] **Micro-étape 2.7.7**: Vérifier que E1 n'est pas modifié (lecture seule)

#### **Étape 2.8 : Endpoints SILVER (read/write)**
- [ ] **Micro-étape 2.8.1**: Créer `src/e2/api/routes/silver.py`
- [ ] **Micro-étape 2.8.2**: Implémenter `GET /api/v1/silver/articles` avec `@require_reader`
- [ ] **Micro-étape 2.8.3**: Implémenter `POST /api/v1/silver/articles` avec `@require_writer`
- [ ] **Micro-étape 2.8.4**: Implémenter `PUT /api/v1/silver/articles/{id}` avec `@require_writer`
- [ ] **Micro-étape 2.8.5**: Implémenter `DELETE /api/v1/silver/articles/{id}` avec `@require_deleter`
- [ ] **Micro-étape 2.8.6**: Tester tous les endpoints avec bons rôles
- [ ] **Micro-étape 2.8.7**: Tester que reader ne peut pas écrire (403)

#### **Étape 2.9 : Endpoints GOLD (read-only)**
- [ ] **Micro-étape 2.9.1**: Créer `src/e2/api/routes/gold.py`
- [ ] **Micro-étape 2.9.2**: Implémenter `GET /api/v1/gold/articles` avec `@require_reader`
- [ ] **Micro-étape 2.9.3**: Implémenter `GET /api/v1/gold/articles/{id}`
- [ ] **Micro-étape 2.9.4**: Implémenter `GET /api/v1/gold/stats`
- [ ] **Micro-étape 2.9.5**: Utiliser `E1DataReader.read_gold_data()` pour lire données
- [ ] **Micro-étape 2.9.6**: Tester endpoints avec token reader
- [ ] **Micro-étape 2.9.7**: Vérifier que E1 n'est pas modifié (lecture seule)

#### **Étape 2.10 : Audit Trail (user_action_log)**
- [ ] **Micro-étape 2.10.1**: Vérifier que table `user_action_log` existe (via E1)
- [ ] **Micro-étape 2.10.2**: Créer fonction `log_action()` dans `src/e2/api/middleware.py`
- [ ] **Micro-étape 2.10.3**: Logger chaque action API (read, create, update, delete)
- [ ] **Micro-étape 2.10.4**: Tester que les logs sont écrits dans `user_action_log`
- [ ] **Micro-étape 2.10.5**: Vérifier que E1 n'est pas modifié (écriture dans table existante)

#### **Étape 2.11 : Tests API**
- [ ] **Micro-étape 2.11.1**: Ajouter `pytest==7.4.3` et `httpx==0.25.0` dans `requirements.txt`
- [ ] **Micro-étape 2.11.2**: Créer `tests/test_e2_api.py`
- [ ] **Micro-étape 2.11.3**: Écrire test `test_login()`
- [ ] **Micro-étape 2.11.4**: Écrire test `test_raw_endpoints()`
- [ ] **Micro-étape 2.11.5**: Écrire test `test_silver_endpoints()`
- [ ] **Micro-étape 2.11.6**: Écrire test `test_gold_endpoints()`
- [ ] **Micro-étape 2.11.7**: Écrire test `test_permissions()`
- [ ] **Micro-étape 2.11.8**: Lancer tous les tests (doivent passer)

#### **Étape 2.12 : Documentation Swagger**
- [ ] **Micro-étape 2.12.1**: Ajouter descriptions dans endpoints FastAPI
- [ ] **Micro-étape 2.12.2**: Ajouter exemples de réponses
- [ ] **Micro-étape 2.12.3**: Vérifier que Swagger UI affiche tout correctement
- [ ] **Micro-étape 2.12.4**: Tester authentification depuis Swagger UI

**✅ Validation Phase 2**: 
- [ ] API FastAPI fonctionne
- [ ] Authentification JWT opérationnelle
- [ ] RBAC par zone implémenté
- [ ] Tous les tests passent
- [ ] E1 n'est pas modifié (isolation respectée)

---

### **PHASE 3 : PYSPARK** ⚡ PRIORITÉ 3

**Objectif**: Traitement Big Data avec PySpark  
**Durée**: 4-6 jours  
**Risque**: ⚠️ Faible (E1 isolé, E3 lit uniquement)

#### **Étape 3.1 : Setup PySpark**
- [ ] **Micro-étape 3.1.1**: Ajouter `pyspark==3.5.0` dans `requirements.txt`
- [ ] **Micro-étape 3.1.2**: Installer dépendances: `pip install -r requirements.txt`
- [ ] **Micro-étape 3.1.3**: Créer `src/e3/spark/__init__.py`
- [ ] **Micro-étape 3.1.4**: Créer `src/e3/spark/session.py` avec `SparkSession` config
- [ ] **Micro-étape 3.1.5**: Configurer SparkSession pour lire Parquet
- [ ] **Micro-étape 3.1.6**: Tester création SparkSession

#### **Étape 3.2 : Lire données GOLD depuis E1**
- [ ] **Micro-étape 3.2.1**: Créer `src/e3/spark/readers/gold_reader.py`
- [ ] **Micro-étape 3.2.2**: Implémenter `read_gold_parquet()` utilisant `E1DataReader.read_gold_data()`
- [ ] **Micro-étape 3.2.3**: Lire Parquet depuis `data/gold/date=YYYY-MM-DD/`
- [ ] **Micro-étape 3.2.4**: Tester lecture avec Spark: `spark.read.parquet("data/gold/")`
- [ ] **Micro-étape 3.2.5**: Vérifier que le DataFrame contient les colonnes attendues
- [ ] **Micro-étape 3.2.6**: Vérifier que E1 n'est pas modifié (lecture seule)

#### **Étape 3.3 : Processeurs Spark**
- [ ] **Micro-étape 3.3.1**: Créer `src/e3/spark/processors/__init__.py`
- [ ] **Micro-étape 3.3.2**: Créer `src/e3/spark/processors/gold_processor.py`
- [ ] **Micro-étape 3.3.3**: Implémenter agrégations (sentiment par source)
- [ ] **Micro-étape 3.3.4**: Implémenter analyses (topics distribution)
- [ ] **Micro-étape 3.3.5**: Tester processeurs avec données réelles
- [ ] **Micro-étape 3.3.6**: Vérifier que E1 n'est pas modifié

#### **Étape 3.4 : Intégration FastAPI**
- [ ] **Micro-étape 3.4.1**: Créer endpoint `GET /api/v1/analytics/sentiment` dans FastAPI
- [ ] **Micro-étape 3.4.2**: Utiliser PySpark pour calculer agrégations
- [ ] **Micro-étape 3.4.3**: Retourner résultats via API
- [ ] **Micro-étape 3.4.4**: Tester endpoint avec données réelles
- [ ] **Micro-étape 3.4.5**: Vérifier que E1 n'est pas modifié

**✅ Validation Phase 3**: 
- [ ] PySpark lit données GOLD
- [ ] Processeurs fonctionnent
- [ ] Intégration FastAPI opérationnelle
- [ ] E1 n'est pas modifié (isolation respectée)

---

### **PHASE 4 : FINE-TUNING ML** ⚡ PRIORITÉ 4

**Objectif**: Fine-tuning FlauBERT & CamemBERT  
**Durée**: 5-7 jours  
**Risque**: ⚠️ Faible (E1 isolé, E3 lit uniquement)

#### **Étape 4.1 : Setup ML**
- [ ] **Micro-étape 4.1.1**: Ajouter `transformers==4.35.0` dans `requirements.txt`
- [ ] **Micro-étape 4.1.2**: Ajouter `torch==2.1.0` dans `requirements.txt`
- [ ] **Micro-étape 4.1.3**: Installer dépendances
- [ ] **Micro-étape 4.1.4**: Créer `src/e3/ml/__init__.py`
- [ ] **Micro-étape 4.1.5**: Créer structure `src/e3/ml/training/`

#### **Étape 4.2 : Préparer datasets depuis GOLD**
- [ ] **Micro-étape 4.2.1**: Créer `src/e3/ml/training/prepare_dataset.py`
- [ ] **Micro-étape 4.2.2**: Utiliser `E1DataReader.read_gold_data()` pour lire données
- [ ] **Micro-étape 4.2.3**: Extraire colonnes nécessaires (text, sentiment, topics)
- [ ] **Micro-étape 4.2.4**: Split train/val/test
- [ ] **Micro-étape 4.2.5**: Tester préparation dataset
- [ ] **Micro-étape 4.2.6**: Vérifier que E1 n'est pas modifié

#### **Étape 4.3 : Fine-tuning FlauBERT (sentiment)**
- [ ] **Micro-étape 4.3.1**: Créer `src/e3/ml/training/train_sentiment.py`
- [ ] **Micro-étape 4.3.2**: Charger modèle `flaubert/flaubert_base_uncased`
- [ ] **Micro-étape 4.3.3**: Configurer Trainer
- [ ] **Micro-étape 4.3.4**: Lancer entraînement
- [ ] **Micro-étape 4.3.5**: Évaluer modèle (accuracy, F1)
- [ ] **Micro-étape 4.3.6**: Sauvegarder modèle

#### **Étape 4.4 : Fine-tuning CamemBERT (topics)**
- [ ] **Micro-étape 4.4.1**: Créer `src/e3/ml/training/train_topics.py`
- [ ] **Micro-étape 4.4.2**: Charger modèle `camembert-base`
- [ ] **Micro-étape 4.4.3**: Configurer Trainer
- [ ] **Micro-étape 4.4.4**: Lancer entraînement
- [ ] **Micro-étape 4.4.5**: Évaluer modèle
- [ ] **Micro-étape 4.4.6**: Sauvegarder modèle

**✅ Validation Phase 4**: 
- [ ] Modèles fine-tunés
- [ ] Métriques satisfaisantes
- [ ] Modèles sauvegardés
- [ ] E1 n'est pas modifié (isolation respectée)

---

### **PHASE 5 : STREAMLIT DASHBOARD** ⚡ PRIORITÉ 5

**Objectif**: Dashboard interactif  
**Durée**: 3-4 jours  
**Risque**: ⚠️ Faible (E1 isolé, lecture seule)

#### **Étape 5.1 : Setup Streamlit**
- [ ] **Micro-étape 5.1.1**: Ajouter `streamlit==1.28.0` dans `requirements.txt`
- [ ] **Micro-étape 5.1.2**: Ajouter `plotly==5.17.0` dans `requirements.txt`
- [ ] **Micro-étape 5.1.3**: Installer dépendances
- [ ] **Micro-étape 5.1.4**: Créer `src/e2/streamlit/__init__.py`
- [ ] **Micro-étape 5.1.5**: Créer `src/e2/streamlit/app.py` avec app basique

#### **Étape 5.2 : Dashboard principal**
- [ ] **Micro-étape 5.2.1**: Créer page `src/e2/streamlit/pages/dashboard.py`
- [ ] **Micro-étape 5.2.2**: Utiliser `E1DataReader` pour lire stats
- [ ] **Micro-étape 5.2.3**: Afficher statistiques globales
- [ ] **Micro-étape 5.2.4**: Créer graphiques sentiment (Plotly)
- [ ] **Micro-étape 5.2.5**: Créer graphiques topics (Plotly)
- [ ] **Micro-étape 5.2.6**: Tester dashboard
- [ ] **Micro-étape 5.2.7**: Vérifier que E1 n'est pas modifié

**✅ Validation Phase 5**: 
- [ ] Dashboard fonctionne
- [ ] Visualisations affichées
- [ ] E1 n'est pas modifié (isolation respectée)

---

### **PHASE 6 : MISTRAL IA GÉNÉRATIVE** ⚡ PRIORITÉ 6

**Objectif**: Insights générés par IA  
**Durée**: 4-5 jours  
**Risque**: ⚠️ Faible (E1 isolé, lecture seule)

#### **Étape 6.1 : Setup Mistral**
- [ ] **Micro-étape 6.1.1**: Ajouter `mistralai==0.0.5` dans `requirements.txt`
- [ ] **Micro-étape 6.1.2**: Configurer `MISTRAL_API_KEY` dans `.env`
- [ ] **Micro-étape 6.1.3**: Créer `src/e3/ai/__init__.py`
- [ ] **Micro-étape 6.1.4**: Créer `src/e3/ai/mistral/client.py`

#### **Étape 6.2 : Génération insights**
- [ ] **Micro-étape 6.2.1**: Créer `src/e3/ai/mistral/insights/summary.py`
- [ ] **Micro-étape 6.2.2**: Utiliser `E1DataReader.read_gold_data()` pour contexte
- [ ] **Micro-étape 6.2.3**: Générer résumé dataset
- [ ] **Micro-étape 6.2.4**: Générer insights climat social
- [ ] **Micro-étape 6.2.5**: Générer insights climat financier
- [ ] **Micro-étape 6.2.6**: Tester génération
- [ ] **Micro-étape 6.2.7**: Vérifier que E1 n'est pas modifié

**✅ Validation Phase 6**: 
- [ ] Insights générés
- [ ] API Mistral fonctionne
- [ ] E1 n'est pas modifié (isolation respectée)

---

## 🛡️ RÈGLES D'OR POUR PROTÉGER E1

### **1. Jamais de modification directe**
❌ **INTERDIT**: Modifier `src/e1/` depuis E2/E3  
✅ **AUTORISÉ**: Utiliser uniquement `E1DataReader` interface

### **2. Tests de non-régression obligatoires**
❌ **INTERDIT**: Merge sans tests E1  
✅ **AUTORISÉ**: Merge uniquement si tous les tests E1 passent

### **3. Versioning E1**
- E1 versionné séparément (ex: `E1-v1.0.0`)
- Changelog E1 séparé
- Tags Git pour chaque version E1

### **4. Documentation interfaces**
- Toute interface E1 → E2/E3 documentée
- Exemples d'utilisation fournis
- Breaking changes documentés

### **5. Monitoring E1**
- Métriques E1 séparées (Prometheus)
- Alertes si E1 échoue
- Dashboard E1 dédié

---

## 📊 CHECKLIST VALIDATION FINALE

Avant de considérer le projet complet :

- [ ] **Phase 0**: E1 isolé et testé
- [ ] **Phase 1**: Docker & CI/CD opérationnels
- [ ] **Phase 2**: FastAPI + RBAC fonctionnels
- [ ] **Phase 3**: PySpark intégré
- [ ] **Phase 4**: Modèles ML fine-tunés
- [ ] **Phase 5**: Dashboard Streamlit actif
- [ ] **Phase 6**: Mistral IA générative opérationnelle
- [ ] **Tests E1**: 100% de passage
- [ ] **Documentation**: Complète et à jour
- [ ] **Isolation E1**: Respectée à 100%

---

## 🎯 PROCHAINES ÉTAPES IMMÉDIATES

1. **Commencer Phase 0** (Isolation E1) - PRIORITÉ ABSOLUE
2. **Valider isolation** avant de continuer
3. **Puis Phase 1** (Docker & CI/CD)
4. **Puis Phase 2** (FastAPI + RBAC)

**⚠️ IMPORTANT**: Ne pas commencer Phase 2 avant d'avoir validé Phase 0 !

---

**Status**: 📋 **PLAN COMPLET - PRÊT POUR IMPLÉMENTATION**  
**Dernière mise à jour**: 2025-12-18
