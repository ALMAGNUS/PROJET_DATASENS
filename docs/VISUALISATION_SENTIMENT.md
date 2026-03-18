# 📊 Guide de Visualisation des Sentiments - DataSens E1

**Objectif**: Comment visualiser les annotations de sentiment (positif/neutre/négatif)

---

## ✅ Vérification: Les Sentiments Sont Présents!

Les sentiments sont **bien présents** dans vos données:
- ✅ **Base de données**: Articles avec sentiment dans `model_output`
- ✅ **Fichier gold.csv**: Colonnes `sentiment` et `sentiment_score` présentes

---

## 🎯 Comment Visualiser les Sentiments

### 1️⃣ **Test et Vérification** (Recommandé en premier)

```bash
python scripts/test_pipeline.py
```

**Affiche:**
- ✅ Vérification des sentiments dans la base de données
- ✅ Vérification des sentiments dans gold.csv
- ✅ Exemples d'articles avec sentiment
- ✅ Résumé des tests

---

### 2️⃣ **Visualisations Graphiques** (Graphiques PNG)

```bash
python scripts/visualize_sentiment.py
```

**Crée 4 graphiques dans `visualizations/sentiment_analysis.png`:**
1. **Distribution du sentiment** (barres)
2. **Répartition du sentiment** (camembert %)
3. **Score moyen par sentiment** (barres)
4. **Distribution des scores** (histogramme)

**Affiche aussi:**
- Statistiques détaillées par sentiment
- Exemples d'articles par sentiment
- Sentiment par source (top 10)
- Sentiment par topic (top 10)

**Fichier généré:**
```
visualizations/sentiment_analysis.png
```

---

### 3️⃣ **Aperçu Rapide** (Texte dans la console)

```bash
python scripts/quick_view.py
```

**Affiche:**
- Distribution des topics
- **Distribution du sentiment** avec emojis (✅ ⚪ ❌)
- Top 10 sources
- 5 exemples d'articles enrichis avec topics + sentiment

---

### 4️⃣ **Dashboard Complet** (Statistiques globales)

```bash
python scripts/show_dashboard.py
```

**Affiche:**
- Résumé global (total articles, enrichis, nouveaux)
- Nouveaux articles par source aujourd'hui
- Enrichissement Topics
- **Enrichissement Sentiment** (distribution positif/neutre/négatif)
- Articles par source
- Évaluation dataset pour IA

---

### 5️⃣ **Explorer les CSV** (Interactif)

```bash
python scripts/view_exports.py
```

**Menu interactif pour voir:**
- `raw.csv` - Données brutes
- `silver.csv` - Données avec topics
- `gold.csv` - **Données avec topics + sentiment** ⭐

**Dans gold.csv, vous verrez les colonnes:**
- `sentiment` - Valeur: `positif`, `neutre`, ou `négatif`
- `sentiment_score` - Score de confiance (0.0 à 1.0)

---

## 📊 Où Trouver les Sentiments

### Dans les Fichiers

1. **`exports/gold.csv`**
   - Colonnes: `sentiment`, `sentiment_score`
   - Ouvrable dans Excel, LibreOffice, ou tout éditeur CSV

2. **`data/gold/date=YYYY-MM-DD/articles.parquet`**
   - Format Parquet (compatible PySpark)
   - Colonnes: `sentiment`, `sentiment_score`

### Dans la Base de Données

**Table `model_output`:**
```sql
SELECT label, COUNT(*) as count, AVG(score) as avg_score
FROM model_output 
WHERE model_name = 'sentiment_keyword'
GROUP BY label
```

**Résultat:**
- `label` = `'positif'`, `'neutre'`, ou `'négatif'`
- `score` = Score de confiance (0.0 à 1.0)

---

## 🔍 Exemples Concrets

### Exemple 1: Article Positif

```csv
id,source,title,sentiment,sentiment_score
1500,yahoo_finance,"CAC 40 en hausse de 2%",positif,0.909
```

### Exemple 2: Article Négatif

```csv
id,source,title,sentiment,sentiment_score
1501,trustpilot_reviews,"Service décevant",négatif,0.834
```

### Exemple 3: Article Neutre

```csv
id,source,title,sentiment,sentiment_score
1502,google_news_rss,"Actualité générale",neutre,0.500
```

---

## 📈 Statistiques Actuelles

D'après vos données actuelles:

| Sentiment | Nombre | Pourcentage | Score Moyen |
|-----------|--------|------------|-------------|
| ⚪ Neutre  | 1,717  | 98.7%      | 0.500       |
| ✅ Positif | 16     | 0.9%       | 0.912       |
| ❌ Négatif | 7      | 0.4%       | 0.834       |

**Total**: 1,740 articles analysés

---

## 🎨 Visualisations Disponibles

### Graphiques PNG

**Fichier**: `visualizations/sentiment_analysis.png`

Contient 4 graphiques:
1. **Barres** - Distribution du sentiment
2. **Camembert** - Répartition en pourcentage
3. **Barres** - Score moyen par sentiment
4. **Histogramme** - Distribution des scores

**Pour ouvrir:**
- Double-clic sur le fichier PNG
- Ou dans un navigateur/image viewer

---

## 🚀 Commandes Rapides

```bash
# 1. Tester que tout fonctionne
python scripts/test_pipeline.py

# 2. Créer les graphiques
python scripts/visualize_sentiment.py

# 3. Voir l'aperçu texte
python scripts/quick_view.py

# 4. Dashboard complet
python scripts/show_dashboard.py

# 5. Explorer les CSV
python scripts/view_exports.py
```

---

## ❓ Problèmes Courants

### "Colonne sentiment introuvable"

**Solution:**
```bash
# Relancer le pipeline pour générer les sentiments
python main.py
```

### "Aucun sentiment dans la base de données"

**Solution:**
```bash
# Enrichir tous les articles existants
python scripts/enrich_all_articles.py
```

### "Graphiques ne s'affichent pas"

**Vérifier:**
- `matplotlib` est installé: `pip install matplotlib`
- Le fichier PNG est créé dans `visualizations/sentiment_analysis.png`

---

## 📝 Notes Techniques

### Comment les Sentiments Sont Calculés

1. **Analyse** du texte (title + content)
2. **Comptage** des mots positifs/négatifs
3. **Classification**:
   - Plus de positifs → `positif`
   - Plus de négatifs → `négatif`
   - Sinon → `neutre`
4. **Score** = Confiance (0.0 à 1.0)

### Mots-clés Utilisés

**Positifs**: bien, excellent, super, bon, fantastique, génial, parfait, merveilleux, formidable

**Négatifs**: mal, mauvais, horrible, terrible, nul, catastrophe, déçu, problème, crise

---

## ✅ Checklist

- [x] Sentiments présents dans la DB
- [x] Sentiments présents dans gold.csv
- [x] Scripts de visualisation créés
- [x] Graphiques générés
- [x] Dashboard fonctionnel

---

**Status**: ✅ **TOUS LES OUTILS DE VISUALISATION SONT DISPONIBLES**

Pour toute question, consultez:
- `docs/E1_STATUS.md` - État du projet E1
- `docs/DATA_FLOW.md` - Flow complet des données
