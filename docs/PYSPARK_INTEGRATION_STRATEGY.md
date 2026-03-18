# 🔄 PySpark Integration Strategy - E1 → E2

## 🎯 Objectif

Connecter PySpark au buffer SQLite DataSens pour récupérer le Gold Parquet **sans rien casser**, en respectant **OOP, SOLID, DRY**.

---

## 📊 État Actuel (E1)

### **Architecture Actuelle**

```
Pipeline E1
    ↓
SQLite (datasens.db)
    ├── raw_data (42,466 articles)
    ├── document_topic (82,381 lignes)
    ├── model_output (43,113 lignes)
    └── source (21 sources)
    ↓
DataAggregator
    ├── aggregate_raw() → DataFrame
    ├── aggregate_silver() → DataFrame (RAW + topics)
    └── aggregate() → DataFrame (SILVER + sentiment = GOLD)
    ↓
GoldExporter
    └── export_all() → Parquet (data/gold/date=YYYY-MM-DD/articles.parquet)
```

### **Fichiers Parquet Générés**

- **Emplacement** : `data/gold/date=YYYY-MM-DD/articles.parquet`
- **Format** : Apache Parquet v2 (PySpark compatible)
- **Partitionnement** : Par date (`date=YYYY-MM-DD`)
- **Contenu** : Toutes les colonnes GOLD (source, title, content, topic_1, topic_2, sentiment, etc.)

---

## 🎯 Stratégie d'Intégration PySpark

### **Principe : Isolation & Abstraction**

**Règle d'or** : PySpark ne touche **JAMAIS** directement à SQLite. Il lit uniquement les Parquet.

```
SQLite (E1) → Parquet (Buffer) → PySpark (E2)
     ↑              ↑                ↑
   E1 Pipeline   Export E1      Lecture seule
```

---

## 🏗️ Architecture Proposée (OOP/SOLID/DRY)

### **1. Pattern Repository (Déjà en place)**

✅ **Repository Pattern** : `src/repository.py`
- ✅ Abstraction de la couche données
- ✅ Interface claire pour accès DB
- ✅ Facile à étendre

**Pas de changement nécessaire** ✅

---

### **2. Pattern Adapter pour PySpark**

**Principe** : Adapter PySpark pour lire depuis Parquet sans dépendre de SQLite.

```python
# Structure proposée (STRATÉGIE, pas encore implémenté)
src/
  spark/
    __init__.py
    adapter.py              # Adapter PySpark (lecture Parquet)
    session.py              # SparkSession config (singleton)
    processors/
      __init__.py
      gold_reader.py        # Lecture GOLD Parquet
      gold_processor.py     # Traitement GOLD
    interfaces/
      __init__.py
      data_reader.py        # Interface (abstraction)
      data_processor.py     # Interface (abstraction)
```

---

### **3. Séparation des Responsabilités (SOLID)**

#### **Single Responsibility Principle (SRP)**

| Classe | Responsabilité Unique |
|--------|----------------------|
| `GoldParquetReader` | Lire Parquet GOLD uniquement |
| `GoldDataProcessor` | Traiter données GOLD uniquement |
| `SparkSessionManager` | Gérer SparkSession uniquement |
| `ParquetSchemaValidator` | Valider schéma Parquet uniquement |

#### **Open/Closed Principle (OCP)**

- ✅ **Ouvert à l'extension** : Nouveaux processors sans modifier existants
- ✅ **Fermé à la modification** : Pas de modification code E1

#### **Liskov Substitution Principle (LSP)**

- ✅ **Interfaces** : `DataReader`, `DataProcessor` (abstraction)
- ✅ **Implémentations** : `GoldParquetReader`, `GoldDataProcessor`

#### **Interface Segregation Principle (ISP)**

- ✅ **Interfaces séparées** : `DataReader`, `DataProcessor`, `DataWriter`
- ✅ **Pas d'interface fat** : Chaque interface = une responsabilité

#### **Dependency Inversion Principle (DIP)**

- ✅ **Dépendances vers abstractions** : Interfaces, pas implémentations
- ✅ **Injection de dépendances** : DI pour SparkSession, readers, processors

---

### **4. DRY (Don't Repeat Yourself)**

#### **Abstraction Commune**

```python
# Interface commune (STRATÉGIE)
class DataReader(ABC):
    """Interface pour lecture données"""
    @abstractmethod
    def read(self, path: str) -> DataFrame:
        pass

class ParquetReader(DataReader):
    """Implémentation lecture Parquet"""
    def read(self, path: str) -> DataFrame:
        # Lecture Parquet
        pass

class GoldParquetReader(ParquetReader):
    """Spécialisation lecture GOLD"""
    def read_gold(self, date: str = None) -> DataFrame:
        # Lecture GOLD avec partition date
        pass
```

#### **Configuration Centralisée**

```python
# src/spark/config.py (STRATÉGIE)
class SparkConfig:
    """Configuration PySpark centralisée"""
    PARQUET_BASE_PATH = "data/gold"
    SPARK_APP_NAME = "DataSens-E2"
    SPARK_MASTER = "local[*]"
    # ...
```

---

## 🔄 Flow d'Intégration Proposé

### **Option 1 : Lecture Directe Parquet (Recommandé)** ✅

```
E1 Pipeline
    ↓
GoldExporter.export_all()
    ↓
Génère: data/gold/date=YYYY-MM-DD/articles.parquet
    ↓
PySpark (E2)
    ↓
spark.read.parquet("data/gold/date=YYYY-MM-DD/articles.parquet")
    ↓
Traitement PySpark
```

**Avantages** :
- ✅ **Aucune dépendance SQLite** : PySpark lit uniquement Parquet
- ✅ **Pas de modification E1** : E1 continue de fonctionner normalement
- ✅ **Performance** : Parquet optimisé pour Spark
- ✅ **Isolation** : E1 et E2 complètement séparés

**Inconvénients** :
- ⚠️ Décalage temporel : Parquet généré par E1, puis lu par PySpark

---

### **Option 2 : Lecture SQLite via JDBC (Non recommandé)**

```
PySpark
    ↓
spark.read.jdbc(url="jdbc:sqlite:datasens.db", table="raw_data")
    ↓
Traitement PySpark
```

**Avantages** :
- ✅ Accès direct aux données

**Inconvénients** :
- ❌ **Dépendance SQLite** : PySpark dépend de SQLite
- ❌ **Performance** : JDBC plus lent que Parquet
- ❌ **Couplage** : E1 et E2 couplés
- ❌ **Risque** : Peut impacter E1 si erreur

**Recommandation** : ❌ **NE PAS UTILISER** (couplage trop fort)

---

### **Option 3 : Lecture via API FastAPI (Futur)**

```
PySpark
    ↓
Requête HTTP → FastAPI → SQLite
    ↓
Traitement PySpark
```

**Avantages** :
- ✅ Abstraction complète
- ✅ Sécurité (RBAC)

**Inconvénients** :
- ❌ Performance (HTTP overhead)
- ❌ Complexité (nécessite FastAPI)

**Recommandation** : ⚠️ **Pour plus tard** (après FastAPI)

---

## 🎯 Stratégie Recommandée : Option 1

### **Architecture Finale**

```
┌─────────────────────────────────────────┐
│           E1 PIPELINE                   │
│  (main.py - Pipeline E1)                │
│                                         │
│  SQLite (datasens.db)                   │
│    ↓                                    │
│  DataAggregator.aggregate()             │
│    ↓                                    │
│  GoldExporter.export_all()              │
│    ↓                                    │
│  Parquet: data/gold/date=*/articles.parquet │
└─────────────────────────────────────────┘
                    ↓
            [BUFFER PARQUET]
                    ↓
┌─────────────────────────────────────────┐
│         E2 PYSPARK                       │
│  (PySpark - Big Data Processing)        │
│                                         │
│  GoldParquetReader.read_gold()          │
│    ↓                                    │
│  spark.read.parquet(...)                │
│    ↓                                    │
│  GoldDataProcessor.process()            │
│    ↓                                    │
│  Traitements Big Data                   │
└─────────────────────────────────────────┘
```

---

## 📋 Implémentation Proposée (Structure)

### **1. Interface Abstraction**

```python
# src/spark/interfaces/data_reader.py (STRATÉGIE)
from abc import ABC, abstractmethod
from pyspark.sql import DataFrame

class DataReader(ABC):
    """Interface pour lecture données (abstraction)"""
    @abstractmethod
    def read(self, path: str) -> DataFrame:
        """Lit données depuis path"""
        pass
```

### **2. Implémentation Parquet**

```python
# src/spark/adapters/gold_parquet_reader.py (STRATÉGIE)
from src.spark.interfaces.data_reader import DataReader
from src.spark.session import get_spark_session
from pyspark.sql import DataFrame
from pathlib import Path
from datetime import date

class GoldParquetReader(DataReader):
    """Lit GOLD Parquet (implémentation concrète)"""
    
    def __init__(self, base_path: str = "data/gold"):
        self.base_path = Path(base_path)
        self.spark = get_spark_session()
    
    def read(self, path: str) -> DataFrame:
        """Lit Parquet depuis path"""
        return self.spark.read.parquet(path)
    
    def read_gold(self, date: date = None) -> DataFrame:
        """Lit GOLD Parquet pour une date donnée"""
        if date:
            path = self.base_path / f"date={date:%Y-%m-%d}" / "articles.parquet"
        else:
            # Lire toutes les partitions
            path = str(self.base_path / "date=*" / "articles.parquet")
        
        if not Path(path).exists() and "*" not in str(path):
            raise FileNotFoundError(f"Parquet not found: {path}")
        
        return self.read(str(path))
```

### **3. SparkSession Singleton**

```python
# src/spark/session.py (STRATÉGIE)
from pyspark.sql import SparkSession
from typing import Optional

_spark_session: Optional[SparkSession] = None

def get_spark_session() -> SparkSession:
    """Singleton SparkSession (DRY)"""
    global _spark_session
    if _spark_session is None:
        _spark_session = SparkSession.builder \
            .appName("DataSens-E2") \
            .config("spark.sql.parquet.enableVectorizedReader", "true") \
            .getOrCreate()
    return _spark_session

def close_spark_session():
    """Ferme SparkSession"""
    global _spark_session
    if _spark_session:
        _spark_session.stop()
        _spark_session = None
```

### **4. Processor GOLD**

```python
# src/spark/processors/gold_processor.py (STRATÉGIE)
from src.spark.interfaces.data_processor import DataProcessor
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, when

class GoldDataProcessor(DataProcessor):
    """Traite données GOLD (implémentation concrète)"""
    
    def process(self, df: DataFrame) -> DataFrame:
        """Traite DataFrame GOLD"""
        # Exemples de traitements
        # - Agrégations
        # - Filtres
        # - Transformations
        return df
    
    def aggregate_by_sentiment(self, df: DataFrame) -> DataFrame:
        """Agrège par sentiment"""
        return df.groupBy("sentiment").agg(
            count("*").alias("count")
        )
```

---

## ✅ Vérification OOP/SOLID/DRY

### **OOP (Object-Oriented Programming)**

✅ **Classes** : `GoldParquetReader`, `GoldDataProcessor`, `SparkSessionManager`
✅ **Héritage** : `GoldParquetReader` hérite de `ParquetReader` hérite de `DataReader`
✅ **Polymorphisme** : Interface `DataReader`, implémentations multiples
✅ **Encapsulation** : Méthodes privées, propriétés protégées

### **SOLID**

✅ **SRP** : Chaque classe = une responsabilité
✅ **OCP** : Extension sans modification (nouveaux processors)
✅ **LSP** : Interfaces substituables
✅ **ISP** : Interfaces séparées (DataReader, DataProcessor)
✅ **DIP** : Dépendances vers abstractions (interfaces)

### **DRY**

✅ **Abstraction** : Interfaces communes (`DataReader`, `DataProcessor`)
✅ **Singleton** : SparkSession (une seule instance)
✅ **Configuration** : Config centralisée
✅ **Helpers** : Fonctions utilitaires réutilisables

---

## 🔒 Garanties : Rien ne Casse

### **Isolation Complète**

1. ✅ **PySpark ne touche pas SQLite** : Lit uniquement Parquet
2. ✅ **E1 continue normalement** : Pipeline E1 inchangé
3. ✅ **Pas de dépendance bidirectionnelle** : E1 → Parquet → E2 (unidirectionnel)
4. ✅ **Pas de modification E1** : Code E1 intact

### **Points de Contrôle**

1. ✅ **Validation schéma** : Vérifier schéma Parquet avant lecture
2. ✅ **Gestion erreurs** : Try/catch, fallback
3. ✅ **Logging** : Tracer toutes les opérations
4. ✅ **Tests** : Tests unitaires pour chaque composant

---

## 📋 Checklist Implémentation (Futur)

### **Phase 1 : Setup PySpark**
- [ ] Installer PySpark (`pip install pyspark`)
- [ ] Créer structure `src/spark/`
- [ ] Implémenter `SparkSessionManager` (singleton)
- [ ] Tests SparkSession

### **Phase 2 : Reader Parquet**
- [ ] Créer interface `DataReader`
- [ ] Implémenter `ParquetReader`
- [ ] Implémenter `GoldParquetReader`
- [ ] Tests lecture Parquet

### **Phase 3 : Processor**
- [ ] Créer interface `DataProcessor`
- [ ] Implémenter `GoldDataProcessor`
- [ ] Tests traitement

### **Phase 4 : Intégration**
- [ ] Intégrer dans pipeline E2
- [ ] Tests end-to-end
- [ ] Documentation

---

## 🎯 Résumé Stratégie

### **Principe Fondamental**

**PySpark lit uniquement les Parquet générés par E1. Aucune connexion directe à SQLite.**

### **Architecture**

```
E1 (SQLite) → Parquet (Buffer) → E2 (PySpark)
     ↑              ↑                ↑
  Pipeline E1    Export E1      Lecture seule
  (inchangé)     (existant)     (nouveau)
```

### **Respect OOP/SOLID/DRY**

- ✅ **OOP** : Classes, héritage, polymorphisme, encapsulation
- ✅ **SOLID** : 5 principes respectés
- ✅ **DRY** : Abstraction, singleton, configuration centralisée

### **Garanties**

- ✅ **Rien ne casse** : E1 inchangé
- ✅ **Isolation** : E1 et E2 séparés
- ✅ **Performance** : Parquet optimisé pour Spark
- ✅ **Maintenabilité** : Code propre, testable

---

**Status** : 📋 **STRATÉGIE DÉFINIE - PRÊT POUR IMPLÉMENTATION (QUAND VOUS LE SOUHAITEZ)**
