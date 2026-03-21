# Versionner et documenter le processus de nettoyage

**Contexte** : Ce document décrit comment le code source du processus de nettoyage est versionné (Git, tags, CHANGELOG) et documenté (docs/, architecture, pipeline, logging).

---

## 1. Versioning

### 1.1 Git + tags

Le dépôt utilise **Git** pour le versionnement. Les versions majeures sont marquées par des **tags** :

```bash
# Lister les tags existants
git tag -l

# Créer un tag pour une release (ex: nettoyage v1.4.1)
git tag -a v1.4.1 -m "Nettoyage: sanitize_text, ContentTransformer, BOM, NFC"

# Push des tags
git push origin v1.4.1
```

**Convention** : [Semantic Versioning](https://semver.org/lang/fr/) — `MAJOR.MINOR.PATCH` (ex: `1.4.1`).

---

### 1.2 CHANGELOG

Toutes les modifications du processus de nettoyage sont documentées dans **`CHANGELOG.md`** à la racine du projet.

**Format** : [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

**Exemple d'entrée pour le nettoyage** (extrait réel) :

```markdown
## [1.4.1] — 2025-02-10

### 🐛 Corrections de Bugs

#### Nettoyage des fichiers collectés (null + caractères spéciaux)
- ✅ **sanitize_text()** : Nouvelle fonction dans `src/e1/core.py` pour supprimer
  les null bytes (`\x00`), caractères de contrôle et caractère de remplacement Unicode (`\ufffd`)
- ✅ **ContentTransformer** : Nettoie désormais `title` ET `content` (avant : content uniquement)
- ✅ **_collect_local_files()** : Sanitization des `title` et `content` issus des fichiers JSON GDELT
- ✅ **Lecture JSON** : `encoding='utf-8', errors='replace'` pour éviter les plantages

#### Optimisations nettoyage
- ✅ **BOM** : Suppression du caractère BOM (`\ufeff`)
- ✅ **Normalisation Unicode (NFC)** : Évite les doublons de représentation
- ✅ **sanitize_url()** : Nettoyage des URLs avant stockage/export
```

**Fichier** : `CHANGELOG.md`

---

## 2. Documentation

### 2.1 Structure docs/

| Document | Contenu |
|----------|---------|
| **ARCHITECTURE.md** | Structure du projet, modules, flow de données |
| **Dossier_E1_nettoyage+scripts.md** | Règles de nettoyage, ContentTransformer, scripts exécutables |
| **Dossier_E1_C33_processus_agregation.md** | Processus d'agrégation (extraction, normalisation, déduplication) |
| **Dossier_E1_preuves.md** | Preuves concrètes (sources, SQL, nettoyage) |
| **LOGGING.md** | sync_log, cleaning_audit, format des logs |
| **FLOW_DONNEES.md** | Flow RAW → SILVER → GOLD |
| **PIPELINE_ANALYSIS.md** | Analyse du pipeline E1 |

---

### 2.2 Architecture du nettoyage

**`docs/ARCHITECTURE.md`** décrit les modules du pipeline :

- `src/e1/core.py` : ContentTransformer, sanitize_text, Article
- `src/e1/pipeline.py` : extract → clean → load
- `src/e1/aggregator.py` : Agrégation RAW/SILVER/GOLD

**`docs/Dossier_E1_nettoyage+scripts.md`** documente en détail :
- Règles (sanitize_text, clean_html, normalize)
- Article.is_valid()
- Fingerprint SHA256
- Scripts exécutables (ContentTransformer, SQL déduplication)

---

### 2.3 Pipeline

**`docs/FLOW_DONNEES.md`** et **`docs/Dossier_E1_C33_processus_agregation.md`** décrivent :

```
Extract (multi-sources)
    ↓
Clean (ContentTransformer.transform + is_valid)
    ↓
Load (fingerprint, déduplication, topics, sentiment)
    ↓
Aggregate (RAW → SILVER → GOLD)
```

---

### 2.4 Logging

**`LOGGING.md`** (racine) documente :

| Table | Rôle |
|-------|------|
| **sync_log** | Ingestion par source (rows_synced, status) |
| **cleaning_audit** | Historique des transformations |
| **data_quality_metrics** | Métriques qualité par source |

**Traçabilité** : Chaque run du pipeline génère des entrées dans `sync_log`. Le nettoyage est appliqué avant l'insertion ; les articles rejetés (invalides) ne sont pas chargés.

---

## 3. Fichiers clés du processus de nettoyage

| Fichier | Rôle |
|---------|------|
| `src/e1/core.py` | sanitize_text, ContentTransformer, Article.is_valid |
| `src/e1/pipeline.py` | Méthode clean(), orchestration |
| `src/e1/repository.py` | load_article_with_id (déduplication fingerprint) |
| `CHANGELOG.md` | Historique des modifications du nettoyage |
| `docs/Dossier_E1_nettoyage+scripts.md` | Documentation technique du nettoyage |
| `docs/Dossier_E1_versioning_documentation.md` | Ce document |

---

## 4. Résumé

| Critère | Implémentation |
|---------|----------------|
| **Versioning Git** | Tags semver (v1.4.1, v1.5.0), commits descriptifs |
| **CHANGELOG** | Entrées datées pour chaque modification du nettoyage |
| **Documentation architecture** | docs/ARCHITECTURE.md, FLOW_DONNEES.md |
| **Documentation pipeline** | Dossier_E1_nettoyage+scripts.md, Dossier_E1_C33_processus_agregation.md |
| **Documentation logging** | LOGGING.md (sync_log, cleaning_audit) |
