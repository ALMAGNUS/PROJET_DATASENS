# Analyse Architecture Métier - DataSens

**Date**: 2025-12-20  
**Basé sur**: Schéma "Architecture métier" - Interface d'évaluation des sentiments

---

## 🎯 Objectif Métier

**Besoin**: Fournir une interface d'évaluation des sentiments croisant différentes sources de données

---

## 📊 Architecture Métier (5 Étapes)

### 1. **Collecte** (Data Ingestion)

**Composants**:
- **Inputs**: Site Web, API, autres sources
- **App**: Web Scraping + Call API
- **DB (buffer quotidien)**: Stockage temporaire quotidien

**Flux**:
```
Sources externes → App (Web Scraping/API) → DB buffer quotidien
```

**État actuel (E1)**:
- ✅ **Implémenté**: 
  - `src/e1/core.py` - Extracteurs (RSS, API, Scraping, GDELT, Kaggle)
  - `src/e1/repository.py` - DB SQLite (buffer quotidien)
  - 21 sources configurées dans `sources_config.json`
  - Déduplication SHA256
  - Logging sync_log

**Gap**:
- ⚠️  **DB buffer quotidien**: Actuellement SQLite unique (pas de partition quotidienne explicite)
- ⚠️  **Scalabilité**: SQLite limité à ~100k articles (OK pour MVP, pas pour production)

**Recommandation**:
- ✅ E1 fonctionne bien pour MVP
- 🔄 Phase 3: Migrer vers partitionnement quotidien (Parquet) pour scalabilité

---

### 2. **Stockage Long Terme** (Long-Term Storage)

**Composants**:
- **Fichiers partitionnés**: Data Lake (Parquet partitionné)
- **App Big Data (ELT)**: Extract, Load, Transform

**Flux**:
```
DB buffer quotidien → App Big Data (ELT) → Fichiers partitionnés
```

**État actuel (E1)**:
- ✅ **Partiellement implémenté**:
  - `src/e1/exporter.py` - Export GOLD vers CSV/Parquet
  - Structure `data/gold/date={YYYY-MM-DD}/` (partitionnement par date)
  - Export Parquet fonctionnel

**Gap**:
- ⚠️  **ELT complet**: Export manuel, pas de pipeline automatisé
- ⚠️  **Big Data**: Pas encore PySpark pour traitement distribué
- ⚠️  **Transformations**: Nettoyage basique, pas de transformations complexes

**Recommandation**:
- 🔄 **Phase 3 (PySpark)**: 
  - Pipeline ELT automatisé
  - Traitement distribué avec Spark
  - Transformations avancées (agrégations, jointures)

---

### 3. **Mise à disposition des données** (Data Provisioning)

**Composants**:
- **App API**: API REST pour accès aux données
- **DB**: Base de données pour API

**Flux**:
```
App Big Data → DB → App API → Consommateurs
```

**État actuel (E2)**:
- ✅ **Implémenté**:
  - `src/e2/api/main.py` - FastAPI application
  - Endpoints RAW/SILVER/GOLD
  - Authentification JWT + RBAC
  - Lecture via `E1DataReader` (isolation E1)
  - Audit trail complet

**Gap**:
- ⚠️  **DB pour API**: Utilise directement DB E1 (pas de DB dédiée API)
- ⚠️  **Cache**: Pas de cache pour performances
- ⚠️  **Écriture SILVER**: Retourne 501 (isolation E1)

**Recommandation**:
- ✅ E2 fonctionne bien pour MVP
- 🔄 **Phase 3**: 
  - Cache Redis pour performances
  - DB dédiée API (si nécessaire)
  - Écriture SILVER via PySpark (si nécessaire)

---

### 4. **Application IA** (AI Application)

**Composants**:
- **Analyse de sentiments**: 
  - **Logique**: Business logic
  - **Modèles**: Modèles ML (sentiment analysis)
- **Restitution (MVC)**: Interface utilisateur

**Flux**:
```
App API → Analyse de sentiments (Logique + Modèles) → Restitution (MVC) → Utilisateurs
```

**État actuel**:
- ✅ **Partiellement implémenté**:
  - `src/e1/analyzer.py` - SentimentAnalyzer (basique)
  - `src/e1/tagger.py` - TopicTagger (basique)
  - `src/dashboard.py` - Dashboard Streamlit (basique)
  - Modèles: Utilise des modèles pré-entraînés (pas de fine-tuning)

**Gap**:
- ⚠️  **Modèles**: Pas de fine-tuning FlauBERT/CamemBERT
- ⚠️  **Logique métier**: Analyse basique, pas de croisement de sources
- ⚠️  **Restitution MVC**: Dashboard Streamlit basique, pas de MVC structuré
- ⚠️  **Interface d'évaluation**: Pas d'interface dédiée pour évaluation croisée

**Recommandation**:
- 🔄 **Phase 4 (ML Fine-tuning)**:
  - Fine-tuning FlauBERT pour sentiment français
  - Fine-tuning CamemBERT pour topics français
  - Évaluation F1/Precision/Recall
- 🔄 **Phase 5 (Streamlit Dashboard)**:
  - Dashboard MVC structuré
  - Visualisations croisées de sources
  - Interface d'évaluation des sentiments
- 🔄 **Phase 6 (Mistral IA)**:
  - Insights générés par IA
  - Analyse croisée automatique

---

### 5. **Gestion IA** (AI Management)

**Composants**:
- **Apprentissage / Spécialisation**: 
  - **Modèles**: Gestion des modèles
  - **Dataset**: Datasets d'entraînement
- **Monitoring IA (KPI)**: Suivi des performances

**Flux**:
```
Modèles (Analyse) → Apprentissage/Spécialisation (Modèles + Dataset) → Modèles (Analyse)
Modèles (Analyse) → Monitoring IA (KPI) → Apprentissage/Spécialisation
```

**État actuel**:
- ❌ **Non implémenté**:
  - Pas de pipeline d'apprentissage
  - Pas de versioning de modèles (MLflow)
  - Pas de monitoring KPI IA
  - Pas de feedback loop

**Gap**:
- ⚠️  **MLOps**: Aucun composant MLOps
- ⚠️  **Versioning**: Pas de gestion de versions de modèles
- ⚠️  **Monitoring**: Pas de KPIs IA (accuracy, drift, etc.)
- ⚠️  **Feedback**: Pas de boucle de feedback pour amélioration

**Recommandation**:
- 🔄 **Phase 4 (ML Fine-tuning)**:
  - MLflow pour versioning
  - Pipeline d'entraînement
  - Évaluation automatique (F1, Precision, Recall)
- 🔄 **Phase 7 (MLOps)**:
  - Monitoring KPIs IA (accuracy, drift detection)
  - A/B testing
  - Feedback loop automatique
  - Retraining pipeline

---

## 🔄 Mapping Architecture Métier → Implémentation

| Architecture Métier | Implémentation Actuelle | Status | Phase |
|---------------------|------------------------|--------|-------|
| **1. Collecte** | E1 - Extracteurs + Repository | ✅ 90% | E1 (Complet) |
| **2. Stockage Long Terme** | E1 - Exporter (Parquet) | ⚠️ 60% | E3 (PySpark) |
| **3. Mise à disposition** | E2 - FastAPI + RBAC | ✅ 100% | E2 (Complet) |
| **4. Application IA** | E1 - Analyzer + Dashboard | ⚠️ 40% | E4-E6 (À faire) |
| **5. Gestion IA** | - | ❌ 0% | E4, E7 (À faire) |

---

## 📋 Plan d'Alignement

### Phase 3: PySpark Integration (Priorité 1)

**Objectif**: Compléter étape 2 (Stockage Long Terme)

**Tâches**:
- [ ] Pipeline ELT automatisé avec PySpark
- [ ] Traitement distribué des données
- [ ] Transformations avancées (agrégations, jointures)
- [ ] Intégration avec E2 API (lecture depuis Parquet)
- [ ] Optimisation partitionnement (date, source)

**Livrables**:
- `src/spark/` - Modules PySpark
- Pipeline ELT automatisé
- Tests PySpark

**Impact**: Scalabilité à 100k+ articles, traitement distribué

---

### Phase 4: ML Fine-tuning (Priorité 2)

**Objectif**: Améliorer étape 4 (Application IA) - Modèles

**Tâches**:
- [ ] Fine-tuning FlauBERT (sentiment français)
- [ ] Fine-tuning CamemBERT (topics français)
- [ ] MLflow pour versioning
- [ ] Pipeline d'évaluation (F1, Precision, Recall)
- [ ] Intégration modèles dans E1 Analyzer

**Livrables**:
- Modèles fine-tunés
- MLflow registry
- Pipeline d'entraînement

**Impact**: Accuracy +25%, modèles spécialisés français

---

### Phase 5: Streamlit Dashboard (Priorité 2)

**Objectif**: Compléter étape 4 (Application IA) - Restitution

**Tâches**:
- [ ] Architecture MVC pour Streamlit
- [ ] Dashboard croisé de sources
- [ ] Visualisations interactives (Plotly)
- [ ] Interface d'évaluation des sentiments
- [ ] Intégration avec E2 API

**Livrables**:
- Dashboard Streamlit structuré
- Visualisations croisées
- Interface utilisateur complète

**Impact**: Interface utilisateur professionnelle, évaluation croisée

---

### Phase 6: Mistral IA (Priorité 3)

**Objectif**: Enrichir étape 4 (Application IA) - Insights IA

**Tâches**:
- [ ] Intégration Mistral API
- [ ] Génération d'insights automatiques
- [ ] Analyse croisée par IA
- [ ] Climat social/financier

**Livrables**:
- Service Mistral IA
- Insights générés automatiquement

**Impact**: Valeur ajoutée IA, insights automatiques

---

### Phase 7: MLOps (Priorité 3)

**Objectif**: Compléter étape 5 (Gestion IA)

**Tâches**:
- [ ] Monitoring KPIs IA (accuracy, drift)
- [ ] A/B testing
- [ ] Feedback loop automatique
- [ ] Retraining pipeline
- [ ] Alertes automatiques

**Livrables**:
- Système de monitoring IA
- Pipeline de retraining
- Dashboard MLOps

**Impact**: Modèles maintenus, qualité garantie

---

## 🎯 Recommandations Stratégiques

### 1. Priorisation

**Court terme (1-2 mois)**:
1. ✅ Phase 3 (PySpark) - Scalabilité critique
2. ✅ Phase 4 (ML Fine-tuning) - Amélioration qualité

**Moyen terme (3-4 mois)**:
3. Phase 5 (Streamlit Dashboard) - Interface utilisateur
4. Phase 6 (Mistral IA) - Valeur ajoutée

**Long terme (5-6 mois)**:
5. Phase 7 (MLOps) - Maintenance et qualité

### 2. Architecture Technique

**Recommandations**:
- ✅ **Isolation E1/E2/E3**: Maintenir (excellent)
- ✅ **API Gateway**: E2 actuel suffit (FastAPI)
- 🔄 **Cache**: Ajouter Redis en Phase 3
- 🔄 **Message Queue**: Considérer pour Phase 3 (traitement asynchrone)
- 🔄 **Monitoring**: Prometheus actuel + Grafana en Phase 7

### 3. Gaps Critiques

**À adresser en priorité**:
1. **Scalabilité**: SQLite → PySpark (Phase 3)
2. **Qualité modèles**: Fine-tuning (Phase 4)
3. **Interface utilisateur**: Dashboard structuré (Phase 5)

**Moins critique**:
4. MLOps complet (Phase 7)
5. Mistral IA (Phase 6)

---

## 📊 Matrice de Maturité

| Composant | Maturité | Action Requise |
|-----------|----------|----------------|
| Collecte (E1) | 🟢 Mature (90%) | Optimisation partitionnement |
| Stockage Long Terme | 🟡 Partiel (60%) | PySpark ELT pipeline |
| Mise à disposition (E2) | 🟢 Mature (100%) | Cache Redis |
| Application IA - Modèles | 🟡 Basique (40%) | Fine-tuning FlauBERT/CamemBERT |
| Application IA - Interface | 🟡 Basique (30%) | Dashboard MVC structuré |
| Gestion IA | 🔴 Absent (0%) | MLOps complet |

---

## ✅ Conclusion

**Points forts**:
- ✅ Architecture E1/E2 solide et isolée
- ✅ Collecte et API fonctionnelles
- ✅ Base technique solide (OOP/SOLID/DRY)

**Points à améliorer**:
- 🔄 Scalabilité (PySpark)
- 🔄 Qualité modèles (Fine-tuning)
- 🔄 Interface utilisateur (Dashboard)
- 🔄 MLOps (Monitoring, retraining)

**Prochaine étape recommandée**: **Phase 3 (PySpark Integration)**

---

**Document créé**: 2025-12-20  
**Auteur**: Analyse architecture métier  
**Version**: 1.0
