# 📋 Dossier E1 — Guide 2 : Annotations Topics et Sentiments

**Pour le jury** : Une fois les articles nettoyés et chargés en base, nous les enrichissons automatiquement avec deux types d’annotations. D’abord les topics : chaque article reçoit jusqu’à deux catégories (finance, politique, technologie, etc.) via une classification par mots-clés. Ensuite le sentiment : nous classifions chaque texte comme positif, neutre ou négatif à l’aide d’un analyseur par mots-clés pondérés. Ces annotations alimentent les zones SILVER et GOLD du pipeline et servent de base aux analyses et au fine-tuning des modèles IA. Les scripts présentés montrent comment exploiter ces composants et interroger les résultats en SQL.

**Objectif** : Documenter l'enrichissement des articles (topics + sentiment) et fournir les scripts exécutables.

---

## 1. Vue d'ensemble

Les articles bruts ne contiennent que du texte. Pour les exploiter (filtrage, statistiques, fine-tuning de modèles), nous les enrichissons avec des métadonnées sémantiques : d'une part des **topics** (finance, politique, etc.) pour catégoriser le sujet, d'autre part un **sentiment** (positif, neutre, négatif) pour capter la tonalité. Ces annotations sont produites par des algorithmes à base de mots-clés, rapides et reproductibles, sans dépendre d'un service externe.

Après le nettoyage et le chargement en base, chaque article est enrichi par :

| Composant | Table | Rôle |
|-----------|-------|------|
| **TopicTagger** | `document_topic` | Assignation de 2 topics (topic_1, topic_2) par article |
| **SentimentAnalyzer** | `model_output` | Classification sentiment : **positif**, **neutre**, **négatif** |

---

## 2. Topics — Classification par mots-clés

Le **TopicTagger** associe à chaque article jusqu'à deux sujets principaux. Il repose sur des dictionnaires de mots-clés par topic : plus un article contient de termes liés à un thème, plus le score de ce topic est élevé. L'algorithme est déterministe et explicable, contrairement à un modèle neuronal opaque.

### 2.1 Topics disponibles

- **finance**, **entreprise**, **politique**, **technologie**
- **santé**, **société**, **environnement**, **sport**, **média**
- **culture**, **transport**, **logement**, **sécurité**
- **éducation**, **travail**, **retraite**, **jeunesse**, **international**
- **autre** : articles non classés (défaut)

### 2.2 Algorithme

1. Concaténation `title + content` en minuscules
2. Comptage des mots-clés par topic : `score = nb_matches / nb_keywords` (max 1.0)
3. Tri par score décroissant
4. Assignation de **2 topics** (topic_1 = meilleur, topic_2 = second) avec score de confiance
5. Si aucun topic trouvé → assignation de "autre" (confiance 0.3)

### 2.3 Tables impactées

```sql
-- document_topic : liaison article ↔ topic
raw_data_id | topic_id | confidence_score
```

---

## 3. Sentiments — Classification par mots-clés

Le **SentimentAnalyzer** classe chaque texte en positif, neutre ou négatif. Il utilise des listes de mots positifs et négatifs, chacun pondéré (fort ou modéré). Le score total permet de trancher entre les trois labels. Ce modèle est enregistré sous le nom `sentiment_keyword` dans la table `model_output`, afin de le distinguer d'un éventuel modèle ML fine-tuné (`sentiment_ml`).

### 3.1 Labels

| Label | Signification |
|-------|---------------|
| **positif** | Tonalité positive |
| **neutre** | Tonalité neutre ou indécise |
| **négatif** | Tonalité négative |

### 3.2 Algorithme

- Mots-clés **positifs** (forts : poids 2, modérés : poids 1)
- Mots-clés **négatifs** (forts : poids 2, modérés : poids 1)
- Score total = somme des occurrences pondérées
- Ratio pos/neg → décision + score de confiance (0.0–0.95)
- Modèle enregistré : `sentiment_keyword`

### 3.3 Règles de décision (simplifiées)

- `pos_score >= 3` et `pos_ratio >= 0.5` → **positif**
- `neg_score >= 3` et `neg_ratio >= 0.5` → **négatif**
- `neg_ratio > 0.6` et `neg_score >= 2` → **négatif**
- Sinon, selon comparaison pos/neg → **positif**, **négatif** ou **neutre**

### 3.4 Table impactée

```sql
-- model_output
raw_data_id | model_name | label | score
```

---

## 4. Scripts exécutables

### 4.1 Enrichir tous les articles (rétroactif)

```bash
# Enrichit tous les articles sans topics ou sans sentiment
python scripts/enrich_all_articles.py
```

### 4.2 Tagger + Analyzer — usage direct

```python
# Tagger : assigner topics à un article
import os
from pathlib import Path
from src.e1.tagger import TopicTagger
from src.e1.analyzer import SentimentAnalyzer

DB_PATH = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))

tagger = TopicTagger(DB_PATH)
analyzer = SentimentAnalyzer(DB_PATH)

# Exemple : article existant (raw_data_id = 1)
raw_id = 1
title = "La bourse monte en flèche après les annonces du gouvernement"
content = "Les marchés réagissent positivement à la nouvelle réforme fiscale."

# Topics (2 par article)
tagger.tag(raw_id, title, content)

# Sentiment
analyzer.save(raw_id, title, content)

tagger.close()
analyzer.close()
```

### 4.3 Analyser le sentiment sans sauvegarder

```python
# Obtenir le label et le score sans écrire en base
from src.e1.analyzer import SentimentAnalyzer
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
analyzer = SentimentAnalyzer(DB_PATH)

text = "Cette réforme est catastrophique pour les retraités."
label, score = analyzer.analyze(text)
print(f"Sentiment: {label} (confiance: {score})")  # négatif (0.xx)

analyzer.close()
```

### 4.4 Requête SQL : distribution des sentiments

```python
import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
conn = sqlite3.connect(DB_PATH)

query = """
SELECT mo.label AS sentiment, COUNT(*) AS nb
FROM model_output mo
WHERE mo.model_name = 'sentiment_keyword'
GROUP BY mo.label
ORDER BY nb DESC
"""
for row in conn.execute(query).fetchall():
    print(f"{row[0]}: {row[1]}")
conn.close()
```

### 4.5 Requête SQL : vue GOLD (articles + topics + sentiment)

```python
import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
conn = sqlite3.connect(DB_PATH)

query = """
SELECT r.title,
       s.name AS source,
       t.name AS topic,
       mo.label AS sentiment,
       mo.score AS sentiment_score
FROM raw_data r
JOIN source s ON s.source_id = r.source_id
LEFT JOIN document_topic dt ON dt.raw_data_id = r.raw_data_id
LEFT JOIN topic t ON t.topic_id = dt.topic_id
LEFT JOIN model_output mo ON mo.raw_data_id = r.raw_data_id AND mo.model_name = 'sentiment_keyword'
ORDER BY r.collected_at DESC
LIMIT 100
"""
for row in conn.execute(query).fetchall():
    print(row)
conn.close()
```

### 4.6 Ré-analyser le sentiment de tous les articles

```bash
# Réapplique l'analyse sentiment sur tous les articles (écrase les anciennes prédictions)
python scripts/reanalyze_sentiment.py
```

---

## 5. Intégration dans le pipeline E1

```
LOAD (article chargé) → tagger.tag() → analyzer.save() → article enrichi
```

- **Automatique** : à chaque `python main.py`, les nouveaux articles sont taggés et analysés
- **Rétroactif** : `enrich_all_articles.py` pour les articles déjà en base

---

## 6. Résumé

| Composant | Fichier | Méthode principale |
|-----------|---------|--------------------|
| TopicTagger | `src/e1/tagger.py` | `tag(raw_data_id, title, content)` |
| SentimentAnalyzer | `src/e1/analyzer.py` | `analyze(text)` → (label, score), `save(raw_data_id, title, content)` |

| Script | Rôle |
|--------|------|
| `enrich_all_articles.py` | Enrichissement rétroactif complet |
| `reanalyze_sentiment.py` | Ré-analyse sentiment uniquement |
