# 📋 Dossier E1 — Guide 1 : Nettoyage des données

**Pour le jury** : Le pipeline E1 collecte des données hétérogènes (RSS, API, scraping, CSV). Avant tout stockage ou enrichissement, nous appliquons un nettoyage strict : suppression des caractères problématiques (BOM, null bytes), extraction du texte depuis le HTML, normalisation des espaces et déduplication par empreinte SHA256. Ces règles garantissent des données fiables et exploitables en aval. Les scripts ci-dessous sont des extraits exécutables tirés du code de production.

**Objectif** : Documenter les étapes de nettoyage des données du pipeline E1 et fournir les scripts exécutables correspondants.

---

## 1. Vue d'ensemble du nettoyage E1

Les données collectées proviennent de sources très diverses : flux RSS (XML), réponses API (JSON), pages HTML scrapées, fichiers CSV. Chaque source introduit son lot d'artefacts : balises HTML, caractères de contrôle, encodages variables, doublons. Le nettoyage consiste à ramener tout cela à un format homogène et exploitable avant stockage. Sans cette étape, les analyses ultérieures et les modèles IA seraient faussés par du bruit ou des doublons.

Le nettoyage s'effectue à **deux niveaux** dans le pipeline :

| Étape | Rôle | Fichier / Composant |
|-------|------|---------------------|
| **CLEAN** | Transformation du texte brut | `ContentTransformer` (src/e1/core.py) |
| **LOAD** | Déduplication + qualité | `Repository.load_article_with_id()` |

```
Articles bruts → ContentTransformer.transform() → Articles nettoyés → load_article_with_id() → DB (sans doublons)
```

---

## 2. Règles de nettoyage

Chaque règle répond à un problème concret rencontré en production. Elles sont appliquées dans un ordre précis pour éviter que des caractères résiduels ne perturbent les étapes suivantes.

### 2.1 Sanitization du texte (`sanitize_text`)

Les fichiers CSV ou XML peuvent contenir des caractères invisibles qui provoquent des erreurs en base ou lors du traitement. La fonction `sanitize_text` applique les filtres suivants :

- Suppression du BOM (`\ufeff`), marqueur d'encodage UTF-8 en début de fichier
- Suppression des null bytes (`\x00`), incompatibles avec SQLite et certains traitements
- Suppression des caractères de contrôle (ord < 32, sauf espace, tabulation, nouvelle ligne)
- Suppression du caractère de remplacement Unicode (`\ufffd`), inséré quand un caractère ne peut pas être décodé
- Normalisation Unicode (NFC) pour éviter les doublons : un même caractère accentué (é) peut exister sous plusieurs formes binaires ; NFC unifie ces représentations.

### 2.2 Nettoyage HTML (`ContentTransformer.clean_html`)

Les sources web (scraping, flux RSS) fournissent souvent du contenu encadré de balises HTML. Nous utilisons BeautifulSoup pour extraire uniquement le texte lisible, sans balises ni scripts :

- Parsing HTML via BeautifulSoup
- Extraction du texte brut (balises supprimées)
- Séparateur d’espaces entre blocs

### 2.3 Normalisation des espaces (`ContentTransformer.normalize`)

- Remplacement des espaces multiples par un seul espace : `re.sub(r"\s+", " ", text)`
- Trim des espaces en début et fin

### 2.4 Validation (`Article.is_valid`)

- Titre : `len(title.strip()) > 3`
- Contenu : `len(content.strip()) > 10`
- Articles ne respectant pas ces critères sont exclus du pipeline

### 2.5 Déduplication (fingerprint SHA256)

Un même article peut être collecté plusieurs fois (répétition dans un flux RSS, recoupement entre sources). La déduplication évite de surcharger la base et de fausser les statistiques. Nous calculons une empreinte unique à partir du titre et du contenu :

- Calcul : `SHA256(title|content)` en minuscules
- Si le fingerprint existe déjà en base → l’article est **ignoré** (doublon)
- Garantie : un seul article par contenu identique

### 2.6 Score de qualité (`quality_score`)

- **0.3** : Données synthétiques ZZDB (identification)
- **0.5** : Sources réelles (défaut)

---

## 3. Scripts exécutables

### 3.1 Utiliser `ContentTransformer` directement

```python
# Nettoyage d'un article via ContentTransformer
from src.e1.core import Article, ContentTransformer

article = Article(
    title="  <b>Exemple</b>  ",
    content="<p>Texte   avec   HTML</p><script>alert(1)</script>",
    url="https://example.com",
)
article = ContentTransformer.transform(article)
print(article.title)   # Exemple
print(article.content) # Texte avec HTML
```

### 3.2 Sanitization manuelle (sans Article)

```python
# Nettoyage de chaînes brutes
from src.e1.core import sanitize_text, sanitize_url

text = "  Texte\u0000avec BOM\ufeff  "
clean = sanitize_text(text)
print(repr(clean))  # 'Texteavec BOM'

url = "https://example.com/page"
clean_url = sanitize_url(url)
```

### 3.3 Nettoyage minimal avec pandas (DataFrame)

```python
# Nettoyage d'un DataFrame exporté (exports/raw.csv, silver.csv, etc.)
import pandas as pd

def minimal_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    df["title"] = df["title"].fillna("").str.strip()
    df["content"] = df["content"].fillna("").str.strip()
    df = df[(df["title"].str.len() > 3) & (df["content"].str.len() > 10)]
    df["collected_at"] = pd.to_datetime(df["collected_at"], errors="coerce")
    return df

# Utilisation
df = pd.read_csv("exports/raw.csv")
df = minimal_cleaning(df)
print(f"Lignes valides: {len(df)}")
```

### 3.4 Vérifier la déduplication (SQLite)

```python
# Statistiques de déduplication par source
import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
conn = sqlite3.connect(DB_PATH)

query = """
SELECT s.name,
       COUNT(*) AS total,
       COUNT(DISTINCT r.fingerprint) AS uniques,
       COUNT(*) - COUNT(DISTINCT r.fingerprint) AS duplicates
FROM raw_data r
JOIN source s ON s.source_id = r.source_id
GROUP BY s.name
ORDER BY total DESC
"""
for row in conn.execute(query).fetchall():
    print(f"{row[0]}: {row[1]} total, {row[2]} uniques, {row[3]} doublons évités")
conn.close()
```

### 3.5 Agrégation RAW (données nettoyées depuis la DB)

Le module `DataAggregator` lit directement depuis la base SQLite et agrège les données brutes déjà nettoyées et dédupliquées. C'est utile pour produire des exports (raw.csv) ou alimenter des analyses sans repasser par le pipeline complet.

```python
# Lire les données RAW agrégées (déjà nettoyées en DB)
import os
from pathlib import Path
from src.e1.aggregator import DataAggregator

DB_PATH = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
agg = DataAggregator(DB_PATH)
df_raw = agg.aggregate_raw()
agg.close()
print(df_raw.head())
# Colonnes: id, source, title, content, url, fingerprint, collected_at, quality_score
```

---

## 4. Ordre des opérations dans le pipeline E1

1. **Extract** : Articles bruts depuis RSS, API, scraping, CSV…
2. **Clean** : `ContentTransformer.transform(article)` + `article.is_valid()`
3. **Load** : `load_article_with_id()` → fingerprint, déduplication, quality_score, INSERT
4. **Tag** : Topics (si chargé)
5. **Analyze** : Sentiment (si chargé)

---

## 5. Résumé

| Composant | Rôle |
|-----------|------|
| `sanitize_text` | Nettoyage caractères problématiques |
| `ContentTransformer.clean_html` | Extraction texte depuis HTML |
| `ContentTransformer.normalize` | Espaces multiples → 1 espace |
| `Article.is_valid` | Filtrage articles trop courts |
| `Article.fingerprint` | Clé de déduplication SHA256 |
| `load_article_with_id` | Insertion + déduplication + quality_score |

**Fichiers source** : `src/e1/core.py`, `src/e1/repository.py`, `src/e1/aggregator.py`

**Versioning & documentation** : Voir `docs/Dossier_E1_versioning_documentation.md` (Git, tags, CHANGELOG, docs/).

---

## 6. Règles formelles et Data Quality Gate

Un document est **rejeté** si :
- texte vide (titre < 4 caractères ou contenu < 11 caractères après trim)
- date invalide (non bloquant : `published_at` peut être NULL)
- doublon détecté (fingerprint déjà présent en base)

Les mécanismes appliqués : **Normalisation UTF-8** (NFC, BOM, null bytes), **Suppression HTML** (BeautifulSoup), **Hash SHA256** (fingerprint pour déduplication).

**Ces règles constituent un premier niveau de Data Quality Gate avant tout traitement IA.**

→ Voir `docs/Dossier_E1_preuves.md` pour les exemples réels et requêtes SQL démontrées.
