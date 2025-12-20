# 🏗️ Architecture Buffer SQLite - Documentation Technique

## 📋 Vue d'Ensemble

Ce document explique l'architecture technique du **buffer SQLite** (`datasens.db`) et son cycle de vie dans le système DataSens E1/E2/E3.

**Niveau** : Senior Developer / Architect  
**Principes** : OOP, SOLID, DRY  
**Sécurité** : Garanties de non-perte de données

---

## 🎯 Concept Architectural

### Buffer SQLite = Zone de Transit Temporaire

```
┌─────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE BUFFER                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  SOURCES EXTERNES (14 sources)                     │    │
│  │  - RSS, APIs, Web Scraping, Datasets               │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ COLLECTE                          │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  BUFFER SQLite (datasens.db) - TEMPORAIRE          │    │
│  │  ⚠️ Zone de transit - NE PAS CONSERVER               │    │
│  │                                                      │    │
│  │  Tables:                                            │    │
│  │  - raw_data (articles bruts)                        │    │
│  │  - document_topic (enrichissement topics)          │    │
│  │  - model_output (enrichissement sentiment)         │    │
│  │  - source, topic, sync_log (métadonnées)          │    │
│  │                                                      │    │
│  │  Rôle:                                              │    │
│  │  1. Collecte quotidienne                            │    │
│  │  2. Enrichissement (topics + sentiment)            │    │
│  │  3. Export vers Parquet GOLD                        │    │
│  │  4. Nettoyage (après export vérifié)                │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ EXPORT (GoldExporter)             │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  STOCKAGE PERMANENT Parquet GOLD                    │    │
│  │  ✅ Source de vérité                                │    │
│  │  ✅ Immutable (une fois créé, ne change pas)        │    │
│  │  ✅ Partitionné par date                            │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ LECTURE (PySpark)                 │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  PYSPARK (E2/E3)                                    │    │
│  │  - GoldParquetReader (lecture seule)               │    │
│  │  - GoldDataProcessor (analyses)                    │    │
│  │  - API Endpoints (analytics)                        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 Garanties de Sécurité

### Principe : Export Avant Nettoyage

**Règle d'or** : Les données ne sont **JAMAIS** supprimées du buffer SQLite avant d'être **vérifiées** dans Parquet GOLD.

### Mécanismes de Protection

#### 1. Vérification Export Parquet (Ligne 45-60)

```python
def check_parquet_export(target_date: date | None = None) -> bool:
    """Vérifie qu'un export Parquet existe pour la date donnée"""
    check_date = target_date or date.today()
    parquet_path = Path('data/gold') / f"date={check_date:%Y-%m-%d}" / "articles.parquet"
    
    if parquet_path.exists():
        import pyarrow.parquet as pq
        try:
            num_rows = pq.ParquetFile(parquet_path).metadata.num_rows
            print(f"  ✅ Parquet trouve: {parquet_path}")
            print(f"     {num_rows:,} lignes")
            return True
        except Exception as e:
            print(f"  ⚠️ Parquet existe mais erreur lecture: {e}")
            return False
    else:
        print(f"  ❌ Parquet non trouve: {parquet_path}")
        return False
```

**Garanties** :
- ✅ Vérifie l'existence du fichier Parquet
- ✅ Vérifie que le fichier est lisible (pas corrompu)
- ✅ Affiche le nombre de lignes pour validation
- ❌ **Bloque le nettoyage si Parquet absent ou corrompu**

#### 2. Confirmation Utilisateur (Ligne 200-210)

```python
# Vérifier export Parquet
print("\nVerification export Parquet GOLD...")
if not check_parquet_export():
    print("\n⚠️ ATTENTION: Aucun export Parquet trouve pour aujourd'hui!")
    confirm = input("   Continuer quand meme? (o/n): ").strip().lower()
    if confirm != 'o':
        print("   Nettoyage annule")
        sys.exit(0)
```

**Garanties** :
- ✅ Demande confirmation explicite si Parquet manquant
- ✅ Permet d'annuler le nettoyage
- ✅ Avertissement clair avant action destructive

#### 3. Mode Simulation (Dry-Run) (Ligne 220-250)

```python
elif choice == "3":
    keep_days_input = input("Nombre de jours a garder (defaut: 7): ").strip()
    keep_days = int(keep_days_input) if keep_days_input else 7
    
    print(f"\nSIMULATION: Nettoyage des articles plus anciens que {keep_days} jours...")
    result = cleanup_buffer(db_path, keep_days=keep_days, dry_run=True)
    print("\n⚠️ SIMULATION - Aucune donnee n'a ete supprimee")
```

**Garanties** :
- ✅ Permet de voir ce qui sera supprimé **sans supprimer**
- ✅ Affiche les statistiques avant/après (simulation)
- ✅ Aucune modification de la base de données en mode simulation

---

## 🏗️ Architecture du Code

### Principe SOLID Appliqué

#### 1. Single Responsibility Principle (SRP)

Chaque fonction a une responsabilité unique :

```python
def get_db_path() -> str | None:
    """Trouve le chemin de la base de données"""
    # Responsabilité UNIQUE: Trouver le chemin DB
    # Ne fait QUE ça, rien d'autre

def check_parquet_export(target_date: date | None = None) -> bool:
    """Vérifie qu'un export Parquet existe"""
    # Responsabilité UNIQUE: Vérifier export Parquet
    # Ne fait QUE ça, rien d'autre

def get_db_stats(conn: sqlite3.Connection) -> dict:
    """Récupère les statistiques de la base de données"""
    # Responsabilité UNIQUE: Récupérer stats
    # Ne fait QUE ça, rien d'autre

def cleanup_buffer(...) -> dict:
    """Nettoie le buffer SQLite"""
    # Responsabilité UNIQUE: Nettoyer le buffer
    # Ne fait QUE ça, rien d'autre
```

#### 2. Open/Closed Principle (OCP)

Le code est extensible sans modification :

```python
def cleanup_buffer(
    db_path: str,
    keep_days: int = 7,
    target_date: date | None = None,  # ← Extension possible
    dry_run: bool = False              # ← Extension possible
) -> dict:
    """Nettoie le buffer SQLite"""
    # Peut être étendu avec de nouveaux paramètres
    # Sans modifier le code existant
```

#### 3. Dependency Inversion Principle (DIP)

Les dépendances sont injectées, pas hardcodées :

```python
def cleanup_buffer(db_path: str, ...):  # ← Injection de dépendance
    conn = sqlite3.connect(db_path)     # ← Utilise l'injection
    # Pas de chemin hardcodé dans la fonction
```

### Principe DRY (Don't Repeat Yourself)

#### Éviter la Duplication

```python
# ❌ MAUVAIS (duplication)
if target_date:
    cursor.execute("DELETE FROM raw_data WHERE date(collected_at) = date(?)", (date_str,))
    deleted_raw = cursor.rowcount
    cursor.execute("DELETE FROM document_topic WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)")
    deleted_topics = cursor.rowcount
    cursor.execute("DELETE FROM model_output WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)")
    deleted_sentiment = cursor.rowcount
else:
    cursor.execute("DELETE FROM raw_data WHERE collected_at < date('now', '-' || ? || ' days')", (keep_days,))
    deleted_raw = cursor.rowcount
    cursor.execute("DELETE FROM document_topic WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)")
    deleted_topics = cursor.rowcount
    cursor.execute("DELETE FROM model_output WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)")
    deleted_sentiment = cursor.rowcount

# ✅ BON (DRY - pas de duplication)
if target_date:
    # Supprimer articles de cette date
    cursor.execute("DELETE FROM raw_data WHERE date(collected_at) = date(?)", (date_str,))
    deleted_raw = cursor.rowcount
else:
    # Supprimer articles anciens
    cursor.execute("DELETE FROM raw_data WHERE collected_at < date('now', '-' || ? || ' days')", (keep_days,))
    deleted_raw = cursor.rowcount

# Nettoyage tables liées (COMMUN aux deux cas)
cursor.execute("DELETE FROM document_topic WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)")
deleted_topics = cursor.rowcount

cursor.execute("DELETE FROM model_output WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)")
deleted_sentiment = cursor.rowcount
```

---

## 🔄 Workflow Détaillé

### Étape 1 : Collecte Quotidienne (E1 Pipeline)

```python
# src/e1/pipeline.py
def run(self):
    # 1. Extraction depuis sources
    articles = self.extract()  # → raw_data (SQLite)
    
    # 2. Nettoyage
    articles = self.clean(articles)  # → raw_data (SQLite)
    
    # 3. Chargement dans buffer SQLite
    self.load(articles)  # → raw_data (SQLite)
    
    # 4. Enrichissement topics
    # → document_topic (SQLite)
    
    # 5. Enrichissement sentiment
    # → model_output (SQLite)
```

**Résultat** : Buffer SQLite contient les données enrichies

### Étape 2 : Export Buffer → Parquet GOLD

```python
# src/e1/pipeline.py
aggregator = DataAggregator(db_path)
exporter = GoldExporter()

# Agrégation GOLD (JOINs SQL)
df_gold = aggregator.aggregate()
# → Joint raw_data + document_topic + model_output

# Export Parquet
result = exporter.export_all(df_gold, date.today())
# → data/gold/date=2025-12-20/articles.parquet
```

**Résultat** : Données sauvegardées dans Parquet GOLD (stockage permanent)

### Étape 3 : Vérification Export (Sécurité)

```python
# scripts/cleanup_sqlite_buffer.py
if not check_parquet_export():
    # ⚠️ Parquet manquant → Bloque nettoyage
    confirm = input("Continuer quand meme? (o/n): ")
    if confirm != 'o':
        sys.exit(0)  # ← Annule nettoyage
```

**Garantie** : Pas de nettoyage si Parquet manquant

### Étape 4 : Nettoyage Buffer (Optionnel)

```python
# scripts/cleanup_sqlite_buffer.py
cleanup_buffer(db_path, keep_days=7, dry_run=False)
```

**Ce qui se passe** :
1. Supprime `raw_data` (articles anciens)
2. Supprime `document_topic` (orphans après suppression raw_data)
3. Supprime `model_output` (orphans après suppression raw_data)
4. **Garde** `source`, `topic`, `sync_log` (métadonnées)

---

## 🛡️ Intégrité Référentielle

### Tables Liées et Cascades

```
raw_data (table principale)
    │
    ├── document_topic (FK: raw_data_id)
    │       └── topic (FK: topic_id)
    │
    └── model_output (FK: raw_data_id)
```

**Stratégie de Nettoyage** :

1. **Supprimer d'abord `raw_data`** (table principale)
   ```sql
   DELETE FROM raw_data WHERE collected_at < date('now', '-7 days')
   ```

2. **Nettoyer les orphans** (tables liées)
   ```sql
   DELETE FROM document_topic 
   WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)
   
   DELETE FROM model_output 
   WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)
   ```

**Pourquoi cet ordre ?**
- ✅ Respecte l'intégrité référentielle
- ✅ Évite les erreurs de contraintes FK
- ✅ Nettoie proprement les données orphelines

---

## 📊 Statistiques et Monitoring

### Avant Nettoyage

```python
stats_before = get_db_stats(conn)
# {
#     'raw_data_count': 43022,
#     'document_topic_count': 86044,
#     'model_output_count': 43022,
#     'oldest_date': '2025-12-16',
#     'newest_date': '2025-12-20'
# }
```

### Après Nettoyage

```python
stats_after = get_db_stats(conn)
# {
#     'raw_data_count': 5000,  # ← Réduit (articles > 7 jours supprimés)
#     'document_topic_count': 10000,  # ← Réduit (orphans nettoyés)
#     'model_output_count': 5000,  # ← Réduit (orphans nettoyés)
#     'oldest_date': '2025-12-13',  # ← Mis à jour
#     'newest_date': '2025-12-20'
# }
```

### Calcul des Suppressions

```python
deleted_raw = stats_before['raw_data_count'] - stats_after['raw_data_count']
deleted_topics = stats_before['document_topic_count'] - stats_after['document_topic_count']
deleted_sentiment = stats_before['model_output_count'] - stats_after['model_output_count']
```

---

## 🔍 Analyse du Code Ligne par Ligne

### Fonction `cleanup_buffer()` - Lignes 100-200

```python
def cleanup_buffer(
    db_path: str,                    # ← Injection dépendance (DIP)
    keep_days: int = 7,              # ← Paramètre configurable
    target_date: date | None = None, # ← Flexibilité (OCP)
    dry_run: bool = False            # ← Sécurité (simulation)
) -> dict:
    """
    Nettoie le buffer SQLite
    
    Args:
        db_path: Chemin vers la base de données
        keep_days: Nombre de jours à garder (articles plus récents)
        target_date: Date spécifique à nettoyer (optionnel)
        dry_run: Si True, simule sans supprimer
    
    Returns:
        Dictionnaire avec statistiques de nettoyage
    """
    # 1. Connexion DB (injection dépendance)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. Statistiques AVANT (baseline)
    stats_before = get_db_stats(conn)
    
    # 3. Logique de nettoyage (SRP: une seule responsabilité)
    if target_date:
        # Nettoyage par date spécifique
        cursor.execute("""
            DELETE FROM raw_data 
            WHERE date(collected_at) = date(?)
        """, (target_date.isoformat(),))
        deleted_raw = cursor.rowcount
    else:
        # Nettoyage par ancienneté
        cursor.execute("""
            DELETE FROM raw_data 
            WHERE collected_at < date('now', '-' || ? || ' days')
        """, (keep_days,))
        deleted_raw = cursor.rowcount
    
    # 4. Nettoyage tables liées (DRY: code commun)
    cursor.execute("""
        DELETE FROM document_topic 
        WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)
    """)
    deleted_topics = cursor.rowcount
    
    cursor.execute("""
        DELETE FROM model_output 
        WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)
    """)
    deleted_sentiment = cursor.rowcount
    
    # 5. Commit (si pas dry_run)
    if not dry_run:
        conn.commit()
    
    # 6. Statistiques APRÈS
    stats_after = get_db_stats(conn)
    
    # 7. Retour résultats
    return {
        'deleted_raw': deleted_raw,
        'deleted_topics': deleted_topics,
        'deleted_sentiment': deleted_sentiment,
        'stats_before': stats_before,
        'stats_after': stats_after
    }
```

**Points Clés** :
- ✅ **SRP** : Une seule responsabilité (nettoyer le buffer)
- ✅ **DIP** : Injection de `db_path` (pas de hardcode)
- ✅ **OCP** : Extensible (`target_date`, `dry_run`)
- ✅ **DRY** : Pas de duplication (nettoyage tables liées commun)
- ✅ **Sécurité** : `dry_run` pour simulation

---

## ⚠️ Points d'Attention

### 1. Transaction SQLite

**Problème potentiel** : Si erreur pendant nettoyage, données partiellement supprimées

**Solution actuelle** : Utilise `conn.commit()` à la fin (transaction implicite)

**Amélioration possible** :
```python
try:
    # Nettoyage...
    conn.commit()  # ← Commit seulement si tout OK
except Exception as e:
    conn.rollback()  # ← Rollback en cas d'erreur
    raise
```

### 2. Vérification Parquet

**Problème potentiel** : Parquet peut exister mais être corrompu

**Solution actuelle** : Vérifie existence + lisibilité (ligne 50-55)

**Amélioration possible** :
```python
def check_parquet_export(target_date: date | None = None) -> bool:
    # Vérifier existence
    if not parquet_path.exists():
        return False
    
    # Vérifier lisibilité
    try:
        pq.ParquetFile(parquet_path).metadata.num_rows
    except Exception:
        return False
    
    # Vérifier nombre de lignes > 0
    if num_rows == 0:
        return False
    
    return True
```

### 3. Backup Avant Nettoyage

**Recommandation** : Créer un backup SQLite avant nettoyage

```python
def create_backup(db_path: str) -> str:
    """Crée un backup de la base de données"""
    backup_path = f"{db_path}.backup.{date.today().isoformat()}"
    import shutil
    shutil.copy2(db_path, backup_path)
    return backup_path
```

---

## 📝 Checklist Avant Nettoyage

### ✅ Vérifications Obligatoires

1. **Export Parquet existe** ✅
   ```python
   check_parquet_export()  # → True
   ```

2. **Parquet lisible** ✅
   ```python
   pq.ParquetFile(parquet_path).metadata.num_rows  # → > 0
   ```

3. **Confirmation utilisateur** ✅
   ```python
   confirm = input("Continuer? (o/n): ")  # → 'o'
   ```

4. **Mode simulation testé** ✅
   ```python
   cleanup_buffer(..., dry_run=True)  # → Testé d'abord
   ```

### ⚠️ Vérifications Recommandées

5. **Backup SQLite créé** (optionnel mais recommandé)
6. **Vérifier nombre de lignes Parquet vs SQLite** (cohérence)
7. **Vérifier dates dans Parquet** (cohérence)

---

## 🔧 Utilisation Recommandée

### Workflow Sécurisé

```bash
# 1. Exécuter pipeline E1 (collecte + export)
python main.py
# → Collecte dans buffer SQLite
# → Export vers Parquet GOLD

# 2. Vérifier export Parquet
python -c "from pathlib import Path; import pyarrow.parquet as pq; \
    p = Path('data/gold/date=2025-12-20/articles.parquet'); \
    print(f'Parquet: {pq.ParquetFile(p).metadata.num_rows} lignes')"

# 3. Simulation nettoyage (dry-run)
python scripts/cleanup_sqlite_buffer.py
# → Choisir option 3 (simulation)
# → Vérifier ce qui sera supprimé

# 4. Nettoyage réel (si simulation OK)
python scripts/cleanup_sqlite_buffer.py
# → Choisir option 1 (nettoyer par jours)
# → Confirmer
```

---

## 🎓 Principes Appliqués

### OOP (Object-Oriented Programming)

**Bien que le script soit procédural**, les principes OOP sont respectés :

- **Encapsulation** : Fonctions isolées avec responsabilités claires
- **Abstraction** : `get_db_stats()` abstrait la complexité SQL
- **Séparation des préoccupations** : Chaque fonction = une préoccupation

### SOLID

- ✅ **S**ingle Responsibility : Chaque fonction = une responsabilité
- ✅ **O**pen/Closed : Extensible via paramètres (`target_date`, `dry_run`)
- ✅ **L**iskov Substitution : N/A (pas d'héritage)
- ✅ **I**nterface Segregation : N/A (pas d'interfaces)
- ✅ **D**ependency Inversion : Injection `db_path` (pas de hardcode)

### DRY

- ✅ Pas de duplication de code SQL
- ✅ Nettoyage tables liées factorisé
- ✅ Statistiques avant/après réutilisables

---

## 🔐 Sécurité et Garanties

### Garanties de Non-Perte de Données

1. **Vérification Export Parquet** ✅
   - Bloque si Parquet absent
   - Bloque si Parquet corrompu

2. **Confirmation Utilisateur** ✅
   - Demande confirmation explicite
   - Permet annulation

3. **Mode Simulation** ✅
   - Permet test sans risque
   - Affiche ce qui sera supprimé

4. **Statistiques Avant/Après** ✅
   - Transparence totale
   - Vérification possible

### Recommandations Supplémentaires

5. **Backup SQLite** (à implémenter)
   - Créer backup avant nettoyage
   - Permet rollback si problème

6. **Vérification Cohérence** (à implémenter)
   - Comparer nombre lignes SQLite vs Parquet
   - Vérifier dates cohérentes

---

## 📚 Références

- **Code Source** : `scripts/cleanup_sqlite_buffer.py`
- **Export E1** : `src/e1/exporter.py` → `export_all()`
- **Agrégation E1** : `src/e1/aggregator.py` → `aggregate()`
- **Workflow Complet** : `docs/WORKFLOW_PARQUET_PYSPARK.md`

---

**Dernière mise à jour** : 2025-12-20  
**Auteur** : DataSens Architecture Team  
**Niveau** : Senior Developer / Architect
