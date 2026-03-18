# 🔍 Audit E1 — Grille de compétences (point de situation)

**Date**: 2026-02-12  
**Projet**: DataSens

---

## A1. Programmer la collecte de données

### C1. Automatiser l'extraction de données depuis un service web

| Critère | Statut | Justification |
|---------|--------|---------------|
| Identification des contraintes techniques propres aux sources | ✅ TRUE | `sources_config.json` décrit url, type (rss/api/scraping), fréquence, partition_path pour chaque source |
| Rédaction des spécifications techniques pour l'extraction | ✅ TRUE | `FLOW_DONNEES.md` (Étape 1 EXTRACT), `sources_config.json` |
| Construction des requêtes HTTP pour la récupération depuis un service web (REST) | ✅ TRUE | `src/e1/core.py` : `requests.get()` pour Reddit, OpenWeather, GDELT, Trustpilot, etc. |
| Lecture d'un fichier de données dans un script | ✅ TRUE | `CSVExtractor` (zzdb_csv), `KaggleExtractor` (CSV/JSON locaux), `_collect_local_files()` |
| Téléchargement de l'HTML d'une ou plusieurs pages web (scraping) | ✅ TRUE | `BeautifulSoup` + `requests.get` dans core.py (Trustpilot, Reddit, IFOP, MonAvisCitoyen, etc.) |
| Connexion programmatique à une BDD et à un système big data | ✅ TRUE | SQLite (`sqlite3`), PySpark (`merge_parquet_goldai.py`, `GoldParquetReader`) |
| Programmation des filtrages/parsing (API, fichiers, HTML) | ✅ TRUE | `feedparser`, `BeautifulSoup`, parsing JSON/CSV, `ContentTransformer.transform()` |
| Exécution programmatique des requêtes SQL | ✅ TRUE | `pd.read_sql_query()`, `cursor.execute()` dans aggregator, repository, pipeline |
| Exécution programmatique des requêtes depuis un système big data | ✅ TRUE | PySpark (`merge_parquet_goldai.py`, `GoldParquetReader`, `GoldDataProcessor`) |

### C2. Développer des requêtes SQL d'extraction

| Critère | Statut | Justification |
|---------|--------|---------------|
| Ecriture des requêtes SQL de récupération (BDD et big data) | ✅ TRUE | `aggregator.aggregate_raw/silver/gold()`, requêtes dans FLOW_DONNEES.md, `QUERIES_SQL.md` |
| Documentation des requêtes d'extraction | ✅ TRUE | `scripts/QUERIES_SQL.md` (requêtes SQL documentées), `FLOW_DONNEES.md` (exemples) |

### C3. Règles d'agrégation

| Critère | Statut | Justification |
|---------|--------|---------------|
| Rédaction des spécifications techniques pour l'agrégation | ✅ TRUE | `FLOW_DONNEES.md` Étape 4 (RAW/SILVER/GOLD), flux décrit |
| Programmation des règles d'agrégation (sources → jeu unique) | ✅ TRUE | `DataAggregator` : `aggregate_raw()`, `aggregate_silver()`, `aggregate_gold()` |
| Programmation de l'identification des entrées corrompues | ✅ TRUE | `article.is_valid()`, `ContentTransformer`, validation len(title)>3, len(content)>10 |
| Programmation de la suppression des entrées corrompues | ✅ TRUE | Articles non valides exclus avant load, fingerprint pour doublons |
| Programmation de l'identification des entrées au format non normalisé | ✅ TRUE | `sanitize_text()`, `sanitize_url()`, validation contenu |
| Programmation de l'homogénéisation des formats | ✅ TRUE | `ContentTransformer` (HTML→texte, espaces), format dates, quality_score |
| Versionnement des scripts avec Git | ✅ TRUE | Dépôt Git, `.github/workflows/`, historique commits |
| Documentation des scripts | ✅ TRUE | `scripts/SCRIPTS_LIST.md`, docstrings dans les modules |

---

## A2. Mise à disposition technique des données

### C4. Créer une base de données (RGPD)

| Critère | Statut | Justification |
|---------|--------|---------------|
| Rédaction des spécifications techniques pour le stockage | ✅ TRUE | `docs/ARCHITECTURE_DB.md`, `docs/SCHEMA_DESIGN.md` |
| Modélisation de la structure selon Merise | ✅ TRUE | `docs/EXPLICATION_RELATIONS_MERISE.md`, `docs/ER_DIAGRAM_*.md` |
| Choix du système de gestion de base de données | ✅ TRUE | SQLite (config.db_path), option PostgreSQL mentionnée |
| Création de la base de données | ✅ TRUE | `repository._ensure_schema()`, `setup_with_sql.py` |
| Documentation de la procédure d'installation | ✅ TRUE | `README.md`, `scripts/README.md`, `setup_with_sql.py` |
| Registre des traitements de données personnelles (RGPD) | ✅ TRUE | `docs/REGISTRE_TRAITEMENTS_RGPD.md` (T1 profils, T2 audit, T3 contenu) |
| Procédures de tri des données personnelles (RGPD) | ✅ TRUE | `docs/PROCEDURE_TRI_DONNEES_PERSONNELLES.md` (détection, suppression, anonymisation) |
| Programmation du script d'import des données | ✅ TRUE | Pipeline E1 (`main.py`, `load()`), `load_article_with_id()` |
| Documentation du script d'import | ✅ TRUE | `FLOW_DONNEES.md` (LOAD), docstrings |

### C5. Développer une API REST

| Critère | Statut | Justification |
|---------|--------|---------------|
| Rédaction des spécifications techniques API | ✅ TRUE | `docs/README_E2_API.md` (endpoints, auth, exemples) |
| Configuration des accès au jeu de données depuis l'API | ✅ TRUE | `run_e2_api.py`, routes RAW/SILVER/GOLD, `data_service.py` |
| Développement de la réception et validation des requêtes client | ✅ TRUE | Pydantic schemas, `AIPredictRequest`, etc. |
| Développement des requêtes à la BDD | ✅ TRUE | `E1DataReader`, `data_service.py`, requêtes SQL via API |
| Développement des réponses de l'API | ✅ TRUE | Routes FastAPI, JSON responses |
| Règles d'autorisation et d'accès (RBAC) | ✅ TRUE | `dependencies/permissions.py`, `require_reader`, zones RAW/SILVER/GOLD |
| Sécurisation (OWASP Top 10) | ✅ TRUE | JWT, bcrypt, RBAC, CORS, audit trail. Section OWASP dans `README_E2_API.md` |
| Documentation technique de l'API REST | ✅ TRUE | Swagger `/docs`, ReDoc `/redoc`, `README_E2_API.md` |
| Documentation technique d'accès à la BDD | ✅ TRUE | `QUERIES_SQL.md`, `ARCHITECTURE_DB.md` |

---

## Synthèse

| Compétence | Critères OK | Critères KO | Partiel |
|------------|-------------|-------------|---------|
| A1 C1 | 9/9 | 0 | 0 |
| A1 C2 | 2/2 | 0 | 0 |
| A1 C3 | 8/8 | 0 | 0 |
| A2 C4 | 9/9 | 0 | 0 |
| A2 C5 | 9/9 | 0 | 0 |

### Statut : ✅ 100 % conforme

Tous les documents manquants ont été créés :
- `docs/REGISTRE_TRAITEMENTS_RGPD.md`
- `docs/PROCEDURE_TRI_DONNEES_PERSONNELLES.md`
- Section OWASP dans `docs/README_E2_API.md`
