# 📁 KAGGLE - Dossier Unique Sans Partitionnement

## ✅ CONFIGURATION ADOPTÉE

**Dossier unique** : `data/raw/kaggle_french_opinions/`

**Fichiers placés directement** (sans sous-dossier `date=YYYY-MM-DD/`) :
- `Comments.csv` (4.1 MB)
- `FrenchNews.csv` (117.3 MB)
- `FrenchNewsDayConcat.csv` (199.7 KB)
- `french_tweets.csv` (126.2 MB)

**Total** : 247.8 MB de données Kaggle

---

## 🔧 MODIFICATIONS APPORTÉES

### **1. KaggleExtractor amélioré** (`src/core.py`)

**Changements** :
- ✅ Support dossier unique (sans partitionnement par date)
- ✅ Utilise `rglob('*.csv')` qui cherche récursivement
- ✅ Détection automatique des colonnes `title`/`content` (avec ou sans header)
- ✅ **Suppression de la limite artificielle** (100 lignes/fichier, 50 articles max)
- ✅ Validation avec `is_valid()` pour chaque article

**Code** :
```python
# Chercher TOUS les CSV récursivement (peu importe le sous-dossier date ou directement dans le dossier)
for csv_file in base.rglob('*.csv'):
    # Détection automatique des colonnes title/content
    # Lecture complète (pas de limite)
```

---

### **2. Aggregator** (`src/aggregator.py`)

**Déjà compatible** :
- ✅ Utilise `rglob('*.csv')` qui trouve les fichiers même sans partitionnement
- ✅ Collecte depuis `kaggle_french_opinions/` automatiquement
- ✅ Intègre dans RAW, puis SILVER, puis GOLD

**Pas de modification nécessaire** : Le code existant fonctionne déjà.

---

### **3. Sources Kaggle désactivées** (`sources_config.json`)

**Sources désactivées** (sans fichiers) :
- `Kaggle_StopWords_28Lang` → `active: false`
- `Kaggle_StopWords` → `active: false`
- `Kaggle_FrenchFinNews` → `active: false`
- `Kaggle_SentimentLexicons` → `active: false`
- `Kaggle_InsuranceReviews` → `active: false`
- `Kaggle_FrenchTweets` → `active: false`

**Source active** :
- `kaggle_french_opinions` → `active: true` ✅

---

## 📊 FLOW DE DONNÉES

### **EXTRACT (KaggleExtractor)**

```
data/raw/kaggle_french_opinions/
├── Comments.csv
├── FrenchNews.csv
├── FrenchNewsDayConcat.csv
└── french_tweets.csv
    ↓
KaggleExtractor.extract()
    ↓
rglob('*.csv') → Trouve TOUS les fichiers
    ↓
Lecture complète (pas de limite)
    ↓
Articles créés → Liste[Article]
```

---

### **AGGREGATE (DataAggregator)**

```
_collect_local_files()
    ↓
Cherche dans data/raw/kaggle_*/
    ↓
rglob('*.csv') → Trouve Comments.csv, FrenchNews.csv, etc.
    ↓
Lecture et ajout au DataFrame RAW
    ↓
Intégration dans SILVER (avec topics)
    ↓
Intégration dans GOLD (avec sentiment)
```

---

## ✅ AVANTAGES

1. ✅ **Simple** : Un seul dossier, pas de partitionnement complexe
2. ✅ **Flexible** : `rglob` trouve les fichiers même dans des sous-dossiers
3. ✅ **Complet** : Tous les fichiers Kaggle lus (pas de limite)
4. ✅ **Compatible** : Fonctionne avec le code existant (aggregator)

---

## 🎯 RÉSULTAT ATTENDU

**Après lancement de `main.py`** :
- ✅ Tous les fichiers CSV de `kaggle_french_opinions/` sont lus
- ✅ Articles intégrés dans `datasens.db` (RAW)
- ✅ Topics assignés (SILVER)
- ✅ Sentiment analysé (GOLD)
- ✅ Exports générés : `exports/raw.csv`, `exports/silver.csv`, `exports/gold.csv`

---

**Status** : ✅ **CODE AMÉLIORÉ - PRÊT POUR TEST**
