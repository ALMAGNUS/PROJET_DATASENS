# 🔍 AUDIT ARCHITECTURE - DataSens E1 Pipeline

**Date**: 2025-12-18  
**Objectif**: Pipeline complet Collect → Partition → Clean → CRUD → Aggregate → Gold Export

---

## 📊 ÉTAT ACTUEL

### ✅ Points Positifs
- Extraction fonctionnelle (RSS, API, Scraping, Kaggle, GDELT)
- Base de données bien structurée (6 tables)
- Partitionnement des données par date
- Déduplication par fingerprint

### ❌ Problèmes Identifiés

#### 1. **Architecture Procédurale**
- `viz_raw_silver_gold.py` : 292 lignes de code procédural
- Pas de séparation des responsabilités (SOLID violé)
- Logique métier mélangée avec I/O

#### 2. **Pas de CRUD pour Topics & Sentiment**
- Topics classifiés mais **PAS stockés** dans `DOCUMENT_TOPIC`
- Sentiment calculé mais **PAS stocké** dans `MODEL_OUTPUT`
- Pas de limite à 2 topics max par document

#### 3. **Export GOLD Incomplet**
- Parquet généré mais pas annoté correctement
- CSV GOLD agrégé par source (pas par article)
- Pas de colonnes `topic_1`, `topic_2`, `sentiment` dans GOLD

#### 4. **Code Dupliqué (DRY violé)**
- Classification topics dans `viz_raw_silver_gold.py` ET `main.py`
- Sentiment dans plusieurs endroits
- Logique de collecte répétée

#### 5. **Pipeline Non Structuré**
- Pas de séparation claire : Collect → Partition → Clean → CRUD → Aggregate → Gold
- Tout mélangé dans `main.py` et `viz_raw_silver_gold.py`

---

## 🎯 OBJECTIFS

### Pipeline Complet
```
1. COLLECT    → Extraction depuis toutes sources (RSS, API, Kaggle, GDELT)
2. PARTITION  → Sauvegarde dans data/raw/sources_YYYY-MM-DD/
3. CLEAN      → Nettoyage HTML, normalisation, validation
4. CRUD       → Insert DB + Topics (2 max) + Sentiment (MODEL_OUTPUT)
5. AGGREGATE  → Préparation données pour GOLD
6. GOLD       → Export .parquet + .csv annoté (topic_1, topic_2, sentiment)
```

### Contraintes
- **DOCUMENT_TOPIC** : Maximum 2 topics par document
- **MODEL_OUTPUT** : Sentiment (négatif, neutre, positif) avec score
- **GOLD** : Fichier par article avec colonnes annotées

---

## 🏗️ ARCHITECTURE PROPOSÉE (SOLID/DRY)

### Structure Modulaire

```
src/
├── core.py              # Models (Article, Source) + Extractors
├── ingestion.py         # PartitionedIngester (existant)
├── transformer.py       # ContentTransformer (existant)
├── repository.py        # DatabaseLoader + CRUD (refactor)
├── tagger.py           # TopicTagger (NOUVEAU)
├── analyzer.py         # SentimentAnalyzer (NOUVEAU)
├── aggregator.py       # DataAggregator (NOUVEAU)
└── exporter.py         # GoldExporter (NOUVEAU)

main.py                  # Orchestrateur pipeline
```

### Classes Principales

#### 1. **TopicTagger** (src/tagger.py)
```python
class TopicTagger:
    """Tag articles with max 2 topics → DOCUMENT_TOPIC"""
    def tag(self, article: Article) -> list[tuple[int, float]]:
        # Retourne [(topic_id, confidence), (topic_id, confidence)]
        # Maximum 2 topics
```

#### 2. **SentimentAnalyzer** (src/analyzer.py)
```python
class SentimentAnalyzer:
    """Analyze sentiment → MODEL_OUTPUT"""
    def analyze(self, article: Article) -> tuple[str, float]:
        # Retourne ('positif'|'neutre'|'négatif', score)
```

#### 3. **Repository** (src/repository.py)
```python
class Repository:
    """CRUD pour raw_data, document_topic, model_output"""
    def save_article(self, article, source_id) -> int
    def save_topics(self, raw_data_id, topics: list[tuple])
    def save_sentiment(self, raw_data_id, sentiment: str, score: float)
```

#### 4. **DataAggregator** (src/aggregator.py)
```python
class DataAggregator:
    """Prépare données pour GOLD"""
    def aggregate(self) -> pd.DataFrame:
        # Jointure raw_data + document_topic + model_output
        # Retourne DF avec topic_1, topic_2, sentiment
```

#### 5. **GoldExporter** (src/exporter.py)
```python
class GoldExporter:
    """Export GOLD : parquet + CSV annoté"""
    def export_parquet(self, df: pd.DataFrame) -> Path
    def export_csv(self, df: pd.DataFrame) -> Path
```

---

## 📝 PLAN D'IMPLÉMENTATION

### Phase 1 : Refactor Repository
- [ ] Créer `src/repository.py` avec CRUD complet
- [ ] Méthodes : `save_article()`, `save_topics()`, `save_sentiment()`
- [ ] Gérer limite 2 topics max

### Phase 2 : TopicTagger
- [ ] Créer `src/tagger.py`
- [ ] Classification avec keywords (existant)
- [ ] Retourner top 2 topics avec confidence
- [ ] Insérer dans `DOCUMENT_TOPIC`

### Phase 3 : SentimentAnalyzer
- [ ] Créer `src/analyzer.py`
- [ ] Classification sentiment (existant)
- [ ] Calculer score de confiance
- [ ] Insérer dans `MODEL_OUTPUT`

### Phase 4 : DataAggregator
- [ ] Créer `src/aggregator.py`
- [ ] Requête SQL avec JOINs
- [ ] DataFrame avec colonnes : id, title, content, topic_1, topic_2, sentiment, score

### Phase 5 : GoldExporter
- [ ] Créer `src/exporter.py`
- [ ] Export parquet (partitionné par date)
- [ ] Export CSV annoté

### Phase 6 : Refactor main.py
- [ ] Pipeline clair : collect → partition → clean → crud → aggregate → gold
- [ ] Utiliser nouvelles classes

---

## 🎨 PRINCIPES SOLID APPLIQUÉS

### Single Responsibility
- `TopicTagger` : Uniquement tagging topics
- `SentimentAnalyzer` : Uniquement analyse sentiment
- `Repository` : Uniquement CRUD DB
- `GoldExporter` : Uniquement export

### Open/Closed
- Extractors extensibles (Factory pattern existant)
- Taggers/Analyzers remplaçables

### Dependency Inversion
- Pipeline dépend d'abstractions (interfaces)
- Pas de dépendances directes entre modules

### DRY
- Classification topics centralisée dans `TopicTagger`
- Sentiment centralisé dans `SentimentAnalyzer`
- Pas de duplication

---

## 📊 SCHEMA GOLD

### Colonnes GOLD (par article)
```
- raw_data_id
- source_name
- title
- content
- url
- collected_at
- topic_1          # Premier topic (ou NULL)
- topic_1_score   # Confidence score
- topic_2          # Deuxième topic (ou NULL)
- topic_2_score   # Confidence score
- sentiment        # 'positif' | 'neutre' | 'négatif'
- sentiment_score  # 0.0 - 1.0
```

---

## ✅ VALIDATION

### Tests à Effectuer
1. ✅ Articles insérés avec 2 topics max dans `DOCUMENT_TOPIC`
2. ✅ Sentiment inséré dans `MODEL_OUTPUT`
3. ✅ GOLD parquet généré avec colonnes annotées
4. ✅ GOLD CSV généré avec colonnes annotées
5. ✅ Pipeline complet sans erreur

---

## 🚀 PROCHAINES ÉTAPES

1. Créer les nouveaux modules (`tagger.py`, `analyzer.py`, `aggregator.py`, `exporter.py`)
2. Refactorer `repository.py` pour CRUD complet
3. Refactorer `main.py` pour pipeline clair
4. Tester end-to-end
5. Documenter

---

**Status**: 🔴 À REFACTORER  
**Complexité**: Moyenne  
**Temps estimé**: 4-6h

