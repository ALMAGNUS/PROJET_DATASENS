# 📋 Dossier E1 — Mode preuve

**Contexte** : Ce document fournit des preuves concrètes du fonctionnement du pipeline E1 : exemples réels d'ingestion pour **toutes les sources** (RSS, API, scraping, Kaggle, GDELT, CSV/ZZDB), requêtes SQL démontrées, et règles de nettoyage formelles. Chaque section prouve un aspect technique du système.

---

## 1. Vue d'ensemble des sources

| Type | Extracteur | Sources actives |
|------|------------|-----------------|
| **RSS** | `RSSExtractor` | rss_french_news, google_news_rss, yahoo_finance |
| **API** | `APIExtractor` | reddit_france, openweather_api |
| **API/Scraping** | `APIExtractor` / `ScrapingExtractor` | agora_consultations |
| **Scraping** | `ScrapingExtractor` | trustpilot_reviews, ifop_barometers, monavis_citoyen |
| **Dataset** | `KaggleExtractor` | kaggle_french_opinions, datagouv_datasets |
| **BigData** | `GDELTFileExtractor` | gdelt_events, GDELT_Last15_English, GDELT_Master_List |
| **CSV** | `CSVExtractor` | zzdb_csv |

---

## 2. Exemples réels par source

### ✔ RSS (rss_french_news, google_news_rss, yahoo_finance)

**Capture JSON brut** (format feedparser) :
```json
{"title": "Titre", "summary": "<p>Résumé HTML</p>", "link": "https://...", "published": "Mon, 13 Jan 2025 12:00:00 +0000"}
```

**Lignes insérées** : Jusqu'à 50 entrées/flux. Déduplication par fingerprint.
**Trace SYNC_LOG** : `SELECT sl.sync_log_id, s.name, sl.rows_synced, sl.status FROM sync_log sl JOIN source s ON s.source_id = sl.source_id WHERE s.name IN ('rss_french_news','google_news_rss','yahoo_finance');`

---

### ✔ API (reddit_france, openweather_api)

**Reddit** : API JSON `reddit.com/r/france/top.json` → posts avec score > 5.
**OpenWeather** : API météo par ville (Paris, Lyon, Marseille…) → bulletins comme articles.
**Lignes** : ~15-25 par subreddit, ~5 par run météo.

---

### ✔ Scraping (trustpilot_reviews, ifop_barometers, monavis_citoyen)

**Trustpilot** : Avis clients via BeautifulSoup.
**IFOP** : Baromètres politiques depuis ifop.com.
**MonAvisCitoyen** : Avis citoyens depuis monaviscitoyen.fr.
**Lignes** : Variable selon pages accessibles.

---

### ✔ Kaggle / Dataset (kaggle_french_opinions, datagouv_datasets)

**Dossier** : `data/raw/kaggle_french_opinions/` (Comments.csv, FrenchNews.csv, french_tweets.csv…)
**Manifest** : `data/raw/sources_YYYY-MM-DD/raw_articles.json`
**Import** : ~76 680 articles Kaggle. `KaggleExtractor` lit `rglob('*.csv')` et `*.json`.

---

### ✔ GDELT / BigData (gdelt_events, GDELT_Last15_English, GDELT_Master_List)

**Paramètres** : `GDELT_LIMIT` (env), source `lastupdate.txt` → URLs GKG/Events.
**Parsing** : CSV tab → colonnes 0 (code), 1 (titre), 2 (date), 57 (URL).
**Exemple** : `{"title": "FRANCE: ...", "content": "Code: 123, Date: 20250113", "url": "https://..."}`

---

### ✔ CSV / ZZDB (zzdb_csv)

**Fichier** : `zzdb/zzdb_dataset.csv` ou `data/raw/zzdb_csv/zzdb_dataset.csv`
**Import** : Données synthétiques Faker, intégration unique (fondation).
**Qualité** : `quality_score = 0.3` pour identification synthétique.

---

### Connecteurs en autonomie

**Le connecteur fonctionne en autonomie et écrit dans la table `raw_data` ainsi que dans le système de logs `sync_log`.**

Chaque extracteur écrit dans `raw_data` et `sync_log`. Requête pour **toutes les sources** :

```sql
SELECT s.name, s.source_type, sl.rows_synced, sl.status, sl.sync_date
FROM sync_log sl
JOIN source s ON s.source_id = sl.source_id
ORDER BY sl.sync_date DESC
LIMIT 20;
```

---

## 3. C2 – SQL (requêtes démontrées)

### 1. Volume par source

```sql
SELECT source_id, COUNT(*) AS nb_articles
FROM raw_data
GROUP BY source_id;
```

**Ce que ça prouve** : Le volume d'articles par source. Permet de vérifier que chaque connecteur alimente bien la base et d'identifier les sources les plus actives.

---

### 2. Déduplication

```sql
SELECT COUNT(*) - COUNT(DISTINCT fingerprint) AS doublons_evites
FROM raw_data
WHERE fingerprint IS NOT NULL;
```

**Ce que ça prouve** : Avec la contrainte UNIQUE sur fingerprint, le résultat est 0 (aucun doublon en base). Prouve que la déduplication SHA256 fonctionne. Les doublons sont rejetés à l'insertion (voir stats du pipeline).

*Note : `fingerprint` = hash SHA256(title|content), équivalent à un `content_hash`.*

---

### 3. Articles récents

```sql
SELECT title, collected_at
FROM raw_data
ORDER BY collected_at DESC
LIMIT 10;
```

**Ce que ça prouve** : Les derniers articles collectés, avec leur date d’ingestion. Confirme que le pipeline alimente régulièrement la base et que les timestamps sont cohérents.

*Note : `collected_at` = date d’insertion en base (équivalent à `created_date`).*

---

## 4. C3 – Nettoyage : règles formelles

### Règles de validation

**Un document est rejeté si :**
- texte vide (titre < 4 caractères ou contenu < 11 caractères après trim)
- date invalide (non bloquant : `published_at` peut être NULL)
- doublon détecté (fingerprint déjà présent en base)

### Mécanismes de nettoyage

| Mécanisme | Description |
|-----------|-------------|
| **Normalisation UTF-8** | NFC pour unifier les représentations Unicode ; suppression du BOM (`\ufeff`), des null bytes (`\x00`) et du caractère de remplacement (`\ufffd`). |
| **Suppression HTML** | Extraction du texte via BeautifulSoup (balises et scripts retirés). |
| **Hash SHA256** | `fingerprint = SHA256(title\|content)` en minuscules, utilisé comme clé de déduplication unique. |

### Phrase clé

**Ces règles constituent un premier niveau de Data Quality Gate avant tout traitement IA.**

Avant toute annotation (topics, sentiment) ou ingestion dans un dataset GoldAI, les documents passent par ce filtre. Seuls les articles valides et non dupliqués sont conservés, ce qui garantit la qualité des données alimentant les modèles.

---

## 5. Fichiers de référence

| Fichier | Rôle |
|---------|------|
| `preuves.ipynb` | Notebook exécutable — preuves pour toutes les sources |
| `src/e1/core.py` | Extracteurs, ContentTransformer, fingerprint |
| `src/e1/repository.py` | Schéma raw_data, sync_log, load_article_with_id |
| `sources_config.json` | Configuration de toutes les sources |
| `scripts/demo_proof_e1.py` | Script de démonstration des preuves |
| `docs/Dossier_E1_nettoyage+scripts.md` | Guide détaillé du nettoyage |
| `docs/Dossier_E1_C33_processus_agregation.md` | **C3.3** Processus automatisé d'agrégation |
| `docs/Dossier_E1_versioning_documentation.md` | Versioning (Git, tags, CHANGELOG) + documentation (docs/, pipeline, logging) |
