# 🔒 STRATÉGIE D'ISOLATION E1 - Guide Complet

**Objectif**: Protéger E1 (pipeline fonctionnel) lors de la construction de E2/E3  
**Principe**: E1 est la **FONDATION IMMUABLE** - Aucune modification ne doit affecter son fonctionnement

---

## 🎯 POURQUOI ISOLER E1 ?

### **Risques sans isolation**
1. ❌ **Modifications accidentelles** : E2/E3 modifient code E1 par erreur
2. ❌ **Régressions** : Nouveau code casse fonctionnalités E1 existantes
3. ❌ **Dépendances circulaires** : E1 dépend de E2/E3, rendant le système fragile
4. ❌ **Tests cassés** : Tests E1 échouent après modifications E2/E3
5. ❌ **Déploiements risqués** : Impossible de déployer E2/E3 sans risquer E1

### **Bénéfices avec isolation**
1. ✅ **Sécurité** : E1 fonctionne toujours, même si E2/E3 échouent
2. ✅ **Tests indépendants** : Tests E1/E2/E3 séparés
3. ✅ **Déploiements indépendants** : Déployer E2/E3 sans toucher E1
4. ✅ **Évolutivité** : Ajouter E4/E5 sans risque pour E1
5. ✅ **Maintenance** : Corriger bugs E2/E3 sans affecter E1

---

## 🏗️ ARCHITECTURE D'ISOLATION

### **Structure Avant (Risquée)**
```
src/
├── core.py              ← E1 + E2/E3 peuvent modifier
├── repository.py        ← E1 + E2/E3 peuvent modifier
├── api/                 ← E2
└── spark/               ← E3
```
**Problème**: E2/E3 peuvent modifier directement E1

### **Structure Après (Sécurisée)**
```
src/
├── e1/                  ← E1 ISOLÉ (package privé)
│   ├── __init__.py
│   ├── core.py
│   ├── repository.py
│   ├── tagger.py
│   ├── analyzer.py
│   ├── aggregator.py
│   ├── exporter.py
│   └── pipeline.py
│
├── e2/                  ← E2 (FastAPI + RBAC)
│   ├── __init__.py
│   ├── api/
│   └── auth/
│
├── e3/                  ← E3 (PySpark + ML)
│   ├── __init__.py
│   ├── spark/
│   └── ml/
│
└── shared/              ← INTERFACES (contrats E1 ↔ E2/E3)
    ├── __init__.py
    ├── interfaces.py    ← E1DataReader (lecture seule)
    └── models.py        ← Modèles de données partagés
```

---

## 🔌 INTERFACE DE LECTURE E1

### **Principe**
> **E2/E3 ne touchent JAMAIS directement à E1** - Uniquement via interface `E1DataReader`

### **Implémentation**

```python
# src/shared/interfaces.py
"""Interfaces entre E1 et E2/E3 - CONTRAT IMMUABLE"""

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import date
from typing import Optional
import pandas as pd
import sqlite3


class E1DataReader(ABC):
    """
    Interface de lecture E1 - E2/E3 utilisent UNIQUEMENT cette interface
    
    RÈGLES:
    - Lecture SEULE (pas d'écriture)
    - Pas de modification de E1
    - Contrat stable (pas de breaking changes)
    """
    
    @abstractmethod
    def read_raw_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Lit données RAW depuis data/raw/
        
        Args:
            date: Date au format 'YYYY-MM-DD' (optionnel, défaut: aujourd'hui)
        
        Returns:
            DataFrame avec colonnes: source, title, content, url, published_at
        
        Raises:
            FileNotFoundError: Si données RAW n'existent pas
        """
        pass
    
    @abstractmethod
    def read_silver_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Lit données SILVER depuis data/silver/
        
        Args:
            date: Date au format 'YYYY-MM-DD' (optionnel, défaut: aujourd'hui)
        
        Returns:
            DataFrame avec colonnes: raw_data_id, title, content, quality_score, topics
        
        Raises:
            FileNotFoundError: Si données SILVER n'existent pas
        """
        pass
    
    @abstractmethod
    def read_gold_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Lit données GOLD depuis data/gold/
        
        Args:
            date: Date au format 'YYYY-MM-DD' (optionnel, défaut: aujourd'hui)
        
        Returns:
            DataFrame avec colonnes: raw_data_id, title, content, sentiment, topics, confidence
        
        Raises:
            FileNotFoundError: Si données GOLD n'existent pas
        """
        pass
    
    @abstractmethod
    def get_database_stats(self) -> dict:
        """
        Lit statistiques depuis datasens.db (lecture seule)
        
        Returns:
            Dict avec clés: total_articles, total_sources, articles_by_source, etc.
        
        Raises:
            sqlite3.Error: Si erreur DB
        """
        pass


class E1DataReaderImpl(E1DataReader):
    """Implémentation concrète de E1DataReader"""
    
    def __init__(self, base_path: Path, db_path: Path):
        """
        Args:
            base_path: Chemin vers data/ (ex: Path('data/'))
            db_path: Chemin vers datasens.db
        """
        self.base_path = base_path
        self.db_path = db_path
    
    def read_raw_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """Lit RAW depuis data/raw/sources_YYYY-MM-DD/raw_articles.csv"""
        if date is None:
            date = date.today().isoformat()
        
        csv_path = self.base_path / 'raw' / f'sources_{date}' / 'raw_articles.csv'
        if not csv_path.exists():
            # Fallback: lire depuis exports/raw.csv
            csv_path = self.base_path.parent / 'exports' / 'raw.csv'
            if not csv_path.exists():
                raise FileNotFoundError(f"RAW data not found for date {date}")
        
        return pd.read_csv(csv_path)
    
    def read_silver_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """Lit SILVER depuis data/silver/v_YYYY-MM-DD/silver_articles.parquet"""
        if date is None:
            date = date.today().isoformat()
        
        parquet_path = self.base_path / 'silver' / f'v_{date}' / 'silver_articles.parquet'
        if not parquet_path.exists():
            # Fallback: lire depuis exports/silver.csv
            csv_path = self.base_path.parent / 'exports' / 'silver.csv'
            if not csv_path.exists():
                raise FileNotFoundError(f"SILVER data not found for date {date}")
            return pd.read_csv(csv_path)
        
        return pd.read_parquet(parquet_path)
    
    def read_gold_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """Lit GOLD depuis data/gold/date=YYYY-MM-DD/articles.parquet"""
        if date is None:
            date = date.today().isoformat()
        
        parquet_path = self.base_path / 'gold' / f'date={date}' / 'articles.parquet'
        if not parquet_path.exists():
            # Fallback: lire depuis exports/gold.csv
            csv_path = self.base_path.parent / 'exports' / 'gold.csv'
            if not csv_path.exists():
                raise FileNotFoundError(f"GOLD data not found for date {date}")
            return pd.read_csv(csv_path)
        
        return pd.read_parquet(parquet_path)
    
    def get_database_stats(self) -> dict:
        """Lit stats depuis datasens.db (lecture seule)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Total articles
            cursor.execute("SELECT COUNT(*) FROM raw_data")
            total_articles = cursor.fetchone()[0]
            
            # Total sources
            cursor.execute("SELECT COUNT(*) FROM source WHERE active = 1")
            total_sources = cursor.fetchone()[0]
            
            # Articles par source
            cursor.execute("""
                SELECT s.name, COUNT(r.raw_data_id) as count
                FROM source s
                LEFT JOIN raw_data r ON s.source_id = r.source_id
                WHERE s.active = 1
                GROUP BY s.name
                ORDER BY count DESC
            """)
            articles_by_source = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Articles enrichis (topics + sentiment)
            cursor.execute("""
                SELECT COUNT(DISTINCT dt.raw_data_id)
                FROM document_topic dt
                JOIN model_output mo ON dt.raw_data_id = mo.raw_data_id
                WHERE mo.model_name = 'sentiment_keyword'
            """)
            enriched_articles = cursor.fetchone()[0]
            
            return {
                'total_articles': total_articles,
                'total_sources': total_sources,
                'articles_by_source': articles_by_source,
                'enriched_articles': enriched_articles,
            }
        finally:
            conn.close()
```

---

## 📝 EXEMPLES D'UTILISATION

### **E2 (FastAPI) utilise E1DataReader**

```python
# src/e2/api/routes/gold.py
"""Endpoints GOLD - Lecture seule via E1DataReader"""

from fastapi import APIRouter, Depends, HTTPException
from src.shared.interfaces import E1DataReader, E1DataReaderImpl
from pathlib import Path

router = APIRouter(prefix="/api/v1/gold", tags=["GOLD"])

# Instance E1DataReader (singleton)
_e1_reader: Optional[E1DataReader] = None

def get_e1_reader() -> E1DataReader:
    """Retourne instance E1DataReader (singleton)"""
    global _e1_reader
    if _e1_reader is None:
        base_path = Path(__file__).parent.parent.parent.parent / 'data'
        db_path = Path.home() / 'datasens_project' / 'datasens.db'
        _e1_reader = E1DataReaderImpl(base_path, db_path)
    return _e1_reader


@router.get("/articles")
async def list_gold_articles(
    date: Optional[str] = None,
    reader: E1DataReader = Depends(get_e1_reader)
):
    """
    Liste articles GOLD (lecture seule)
    
    ✅ UTILISE UNIQUEMENT E1DataReader (pas de modification E1)
    """
    try:
        df = reader.read_gold_data(date)
        return df.to_dict('records')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="GOLD data not found")


@router.get("/stats")
async def get_gold_stats(
    reader: E1DataReader = Depends(get_e1_reader)
):
    """
    Statistiques GOLD depuis DB (lecture seule)
    
    ✅ UTILISE UNIQUEMENT E1DataReader (pas de modification E1)
    """
    try:
        stats = reader.get_database_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **E3 (PySpark) utilise E1DataReader**

```python
# src/e3/spark/readers/gold_reader.py
"""Lecteur GOLD pour PySpark - Via E1DataReader"""

from pyspark.sql import SparkSession, DataFrame
from src.shared.interfaces import E1DataReader, E1DataReaderImpl
from pathlib import Path


class SparkGoldReader:
    """Adaptateur PySpark pour E1DataReader"""
    
    def __init__(self, spark: SparkSession, e1_reader: E1DataReader):
        self.spark = spark
        self.e1_reader = e1_reader
    
    def read_gold_parquet(self, date: Optional[str] = None) -> DataFrame:
        """
        Lit GOLD Parquet avec PySpark
        
        ✅ UTILISE UNIQUEMENT E1DataReader (pas de modification E1)
        """
        if date is None:
            date = date.today().isoformat()
        
        # Chemin Parquet GOLD (déterminé par E1DataReader)
        base_path = Path(__file__).parent.parent.parent.parent / 'data'
        parquet_path = base_path / 'gold' / f'date={date}' / 'articles.parquet'
        
        if not parquet_path.exists():
            raise FileNotFoundError(f"GOLD Parquet not found for date {date}")
        
        # Lecture PySpark (lecture seule)
        return self.spark.read.parquet(str(parquet_path))


# Utilisation
def create_spark_gold_reader(spark: SparkSession) -> SparkGoldReader:
    """Factory pour créer SparkGoldReader"""
    base_path = Path(__file__).parent.parent.parent.parent / 'data'
    db_path = Path.home() / 'datasens_project' / 'datasens.db'
    e1_reader = E1DataReaderImpl(base_path, db_path)
    return SparkGoldReader(spark, e1_reader)
```

---

## ✅ TESTS DE NON-RÉGRESSION E1

### **Principe**
> **Aucun merge E2/E3 sans validation que E1 fonctionne toujours**

### **Tests obligatoires**

```python
# tests/test_e1_isolation.py
"""Tests garantissant qu'E1 fonctionne toujours"""

import pytest
from pathlib import Path
from src.e1.pipeline import E1Pipeline
from src.shared.interfaces import E1DataReaderImpl


def test_e1_pipeline_complete():
    """
    Test complet E1 - DOIT passer à 100% avant chaque merge
    
    ✅ VALIDATION: E1 génère toujours les exports attendus
    """
    # Lancer pipeline E1
    pipeline = E1Pipeline()
    pipeline.run()
    
    # Vérifications
    assert pipeline.stats['loaded'] > 0, "E1 doit charger des articles"
    assert pipeline.stats['tagged'] > 0, "E1 doit tagger des articles"
    assert pipeline.stats['analyzed'] > 0, "E1 doit analyser des articles"
    
    # Vérifier exports
    today = date.today().isoformat()
    assert Path(f'data/gold/date={today}/articles.parquet').exists(), "GOLD Parquet doit exister"
    assert Path('exports/raw.csv').exists(), "RAW CSV doit exister"
    assert Path('exports/silver.csv').exists(), "SILVER CSV doit exister"
    assert Path('exports/gold.csv').exists(), "GOLD CSV doit exister"


def test_e1_database_schema():
    """
    Test schéma DB E1 - DOIT passer à 100%
    
    ✅ VALIDATION: Tables E1 existent toujours
    """
    import sqlite3
    from pathlib import Path
    
    db_path = Path.home() / 'datasens_project' / 'datasens.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier tables E1
    tables = ['source', 'raw_data', 'sync_log', 'topic', 'document_topic', 'model_output']
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        assert cursor.fetchone() is not None, f"Table {table} doit exister"
    
    conn.close()


def test_e1_interface_stable():
    """
    Test interface E1DataReader - DOIT passer à 100%
    
    ✅ VALIDATION: Interface E1DataReader fonctionne toujours
    """
    base_path = Path('data')
    db_path = Path.home() / 'datasens_project' / 'datasens.db'
    reader = E1DataReaderImpl(base_path, db_path)
    
    # Test lecture GOLD
    df_gold = reader.read_gold_data()
    assert len(df_gold) > 0, "GOLD doit contenir des données"
    assert 'sentiment' in df_gold.columns, "GOLD doit avoir colonne sentiment"
    
    # Test stats DB
    stats = reader.get_database_stats()
    assert 'total_articles' in stats, "Stats doivent contenir total_articles"
    assert stats['total_articles'] > 0, "DB doit contenir des articles"


@pytest.fixture(autouse=True)
def run_before_each_test():
    """
    Fixture: Vérifier E1 avant chaque test E2/E3
    
    ✅ VALIDATION: E1 fonctionne avant chaque test
    """
    # Vérifier que E1 peut être importé
    from src.e1.pipeline import E1Pipeline
    assert E1Pipeline is not None, "E1Pipeline doit être importable"
```

### **CI/CD - Tests automatiques**

```yaml
# .github/workflows/test.yml
name: Tests E1 Isolation

on: [push, pull_request]

jobs:
  test-e1-isolation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run E1 isolation tests
        run: pytest tests/test_e1_isolation.py -v
      
      - name: Validate E1 pipeline
        run: |
          python main.py
          # Vérifier exports
          test -f exports/raw.csv
          test -f exports/silver.csv
          test -f exports/gold.csv
```

---

## 🚫 INTERDICTIONS ABSOLUES

### **❌ NE JAMAIS FAIRE**

1. **Modifier directement `src/e1/` depuis E2/E3**
   ```python
   # ❌ INTERDIT
   from src.e1.repository import Repository
   repo = Repository(db_path)
   repo.conn.execute("DELETE FROM raw_data")  # ❌ MODIFICATION E1
   ```

2. **Importer classes internes E1 depuis E2/E3**
   ```python
   # ❌ INTERDIT
   from src.e1.core import ContentTransformer  # ❌ CLASSE INTERNE
   ```

3. **Écrire dans fichiers E1 depuis E2/E3**
   ```python
   # ❌ INTERDIT
   with open('data/raw/sources_2025-12-18/raw_articles.json', 'w') as f:
       json.dump(new_data, f)  # ❌ ÉCRITURE DIRECTE
   ```

4. **Modifier schéma DB E1 depuis E2/E3**
   ```python
   # ❌ INTERDIT
   conn.execute("ALTER TABLE raw_data ADD COLUMN new_col TEXT")  # ❌ MODIFICATION SCHEMA
   ```

### **✅ TOUJOURS FAIRE**

1. **Utiliser uniquement `E1DataReader`**
   ```python
   # ✅ AUTORISÉ
   from src.shared.interfaces import E1DataReader, E1DataReaderImpl
   reader = E1DataReaderImpl(base_path, db_path)
   df = reader.read_gold_data()  # ✅ LECTURE SEULE
   ```

2. **Importer uniquement interfaces publiques**
   ```python
   # ✅ AUTORISÉ
   from src.shared.interfaces import E1DataReader  # ✅ INTERFACE PUBLIQUE
   ```

3. **Lire depuis exports/ ou data/ (lecture seule)**
   ```python
   # ✅ AUTORISÉ
   df = pd.read_csv('exports/gold.csv')  # ✅ LECTURE SEULE
   ```

4. **Utiliser DB en lecture seule**
   ```python
   # ✅ AUTORISÉ
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   cursor.execute("SELECT * FROM raw_data")  # ✅ LECTURE SEULE
   ```

---

## 📊 MONITORING E1

### **Métriques séparées**

```python
# src/e1/metrics.py (existant)
"""Métriques Prometheus E1 - SÉPARÉES de E2/E3"""

from prometheus_client import Counter, Histogram

# Métriques E1 uniquement
pipeline_runs_total = Counter('e1_pipeline_runs_total', 'Total E1 pipeline runs')
articles_extracted_total = Counter('e1_articles_extracted_total', 'E1 articles extracted')
articles_loaded_total = Counter('e1_articles_loaded_total', 'E1 articles loaded')
```

### **Alertes E1**

```yaml
# monitoring/prometheus_rules.yml
groups:
  - name: e1_alerts
    rules:
      - alert: E1PipelineFailed
        expr: e1_pipeline_runs_total == 0
        for: 1h
        annotations:
          summary: "E1 pipeline n'a pas tourné depuis 1h"
      
      - alert: E1ExportsMissing
        expr: count(files{path=~"exports/.*\\.csv"}) < 3
        annotations:
          summary: "Exports E1 manquants"
```

---

## 🎯 CHECKLIST VALIDATION ISOLATION

Avant chaque merge E2/E3, vérifier :

- [ ] **Tests E1 passent** : `pytest tests/test_e1_isolation.py` → 100%
- [ ] **Pipeline E1 fonctionne** : `python main.py` → Succès
- [ ] **Exports E1 générés** : `exports/raw.csv`, `exports/silver.csv`, `exports/gold.csv` existent
- [ ] **DB E1 intacte** : Schéma non modifié, données présentes
- [ ] **Interface E1DataReader stable** : Pas de breaking changes
- [ ] **Aucune modification `src/e1/`** : Git diff ne montre pas de changements E1
- [ ] **Documentation à jour** : Interfaces documentées

---

## 📚 RESSOURCES

- **Plan d'action complet** : `docs/PLAN_ACTION_E1_E2_E3.md`
- **Roadmap évolution** : `docs/ROADMAP_EVOLUTION.md`
- **Architecture** : `docs/ARCHITECTURE.md`

---

**Status**: ✅ **STRATÉGIE COMPLÈTE - PRÊT POUR IMPLÉMENTATION**  
**Dernière mise à jour**: 2025-12-18
