# C3.3 — Processus automatisé d'agrégation multi-sources

**Pour le jury** : Ce document présente le code qui implémente un processus automatisé pour l'agrégation des données provenant de différentes sources : extraction multi-sources, normalisation des colonnes, déduplication par fingerprint, enrichissement (topics + sentiment).

---

## Vue d'ensemble du flux

```
sources_config.json
       ↓
  load_sources()  →  extract()  →  clean()  →  load()
       ↓                  ↓            ↓           ↓
  Multi-sources    create_extractor  ContentTransformer  load_article_with_id
  (RSS, API,       par source        sanitize + HTML     fingerprint + INSERT
   Kaggle, ...)                      + normalize         + tagger.tag()
                                                        + analyzer.save()
       ↓
  DataAggregator.aggregate_raw() → aggregate_silver() → aggregate()
       ↓                  ↓                    ↓
  RAW (colonnes      SILVER (+ topics)    GOLD (+ sentiment)
   normalisées)
```

---

## 1. Extraction multi-sources

### 1.1 Chargement de la configuration (`src/e1/pipeline.py`)

```python
def load_sources(self, inject_csv_path: str | None = None, inject_source_name: str = "csv_inject") -> list:
    """Load sources from JSON config + source CSV injectée si --inject-csv"""
    config_path = Path(__file__).parent.parent.parent / "sources_config.json"
    sources = []
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            sources = [Source(**s) for s in config["sources"]]
    if inject_csv_path:
        p = Path(inject_csv_path)
        if p.exists():
            sources.insert(0, Source(source_name=inject_source_name, acquisition_type="csv", url=str(p.resolve())))
    return sources
```

### 1.2 Factory d'extracteurs (`src/e1/core.py`)

```python
def create_extractor(source: Source) -> BaseExtractor:
    """Factory - route source to correct extractor"""
    acq_type, src_low = source.acquisition_type.lower(), source.source_name.lower()
    if acq_type == "rss":
        return RSSExtractor(source.source_name, source.url)
    elif acq_type == "bigdata":
        return GDELTFileExtractor(source.source_name, source.url)
    elif acq_type == "mongodb":
        return MongoExtractor(source.source_name, source.url)
    elif acq_type == "csv" or "zzdb" in src_low:
        return CSVExtractor(source.source_name, source.url)
    elif acq_type == "dataset":
        return KaggleExtractor(source.source_name, source.url)
    elif acq_type in ["api", "api_scraping"]:
        if any(k in src_low for k in ["reddit", "weather", "meteo"]):
            return APIExtractor(source.source_name, source.url)
        elif any(k in src_low for k in ["insee", "citoyen", "opinion"]):
            return ScrapingExtractor(source.source_name, source.url)
        return APIExtractor(source.source_name, source.url)
    elif acq_type == "scraping":
        return ScrapingExtractor(source.source_name, source.url)
    return RSSExtractor(source.source_name, source.url)
```

### 1.3 Boucle d'extraction (`src/e1/pipeline.py`)

```python
def extract(self, inject_csv_path=None, inject_source_name="csv_inject"):
    sources = self.load_sources(inject_csv_path=inject_csv_path, inject_source_name=inject_source_name)
    articles = []
    for source in sources:
        if not source.active:
            continue
        extractor = create_extractor(source)
        extracted = extractor.extract()
        self.stats["extracted"] += len(extracted)
        articles.extend([(a, source.source_name) for a in extracted])
        if source_id:
            self.db.log_sync(source_id, len(extracted), "OK")
    return articles
```

---

## 2. Normalisation des colonnes

### 2.1 Sanitization et normalisation (`src/e1/core.py`)

```python
def sanitize_text(text: str | None) -> str:
    """Remove null bytes, control chars, BOM. Normalizes Unicode (NFC)."""
    if not text:
        return ""
    text = str(text)
    text = text.replace("\ufeff", "")   # BOM
    text = text.replace("\x00", "")     # null bytes
    text = "".join(c for c in text if ord(c) >= 32 or c in " \t\n\r")
    text = text.replace("\ufffd", "")   # Unicode replacement
    text = unicodedata.normalize("NFC", text)
    return text.strip()

class ContentTransformer:
    @staticmethod
    def clean_html(text: str) -> str:
        if not text or len(text.strip()) < 5:
            return text or ""
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(separator=" ").strip()

    @staticmethod
    def normalize(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def transform(article: Article) -> Article:
        article.title = sanitize_text(article.title)
        article.content = sanitize_text(article.content)
        article.content = ContentTransformer.clean_html(article.content)
        article.content = ContentTransformer.normalize(article.content)
        if article.url:
            article.url = sanitize_url(article.url)
        return article
```

### 2.2 Étape clean du pipeline

```python
def clean(self, articles: list) -> list:
    cleaned = []
    for article, source_name in articles:
        article = ContentTransformer.transform(article)
        if article.is_valid():
            cleaned.append((article, source_name))
            self.stats["cleaned"] += 1
    return cleaned
```

**Colonnes normalisées** : `title` (max 500), `content` (max 2000), `url` sanitized. Toutes les sources produisent des `Article` avec ce schéma.

---

## 3. Déduplication par fingerprint

### 3.1 Calcul du fingerprint (`src/e1/core.py`)

```python
@dataclass
class Article:
    title: str
    content: str
    url: str | None = None
    source_name: str | None = None
    published_at: str | None = None

    def fingerprint(self) -> str:
        return hashlib.sha256(f"{self.title}|{self.content}".lower().encode()).hexdigest()

    def is_valid(self) -> bool:
        return len(self.title.strip()) > 3 and len(self.content.strip()) > 10
```

### 3.2 Insertion avec déduplication (`src/e1/repository.py`)

```python
def load_article_with_id(self, article: Article, source_id: int) -> int | None:
    """Load article and return raw_data_id (or None if duplicate)"""
    fp = article.fingerprint()
    self.cursor.execute("SELECT raw_data_id FROM raw_data WHERE fingerprint = ?", (fp,))
    if self.cursor.fetchone():
        return None  # Doublon → ignoré

    quality_score = 0.3 if "zzdb" in (article.source_name or "").lower() else 0.5
    self.cursor.execute(
        """INSERT INTO raw_data (source_id, title, content, url, fingerprint, published_at, collected_at, quality_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (source_id, article.title, article.content, article.url, fp,
         article.published_at, datetime.now().isoformat(), quality_score),
    )
    self.conn.commit()
    # Retourne raw_data_id pour enrichissement
    self.cursor.execute("SELECT raw_data_id FROM raw_data WHERE fingerprint = ?", (fp,))
    return self.cursor.fetchone()[0]
```

---

## 4. Enrichissement topics + sentiment

### 4.1 Intégration dans le load (`src/e1/pipeline.py`)

```python
def load(self, articles: list):
    for article, source_name in articles:
        source_id = self.db.get_source_id(source_name)
        if source_id:
            raw_data_id = self.db.load_article_with_id(article, source_id)
            if raw_data_id:
                # Topics (max 2 par article)
                if self.tagger.tag(raw_data_id, article.title, article.content):
                    self.stats["tagged"] += 1
                # Sentiment (positif / neutre / négatif)
                if self.analyzer.save(raw_data_id, article.title, article.content):
                    self.stats["analyzed"] += 1
            else:
                self.stats["deduplicated"] += 1
```

### 4.2 Agrégation RAW → SILVER → GOLD (`src/e1/aggregator.py`)

**RAW** : colonnes `id`, `source`, `title`, `content`, `url`, `fingerprint`, `collected_at`, `quality_score`, `source_type`

```python
def aggregate_raw(self) -> pd.DataFrame:
    df_db = pd.read_sql_query(
        "SELECT r.raw_data_id as id, s.name as source, r.title, r.content, r.url, "
        "r.fingerprint, r.collected_at, r.quality_score FROM raw_data r "
        "JOIN source s ON r.source_id = s.source_id ORDER BY r.collected_at DESC",
        self.conn,
    )
    df_db["source_type"] = df_db["source"].apply(classify_source)  # real / flat_files / db_non_relational
    return df_db
```

**SILVER** : RAW + `topic_1`, `topic_1_score`, `topic_2`, `topic_2_score`

```python
def aggregate_silver(self) -> pd.DataFrame:
    df = self.aggregate_raw()
    topics = pd.read_sql_query(
        "SELECT dt.raw_data_id, t.name as topic_name, dt.confidence_score, "
        "ROW_NUMBER() OVER (PARTITION BY dt.raw_data_id ORDER BY dt.confidence_score DESC) as rn "
        "FROM document_topic dt JOIN topic t ON dt.topic_id = t.topic_id",
        self.conn,
    )
    # Pivot pour topic_1, topic_2
    df = df.merge(t1, ...).merge(t2, ...)
    return df
```

**GOLD** : SILVER + `sentiment`, `sentiment_score`

```python
def aggregate(self) -> pd.DataFrame:
    df = self.aggregate_silver()
    sentiment = pd.read_sql_query(
        "SELECT raw_data_id, label as sentiment, score as sentiment_score "
        "FROM model_output WHERE model_name = 'sentiment_keyword'",
        self.conn,
    )
    df = df.merge(sentiment, left_on="id", right_on="raw_data_id", how="left")
    df["sentiment"] = df["sentiment"].fillna("neutre")
    return df
```

---

## 5. Point d'entrée et orchestration

### 5.1 Commande de lancement (`main.py`)

```python
from e1.pipeline import E1Pipeline

pipeline = E1Pipeline(quiet=args.quiet)
pipeline.run(inject_csv_path=args.inject_csv, inject_source_name=args.source_name)
```

### 5.2 Run complet (`src/e1/pipeline.py`)

```python
def run(self, inject_csv_path=None, inject_source_name="csv_inject"):
    # ETAPE 1: Extract + Clean + Load (avec topics + sentiment)
    articles = self.extract(inject_csv_path=inject_csv_path, inject_source_name=inject_source_name)
    articles = self.clean(articles)
    self.load(articles)

    # ETAPE 2: Exports RAW / SILVER / GOLD
    aggregator = DataAggregator(db_path)
    df_raw = aggregator.aggregate_raw()
    df_silver = aggregator.aggregate_silver()
    df_gold = aggregator.aggregate()
    # Export CSV + Parquet
```

---

## 6. Résumé des principes C3.3

| Principe | Implémentation |
|----------|----------------|
| **Extraction multi-sources** | `load_sources()` + `create_extractor()` + boucle `extract()` pour chaque source active |
| **Normalisation colonnes** | `ContentTransformer.transform()` : sanitize_text, clean_html, normalize → schéma `Article` unique |
| **Déduplication fingerprint** | `Article.fingerprint()` = SHA256(title\|content) ; `load_article_with_id()` vérifie avant INSERT |
| **Enrichissement topics + sentiment** | `tagger.tag()` et `analyzer.save()` après chaque INSERT ; agrégation SILVER/GOLD via JOIN document_topic et model_output |

**Fichiers clés** : `src/e1/pipeline.py`, `src/e1/core.py`, `src/e1/repository.py`, `src/e1/aggregator.py`, `main.py`
