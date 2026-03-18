# PySpark Integration Sécurisée - Plan d'Implémentation

## 🎯 Objectif

Intégrer PySpark dans E1 **SANS RIEN CASSER**, en respectant l'isolation E1.

## 🔒 Principe Fondamental

**PySpark lit UNIQUEMENT les Parquet générés par E1. Aucune connexion directe à SQLite.**

```
E1 Pipeline → Parquet (Buffer) → PySpark (Lecture seule)
     ↑              ↑                    ↑
  SQLite      Export E1          Aucun accès DB
```

## ✅ Garanties de Sécurité

### 1. Isolation Complète

- ✅ **PySpark ne touche pas SQLite** : Lit uniquement Parquet
- ✅ **E1 continue normalement** : Pipeline E1 inchangé
- ✅ **Pas de dépendance bidirectionnelle** : E1 → Parquet → PySpark (unidirectionnel)
- ✅ **Pas de modification E1** : Code E1 intact

### 2. Points de Contrôle

- ✅ **Validation schéma** : Vérifier schéma Parquet avant lecture
- ✅ **Gestion erreurs** : Try/catch, fallback
- ✅ **Logging** : Tracer toutes les opérations
- ✅ **Tests** : Tests unitaires pour chaque composant

## 📋 Plan d'Implémentation par Étapes

### Phase 0 : Préparation (Sécurité)

#### Étape 0.1 : Backup & Tests

```bash
# 1. Backup de la DB
cp C:\Users\Utilisateur\datasens_project\datasens.db \
   C:\Users\Utilisateur\datasens_project\datasens.db.backup

# 2. Vérifier que E1 fonctionne
python main.py

# 3. Vérifier que E2 fonctionne
python -m pytest tests/test_e2_api.py -v
```

**Checkpoint** : ✅ E1 et E2 fonctionnent avant de commencer

#### Étape 0.2 : Créer Branche Git

```bash
git checkout -b feature/pyspark-integration
```

**Checkpoint** : ✅ Branche séparée pour isolation

### Phase 1 : Structure PySpark (Sans Impact E1)

#### Étape 1.1 : Créer Structure `src/spark/`

```
src/
  spark/
    __init__.py              # Package PySpark
    session.py               # SparkSession singleton
    config.py                # Configuration PySpark
    interfaces/
      __init__.py
      data_reader.py         # Interface abstraction
    adapters/
      __init__.py
      gold_parquet_reader.py # Lecture Parquet GOLD
    processors/
      __init__.py
      gold_processor.py      # Traitement GOLD
```

**Checkpoint** : ✅ Structure créée, aucun impact E1

#### Étape 1.2 : Tests de Base

```python
# tests/test_spark_session.py
def test_spark_session_creation():
    """Test que SparkSession se crée sans erreur"""
    from src.spark.session import get_spark_session
    spark = get_spark_session()
    assert spark is not None
    assert spark.appName == "DataSens-E2"
```

**Checkpoint** : ✅ SparkSession fonctionne

### Phase 2 : Reader Parquet (Lecture Seule)

#### Étape 2.1 : Interface Abstraction

```python
# src/spark/interfaces/data_reader.py
from abc import ABC, abstractmethod
from pyspark.sql import DataFrame

class DataReader(ABC):
    """Interface pour lecture données (abstraction)"""
    @abstractmethod
    def read(self, path: str) -> DataFrame:
        """Lit données depuis path"""
        pass
```

**Checkpoint** : ✅ Interface créée, aucun impact E1

#### Étape 2.2 : Implémentation Parquet Reader

```python
# src/spark/adapters/gold_parquet_reader.py
from src.spark.interfaces.data_reader import DataReader
from src.spark.session import get_spark_session
from pyspark.sql import DataFrame
from pathlib import Path
from datetime import date

class GoldParquetReader(DataReader):
    """Lit GOLD Parquet (lecture seule, pas de modification E1)"""
    
    def __init__(self, base_path: str = "data/gold"):
        self.base_path = Path(base_path)
        self.spark = get_spark_session()
    
    def read_gold(self, date: date = None) -> DataFrame:
        """Lit GOLD Parquet pour une date donnée"""
        if date:
            path = self.base_path / f"date={date:%Y-%m-%d}" / "articles.parquet"
        else:
            # Lire toutes les partitions
            path = str(self.base_path / "date=*" / "articles.parquet")
        
        if not Path(path).exists() and "*" not in str(path):
            raise FileNotFoundError(f"Parquet not found: {path}")
        
        return self.spark.read.parquet(str(path))
```

**Checkpoint** : ✅ Reader fonctionne, lit uniquement Parquet

#### Étape 2.3 : Tests Reader

```python
# tests/test_gold_parquet_reader.py
def test_read_gold_parquet():
    """Test lecture Parquet GOLD"""
    from src.spark.adapters.gold_parquet_reader import GoldParquetReader
    from datetime import date
    
    reader = GoldParquetReader()
    df = reader.read_gold(date.today())
    
    assert df is not None
    assert df.count() > 0
    # Vérifier colonnes attendues
    assert "title" in df.columns
    assert "sentiment" in df.columns
```

**Checkpoint** : ✅ Tests passent, lecture Parquet fonctionne

### Phase 3 : Processor (Traitement)

#### Étape 3.1 : Interface Processor

```python
# src/spark/interfaces/data_processor.py
from abc import ABC, abstractmethod
from pyspark.sql import DataFrame

class DataProcessor(ABC):
    """Interface pour traitement données"""
    @abstractmethod
    def process(self, df: DataFrame) -> DataFrame:
        """Traite DataFrame"""
        pass
```

**Checkpoint** : ✅ Interface créée

#### Étape 3.2 : Implémentation Processor

```python
# src/spark/processors/gold_processor.py
from src.spark.interfaces.data_processor import DataProcessor
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, when

class GoldDataProcessor(DataProcessor):
    """Traite données GOLD (sans modification E1)"""
    
    def process(self, df: DataFrame) -> DataFrame:
        """Traite DataFrame GOLD"""
        # Exemples de traitements (sans modification E1)
        return df
    
    def aggregate_by_sentiment(self, df: DataFrame) -> DataFrame:
        """Agrège par sentiment"""
        return df.groupBy("sentiment").agg(
            count("*").alias("count")
        )
```

**Checkpoint** : ✅ Processor fonctionne, pas de modification E1

### Phase 4 : Intégration (Optionnelle)

#### Étape 4.1 : Script de Test

```python
# scripts/test_pyspark_integration.py
"""Test intégration PySpark (lecture seule)"""
from src.spark.adapters.gold_parquet_reader import GoldParquetReader
from src.spark.processors.gold_processor import GoldDataProcessor
from datetime import date

def main():
    # 1. Lire Parquet GOLD
    reader = GoldParquetReader()
    df_gold = reader.read_gold(date.today())
    
    print(f"✅ Parquet lu : {df_gold.count()} lignes")
    print(f"✅ Colonnes : {df_gold.columns}")
    
    # 2. Traiter
    processor = GoldDataProcessor()
    df_processed = processor.process(df_gold)
    
    # 3. Agrégation exemple
    df_sentiment = processor.aggregate_by_sentiment(df_gold)
    df_sentiment.show()
    
    print("✅ Intégration PySpark réussie (lecture seule)")

if __name__ == "__main__":
    main()
```

**Checkpoint** : ✅ Script fonctionne, E1 intact

## 🔍 Vérifications de Sécurité

### Checklist Avant Chaque Commit

- [ ] E1 pipeline fonctionne : `python main.py`
- [ ] E2 API fonctionne : `python -m pytest tests/test_e2_api.py`
- [ ] Aucune modification de `src/e1/`
- [ ] Aucune connexion SQLite dans PySpark
- [ ] PySpark lit uniquement Parquet
- [ ] Tests PySpark passent

### Tests de Régression

```bash
# Avant chaque commit
python main.py                    # E1 doit fonctionner
python -m pytest tests/          # Tous les tests doivent passer
python run_e2_api.py &           # E2 doit démarrer
curl http://localhost:8001/health # E2 doit répondre
```

## 🚨 Plan de Rollback

Si quelque chose casse :

1. **Revenir à la branche main** :
   ```bash
   git checkout main
   ```

2. **Restaurer la DB** :
   ```bash
   cp C:\Users\Utilisateur\datasens_project\datasens.db.backup \
      C:\Users\Utilisateur\datasens_project\datasens.db
   ```

3. **Vérifier E1** :
   ```bash
   python main.py
   ```

## 📊 Résumé Sécurité

### ✅ Ce qui est SÉCURISÉ

- ✅ **PySpark lit uniquement Parquet** : Pas d'accès SQLite
- ✅ **E1 inchangé** : Aucune modification de `src/e1/`
- ✅ **Isolation complète** : E1 et PySpark séparés
- ✅ **Tests indépendants** : Tests PySpark séparés
- ✅ **Branche Git** : Isolation code

### ❌ Ce qui est INTERDIT

- ❌ **Pas de connexion SQLite dans PySpark**
- ❌ **Pas de modification de `src/e1/`**
- ❌ **Pas de dépendance bidirectionnelle**
- ❌ **Pas de modification des exports E1**

## 🎯 Prochaines Étapes

1. **Phase 0** : Backup & Tests (5 min)
2. **Phase 1** : Structure PySpark (15 min)
3. **Phase 2** : Reader Parquet (30 min)
4. **Phase 3** : Processor (30 min)
5. **Phase 4** : Intégration (15 min)

**Total estimé** : ~1h30 avec tests

**Risque** : ⚠️ **TRÈS FAIBLE** (lecture seule, isolation complète)
