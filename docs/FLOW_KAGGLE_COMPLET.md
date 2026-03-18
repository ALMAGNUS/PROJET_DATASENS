# 📊 FLOW KAGGLE COMPLET : De Fichiers → DB → SILVER → GOLD

## ✅ RÉPONSE DIRECTE

**OUI**, les fichiers Kaggle sont :
1. ✅ **Nettoyés** (ContentTransformer)
2. ✅ **Chargés dans datasens.db** (table `raw_data`)
3. ✅ **Enrichis** (topics dans `document_topic`, sentiment dans `model_output`)
4. ✅ **Agrégés** dans RAW → SILVER → GOLD
5. ✅ **Exportés** en CSV/Parquet

---

## 🔄 FLOW COMPLET KAGGLE

### **ÉTAPE 1 : EXTRACT**

```
Fichiers Kaggle (data/raw/kaggle_french_opinions/*.csv)
├── Comments.csv
├── FrenchNews.csv
├── FrenchNewsDayConcat.csv
└── french_tweets.csv
    ↓
KaggleExtractor.extract()
    ↓
Lecture de TOUS les fichiers CSV (rglob récursif)
    ↓
Détection automatique colonnes title/content
    ↓
Création Articles → Liste[Article]
```

**Résultat** : Articles extraits depuis les fichiers CSV

---

### **ÉTAPE 2 : CLEAN**

```
Liste[Article]
    ↓
ContentTransformer.transform()
    ├── Suppression HTML
    ├── Normalisation espaces
    └── Validation
    ↓
Articles nettoyés et validés
```

**Résultat** : Articles nettoyés

---

### **ÉTAPE 3 : LOAD (Chargement DB)**

```
Articles nettoyés
    ↓
Repository.load_article_with_id()
    ├── Calcul fingerprint (SHA256)
    ├── Vérification doublon
    ├── INSERT INTO raw_data
    └── Retourne raw_data_id
    ↓
TopicTagger.tag(raw_data_id)
    └── INSERT INTO document_topic (2 topics)
    ↓
SentimentAnalyzer.analyze(raw_data_id)
    └── INSERT INTO model_output (sentiment)
```

**Résultat** : Articles dans `datasens.db` :
- ✅ Table `raw_data` : Articles bruts
- ✅ Table `document_topic` : Topics assignés
- ✅ Table `model_output` : Sentiment assigné

---

### **ÉTAPE 4 : AGGREGATE**

#### **RAW** (`aggregate_raw()`)

```sql
SELECT r.raw_data_id as id, s.name as source, r.title, r.content, ...
FROM raw_data r 
JOIN source s ON r.source_id = s.source_id
WHERE s.name = 'kaggle_french_opinions'
```

**Résultat** : DataFrame RAW avec articles Kaggle depuis la DB

---

#### **SILVER** (`aggregate_silver()`)

```
RAW DataFrame
    ↓
JOIN document_topic
    ↓
2 topics par article (topic_1, topic_2)
    ↓
DataFrame SILVER
```

**Résultat** : DataFrame SILVER avec topics

---

#### **GOLD** (`aggregate()`)

```
SILVER DataFrame
    ↓
JOIN model_output
    ↓
Sentiment ajouté
    ↓
DataFrame GOLD
```

**Résultat** : DataFrame GOLD avec topics + sentiment

---

### **ÉTAPE 5 : EXPORT**

```
DataFrame GOLD
    ↓
GoldExporter.export()
    ├── exports/gold.csv
    ├── exports/gold.parquet
    └── data/gold/date=YYYY-MM-DD/articles.parquet
```

**Résultat** : Exports CSV et Parquet

---

## ✅ CORRECTION EFFECTUÉE

### **Problème identifié**

`_collect_local_files()` lisait aussi les fichiers Kaggle alors qu'ils sont déjà dans la DB via `KaggleExtractor` → **risque de duplication**.

### **Solution appliquée**

**Modifié `src/aggregator.py`** :
- ✅ **Kaggle exclu** de `_collect_local_files()` (comme ZZDB)
- ✅ **Seulement GDELT** est lu depuis fichiers locaux (si pas dans DB)
- ✅ **Kaggle vient uniquement de la DB** (via `aggregate_raw()` qui lit depuis `raw_data`)

**Code modifié** :
```python
def _collect_local_files(self) -> pd.DataFrame:
    """Collect GDELT files from local data/raw/ (ZZDB and Kaggle excluded: already in DB)"""
    # Seulement GDELT, pas Kaggle
    for gdelt_dir in p.glob('gdelt_*'):
        # ...
```

---

## 📊 RÉSUMÉ DU FLOW

| Étape | Action | Résultat |
|-------|--------|----------|
| **EXTRACT** | KaggleExtractor lit fichiers CSV | Liste[Article] |
| **CLEAN** | ContentTransformer nettoie | Articles nettoyés |
| **LOAD** | Repository charge dans DB | Articles dans `raw_data` |
| **TAG** | TopicTagger assigne topics | Topics dans `document_topic` |
| **ANALYZE** | SentimentAnalyzer assigne sentiment | Sentiment dans `model_output` |
| **AGGREGATE RAW** | Lit depuis DB (pas fichiers locaux) | DataFrame RAW |
| **AGGREGATE SILVER** | RAW + topics | DataFrame SILVER |
| **AGGREGATE GOLD** | SILVER + sentiment | DataFrame GOLD |
| **EXPORT** | CSV/Parquet | Fichiers exports |

---

## ✅ RÉPONSE FINALE

**OUI**, les fichiers Kaggle sont :
- ✅ **Nettoyés** (ContentTransformer)
- ✅ **Chargés dans datasens.db** (table `raw_data`)
- ✅ **Enrichis** (topics + sentiment)
- ✅ **Agrégés** dans RAW → SILVER → GOLD
- ✅ **Exportés** en CSV/Parquet

**Pas de duplication** : Kaggle exclu de `_collect_local_files()`, vient uniquement de la DB.

---

**Status** : ✅ **FLOW COMPLET - KAGGLE DANS LA DB + EXPORTS**
