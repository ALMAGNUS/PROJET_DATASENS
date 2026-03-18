# 🏗️ ARCHITECTURE — DataSens E1

## 📋 Table des Matières
1. [Structure du Projet](#structure-du-projet)
2. [Modules Principaux](#modules-principaux)
3. [Dépendances](#dépendances)
4. [Flow de Données](#flow-de-données)
5. [Principes SOLID](#principes-solid)
6. [Exemples Pratiques](#exemples-pratiques)

---

## 📁 Structure du Projet

```
PROJET_DATASENS/ (racine)
│
├── README.md ........................... Guide utilisateur principal
├── main.py (20 lignes) ................. Entrée application
├── requirements.txt .................... Dépendances pip
├── pyrightconfig.json .................. Config Pyright/Pylance
├── sources_config.json ................. Config sources d'extraction
│
├── src/ ................................ Code source Python
│   ├── __init__.py ..................... Initialisation package
│   ├── models.py (45 lignes) ........... Dataclasses (Article, Source)
│   ├── extractors.py (280 lignes) ..... 8 extractors + Factory
│   └── core.py (150 lignes) ........... Pipeline + DB + Transformer
│
├── data/ ............................... Données (créé à runtime)
│   ├── raw/ ............................ Données brutes JSON/CSV
│   ├── silver/ ......................... Données nettoyées
│   └── gold/ ........................... Données agrégées
│
├── notebooks/ .......................... Jupyter notebooks
│   ├── datasens_E1/ ................... Phase 1 (extraction)
│   └── datasens_E1_v1/ ............... Version unifiée
│
├── visualizations/ .................... Outputs graphiques
│
└── docs/ .............................. Documentation (ce dossier)
    ├── ARCHITECTURE.md ............... (ce fichier)
    ├── ARCHITECTURE_DB.md ............ Architecture bases de données (ZZDB, DataSens, PySpark)
    ├── CHANGELOG.md .................. Historique versions
    ├── CONTRIBUTING.md .............. Guide contributeurs
    ├── LOGGING.md ................... Configuration logging
    ├── SCHEMA_DESIGN.md ............ Design base données
    └── AGILE_ROADMAP.md ........... Roadmap produit
```

---

## 🔧 Modules Principaux

### 1️⃣ **src/models.py** (45 lignes)
**Responsabilité :** Définir les structures de données

#### Classe `Article`
```python
@dataclass
class Article:
    title: str                  # Titre article
    content: str               # Contenu complet
    url: Optional[str]         # Lien source
    source_name: Optional[str] # Nom source origine
    published_at: Optional[str]# Date publication
```

**Méthodes :**
| Méthode | Paramètres | Retour | Usage |
|---------|-----------|--------|-------|
| `fingerprint()` | - | `str` (SHA256) | Deduplication articles |
| `is_valid()` | - | `bool` | Valide contenu minimal |
| `truncate()` | title_len, content_len | `Article` | Limite taille |

**Exemple :**
```python
article = Article(title="Titre", content="Contenu...")
if article.is_valid():
    fingerprint = article.fingerprint()  # SHA256
    article.truncate(title_len=500)
```

#### Classe `Source`
```python
@dataclass
class Source:
    source_name: str           # Nom unique source
    description: str           # Description
    acquisition_type: str      # Type: 'rss', 'api', 'scraping', 'bigdata', 'dataset'
    theme: str                 # Thème: 'news', 'politique', 'économie'...
    url: str                   # URL source
    partition_path: str        # Chemin partitionnement données
    file_naming: str           # Convention nommage fichiers
    refresh_frequency: str     # Fréquence: '1h', '1d', '1w'
    active: bool               # Actif/Inactif
```

---

### 2️⃣ **src/extractors.py** (280 lignes)
**Responsabilité :** Extraire données de toutes les sources

#### Hiérarchie des Classes

```
BaseExtractor (classe abstraite)
│
├── RSSExtractor .................. Flux RSS/Atom (Reuters, BBC, etc.)
├── APIExtractor .................. APIs REST
│   ├── _extract_reddit() ......... Reddit r/france, r/actualites
│   ├── _extract_weather() ....... OpenWeather météo France
│   ├── _extract_trustpilot() .... Trustpilot reviews API
│   └── _extract_generic_api() ... APIs génériques JSON
│
├── ScrapingExtractor ............ Web Scraping BeautifulSoup
│   ├── _scrape_trustpilot() ..... Trustpilot (HTML)
│   ├── _scrape_ifop() ........... Sondages IFOP
│   ├── _scrape_monaviscitoyen() . Avis citoyens
│   └── _generic_scrape() ........ Sites génériques
│
├── GDELTFileExtractor .......... Dataset GDELT (événements monde)
│
├── KaggleExtractor ............ Datasets publics Kaggle
│
└── ExtractorFactory ........... Factory (crée extractors automatiquement)
```

#### Classe `BaseExtractor`
```python
class BaseExtractor(ABC):
    def __init__(self, source: Source):
        self.source = source
        self.max_articles = 50  # Max articles par source
    
    @abstractmethod
    def extract(self) -> List[Article]:
        """À implémenter dans chaque extractor"""
        pass
    
    def _safe_extract(self, func) -> List[Article]:
        """Wrapper sécurisé avec gestion d'erreurs"""
        # ✅ Try/except robuste
        # ✅ Validation articles
        # ✅ Logging erreurs
        # ✅ Retourne [] si échec
```

**Pattern utilisé :**
```
Source → ExtractorFactory.create() → Extractor.extract() → List[Article]
```

#### Exemple : RSSExtractor
```python
class RSSExtractor(BaseExtractor):
    def extract(self) -> List[Article]:
        # Appel sécurisé
        return self._safe_extract(self._extract_rss)
    
    def _extract_rss(self) -> List[Article]:
        feed = feedparser.parse(self.source.url)  # Récup flux
        articles = []
        for entry in feed.entries[:self.max_articles]:
            articles.append(Article(
                title=entry.get('title'),
                content=entry.get('summary'),
                url=entry.get('link'),
                source_name=self.source.source_name,
                published_at=entry.get('published')
            ))
        return articles
```

#### Exemple : APIExtractor (Reddit)
```python
def _extract_reddit(self) -> List[Article]:
    articles = []
    for subreddit in ['france', 'actualites']:
        # Fetch Reddit JSON API
        resp = requests.get(f'https://reddit.com/r/{subreddit}/top.json?t=week')
        for post in resp.json()['data']['children']:
            if post['data']['score'] > 5:  # Filtre qualité
                articles.append(Article(
                    title=f"[{subreddit}] {post['data']['title']}",
                    content=post['data']['selftext'],
                    url=f"https://reddit.com{post['data']['permalink']}",
                    source_name=self.source.source_name
                ))
    return articles
```

#### ExtractorFactory Pattern
```python
class ExtractorFactory:
    _EXTRACTORS = {
        'rss': RSSExtractor,
        'api': APIExtractor,
        'scraping': ScrapingExtractor,
        'bigdata': GDELTFileExtractor,
        'dataset': KaggleExtractor,
    }
    
    @classmethod
    def create(cls, source: Source) -> BaseExtractor:
        # Crée extractor basé sur type source
        extractor_class = cls._EXTRACTORS.get(
            source.acquisition_type.lower(), 
            RSSExtractor  # Défaut
        )
        return extractor_class(source)
```

**Avantage :** Ajouter nouvelle source = créer classe + la mapper dans Factory (Open/Closed Principle)

---

### 2.5️⃣ **src/ingestion.py** (122 lignes)
**Responsabilité :** Télécharger et partitionner les datasets externes (Kaggle, GDELT)

#### Classe `SourceSpec`
```python
@dataclass(frozen=True)
class SourceSpec:
    source_name: str              # Nom identifiant (ex: Kaggle_StopWords_28Lang)
    kaggle_slug: str | None = None    # Slug Kaggle (ex: heeraldedhia/stop-words-in-28-languages)
    gdelt_key: str | None = None      # Clé GDELT (ex: gdelt_last15_english)
```

#### Classe `PartitionedIngester`
**Usage :** Télécharger et organiser données en répertoires partitionnés par date

| Méthode | Input | Output | Usage |
|---------|-------|--------|-------|
| `ingest()` | `SourceSpec` | `Path` (dir partitionné) | Télécharge + dézippe + manifeste |
| `_download()` | URL, chemin | `Path` fichier | Télécharge fichier HTTP |
| `_download_with_retry()` | URL, chemin | `Path` fichier | Télécharge avec retry (WinError 32) |
| `_unzip_and_copy()` | Source ZIP/dir | Fichiers extraits | Dézippe récursivement |
| `partition_dir()` | source_name, date | `Path` | Retourne `data/raw/{name}/date={YYYY-MM-DD}` |

**Structure créée :**
```
data/raw/
├── Kaggle_StopWords_28Lang/
│   └── date=2025-12-17/
│       └── [extracted files]
│       └── Kaggle_StopWords_28Lang_manifest_20251217_120000.json
├── Kaggle_FrenchFinNews/
│   └── date=2025-12-17/
├── GDELT_Last15_English/
│   └── date=2025-12-17/
└── sources_2025-12-17/
    └── raw_articles.json
```

**Exemple :**
```python
ingester = PartitionedIngester(str(Path.home() / 'datasens_project'))
specs = [
    SourceSpec(source_name='Kaggle_StopWords_28Lang', 
               kaggle_slug='heeraldedhia/stop-words-in-28-languages'),
    SourceSpec(source_name='GDELT_Last15_English',
               gdelt_key='gdelt_last15_english'),
]
for spec in specs:
    result_dir = ingester.ingest(spec)  # Télécharge + organise
```

---

### 3️⃣ **src/core.py** (150 lignes)
**Responsabilité :** Pipeline ETL + Database + Transformations

#### Classe `ContentTransformer`
**Usage :** Nettoie et normalise contenu article

| Méthode | Input | Output | Usage |
|---------|-------|--------|-------|
| `clean_html()` | HTML string | Texte brut | Enlève `<tags>` |
| `normalize_whitespace()` | Texte | Texte normalisé | Enlève espaces multiples |
| `transform()` | `Article` | `Article` modifié | Applique tous nettoyages |

```python
class ContentTransformer:
    @staticmethod
    def clean_html(text: str) -> str:
        """<p>Texte</p> → Texte"""
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text(separator=' ').strip()
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Texte   multi-espaces → Texte multi-espaces"""
        return re.sub(r'\s+', ' ', text).strip()
    
    @staticmethod
    def transform(article: Article) -> Article:
        article.content = ContentTransformer.clean_html(article.content)
        article.content = ContentTransformer.normalize_whitespace(article.content)
        return article
```

#### Classe `DatabaseLoader`
**Usage :** CRUD SQLite (Create, Read, Update, Delete)

| Méthode | Paramètres | Retour | Usage |
|---------|-----------|--------|-------|
| `__init__()` | db_path | - | Connexion SQLite |
| `get_source_id()` | source_name | `Optional[int]` | Récup ID source |
| `load_article()` | article, source_id | `bool` | Insert + dedup |
| `get_stats()` | - | `Dict[str, int]` | Stats par source |
| `log_sync()` | source_id, rows, status | `bool` | Log synchro |
| `close()` | - | - | Ferme connexion |

```python
class DatabaseLoader:
    def load_article(self, article: Article, source_id: int) -> bool:
        """Insert article avec deduplication SHA256"""
        fingerprint = article.fingerprint()
        
        # Check si article existe déjà
        if self._article_exists(fingerprint):
            return False  # Déjà existant
        
        # Insert
        self.cursor.execute("""
            INSERT INTO raw_data (source_id, title, content, url, fingerprint, ...)
            VALUES (?, ?, ?, ?, ?, ...)
        """, (...))
        self.conn.commit()
        return True
```

#### Classe `E1Pipeline`
**Usage :** Orchestration ETL complète (Extraction → Cleaning → Loading)

```python
class E1Pipeline:
    def __init__(self, db_path: str, config_path: str):
        self.db = DatabaseLoader(db_path)
        self.config_path = Path(config_path)
        self.stats = {'extracted': 0, 'cleaned': 0, 'loaded': 0, 'deduplicated': 0}
    
    def run(self):
        """Lance pipeline complet"""
        articles = self.extract()      # ✅ Récup données
        articles = self.clean(articles)  # 🧹 Nettoie
        self.load(articles)             # 💾 Insert DB
        self.show_stats()               # 📊 Statistiques
```

**Phase 1 : Extract**
```python
def extract(self) -> List[Tuple[Article, str]]:
    articles = []
    for source in self.load_sources():
        extractor = ExtractorFactory.create(source)
        extracted = extractor.extract()
        articles.extend([(a, source.source_name) for a in extracted])
        self.stats['extracted'] += len(extracted)
    return articles
```

**Phase 2 : Clean**
```python
def clean(self, articles) -> List[Tuple[Article, str]]:
    cleaned = []
    for article, source_name in articles:
        article = ContentTransformer.transform(article)
        if article.is_valid():  # Vérifie min contenu
            cleaned.append((article, source_name))
            self.stats['cleaned'] += 1
    return cleaned
```

**Phase 3 : Load**
```python
def load(self, articles):
    for article, source_name in articles:
        source_id = self.db.get_source_id(source_name)
        if self.db.load_article(article, source_id):
            self.stats['loaded'] += 1
        else:
            self.stats['deduplicated'] += 1
```

---

## 📦 Dépendances

### `requirements.txt`

```
feedparser==6.1.1          # Parse RSS/Atom feeds
requests==2.31.0           # HTTP requests (APIs, scraping)
beautifulsoup4==4.12.0     # HTML parsing
lxml==4.9.3                # XML/HTML parser (optionnel)
```

**Utilisation :**

| Package | Usage | Exemple |
|---------|-------|---------|
| `feedparser` | Parser flux RSS | `feedparser.parse('https://...')` |
| `requests` | HTTP client | `requests.get('https://api.../data')` |
| `beautifulsoup4` | HTML/XML parsing | `BeautifulSoup(html, 'html.parser')` |

### Built-in (inclus Python 3.13)

```python
sqlite3         # Database client
json            # JSON parsing
csv             # CSV reading/writing
re              # Regex
logging         # Logging
pathlib         # Path management
dataclasses     # @dataclass decorator
datetime        # Date/time operations
```

---

## 🔄 Flow de Données

```
┌─────────────────────────────────────────────────────────────┐
│                   sources_config.json                       │
│  [{"source_name": "Reuters", "url": "...", ...}, ...]      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            E1Pipeline.load_sources()                         │
│       Returns: List[Source] dataclasses                      │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │ Pour chaque Source      │
        ▼                         │
┌─────────────────────────────┐  │
│ ExtractorFactory.create()   │  │
│ → Sélectionne Extractor    │  │
│   basé sur type (rss, api) │  │
└──────────────┬──────────────┘  │
               │                  │
        ┌──────▼──────────┐       │
        │ RSSExtractor    │ ◄─┘   │
        │ APIExtractor    │
        │ Scraping...     │
        │ _safe_extract() │
        └──────┬──────────┘
               │
               ▼
        List[Article]  ← ✅ EXTRACTED
        
        ┌──────────────────────────┐
        │ ContentTransformer.      │
        │ transform(article)       │
        │ - clean_html()           │
        │ - normalize_whitespace() │
        └──────┬───────────────────┘
               │
               ▼
        List[Article]  ← 🧹 CLEANED
        
        ┌──────────────────────────┐
        │ DatabaseLoader.          │
        │ load_article()           │
        │ - fingerprint (SHA256)   │
        │ - deduplication check    │
        │ - INSERT raw_data        │
        │ - Log sync               │
        └──────┬───────────────────┘
               │
               ▼
        SQLite DB  ← 💾 LOADED
        
        ┌──────────────────────────┐
        │ Pipeline.show_stats()    │
        │ Affiche rapports         │
        └──────────────────────────┘
```

---

## ✨ Principes SOLID

### 1. **S - Single Responsibility Principle**
Chaque classe = 1 seule responsabilité

| Classe | Responsabilité |
|--------|----------------|
| `Article` | Représenter un article |
| `Source` | Config source d'extraction |
| `RSSExtractor` | Extraire depuis RSS |
| `APIExtractor` | Extraire depuis API |
| `ContentTransformer` | Nettoyer contenu |
| `DatabaseLoader` | Opérations BD |
| `E1Pipeline` | Orchestrer ETL |

✅ **Avant :** APIExtractor faisait Reddit + Weather + INSEE + Trustpilot
❌ **Après :** Chacun a sa méthode dédiée

### 2. **O - Open/Closed Principle**
Ouvert à l'extension, fermé à la modification

```python
# ✅ AVANT : Ajouter source = modifier create_extractor()
def create_extractor(source):
    if source.type == 'rss':
        return RSSExtractor()
    elif source.type == 'api':
        return APIExtractor()
    elif source.type == 'scraping':
        return ScrapingExtractor()
    # ❌ Chaque nouvelle source = modifier cette fonction

# ✅ APRÈS : Factory Pattern
class ExtractorFactory:
    _EXTRACTORS = {
        'rss': RSSExtractor,
        'api': APIExtractor,
        'scraping': ScrapingExtractor,
        'bigdata': GDELTFileExtractor,
        'dataset': KaggleExtractor,
    }
    
    # ✅ Ajouter nouveau = enregistrer dans dict (0 modification existant)
```

### 3. **L - Liskov Substitution Principle**
Tous les Extractors interchangeables

```python
extractor: BaseExtractor = ExtractorFactory.create(source)
articles = extractor.extract()  # Fonctionne pour tous les types
```

### 4. **I - Interface Segregation Principle**
Interface minimale et pertinente

```python
class BaseExtractor(ABC):
    @abstractmethod
    def extract(self) -> List[Article]:
        """Interface minimale"""
        pass
    
    # Methodes utilitaires
    def _safe_extract(self, func):
        """Pour tous les extractors"""
```

### 5. **D - Dependency Inversion Principle**
Dépendre d'abstractions, pas d'implémentations

```python
# ❌ Mauvais : Couplage dur
extractor = RSSExtractor(source)

# ✅ Bon : Dépend d'abstraction + Factory
extractor: BaseExtractor = ExtractorFactory.create(source)
```

---

## 💻 Exemples Pratiques

### Lancer le Pipeline

```bash
python main.py
```

Affiche :
```
======================================================================
🚀 DataSens E1 - COMPLETE PIPELINE
======================================================================

======================================================================
📥 EXTRACTION PHASE
======================================================================

📰 Reuters... (rss) ✅ 45
📰 Reddit... (api) ✅ 52
📰 Trustpilot... (scraping) ✅ 38
📰 GDELT... (bigdata) ✅ 100
📰 Kaggle... (dataset) ✅ 50

✅ Total extracted: 285

======================================================================
🧹 CLEANING PHASE
======================================================================
✅ Total cleaned: 271

======================================================================
💾 LOADING PHASE
======================================================================
✅ Total loaded: 245
⚠️  Deduplicated: 26

======================================================================
📊 STATISTICS
======================================================================
   Extracted:    285
   Cleaned:      271
   Loaded:       245
   Deduplicated: 26

   Database total records: 12450

   By source:
      • Reuters: 3200
      • Reddit: 2850
      • Trustpilot: 2145
      • GDELT: 2100
      • Kaggle: 2155
======================================================================
```

### Ajouter une Nouvelle Source

**1. Créer Extractor dans `src/extractors.py`**

```python
class MySourceExtractor(BaseExtractor):
    def extract(self) -> List[Article]:
        return self._safe_extract(self._extract_mysource)
    
    def _extract_mysource(self) -> List[Article]:
        articles = []
        # Ton code
        return articles
```

**2. Enregistrer dans Factory**

```python
class ExtractorFactory:
    _EXTRACTORS = {
        # ...
        'mysource': MySourceExtractor,  # ← Ajouter ici
    }
```

**3. Ajouter dans `sources_config.json`**

```json
{
  "source_name": "MySource",
  "acquisition_type": "mysource",
  "url": "https://...",
  "theme": "news",
  "active": true
}
```

**4. Lancer**

```bash
python main.py
```

✅ MySource est automatiquement utilisée !

---

## 📊 Métriques Code

| Métrique | Valeur |
|----------|--------|
| Lignes totales | ~495 |
| Modules | 3 (models, extractors, core) |
| Classes | 8 extractors + 3 utilitaires |
| Type coverage | 100% |
| Docstrings | 85% |
| Tests | À ajouter |

---

## 🔗 Liens Utiles

- [Base de données](#docs/SCHEMA_DESIGN.md)
- [Changelog](#docs/CHANGELOG.md)
- [Guide contributeurs](#docs/CONTRIBUTING.md)
- [Configuration logging](#docs/LOGGING.md)
- [Roadmap produit](#docs/AGILE_ROADMAP.md)
