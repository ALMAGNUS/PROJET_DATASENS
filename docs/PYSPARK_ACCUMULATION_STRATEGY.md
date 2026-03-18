# 📊 PySpark - Stratégie d'Accumulation Parquet (Actuel + Jour J)

## 🎯 Objectif

PySpark doit lire **plusieurs partitions Parquet** et les **combiner** :
- ✅ **Parquet actuel** (dernière partition complète)
- ✅ **+ Parquet du jour J** (nouvelle partition du jour)
- ✅ **= Vue unifiée** : Parquet actuel + Parquet jour J

---

## 📋 Logique d'Accumulation

### **Scénario**

```
Jour 1 (J1) :
  - Parquet actuel : date=2025-01-15/articles.parquet
  - Nouveau du jour : date=2025-01-16/articles.parquet
  - PySpark lit : date=2025-01-15 + date=2025-01-16

Jour 2 (J2) :
  - Parquet actuel : date=2025-01-16/articles.parquet (devient le nouveau "actuel")
  - Nouveau du jour : date=2025-01-17/articles.parquet
  - PySpark lit : date=2025-01-16 + date=2025-01-17

Jour 3 (J3) :
  - Parquet actuel : date=2025-01-17/articles.parquet
  - Nouveau du jour : date=2025-01-18/articles.parquet
  - PySpark lit : date=2025-01-17 + date=2025-01-18
```

---

## 🏗️ Architecture Proposée

### **Structure Parquet**

```
data/gold/
  ├── date=2025-01-15/
  │   └── articles.parquet          # Parquet actuel (J-1)
  ├── date=2025-01-16/
  │   └── articles.parquet          # Parquet du jour J
  ├── date=2025-01-17/
  │   └── articles.parquet          # Parquet du jour J+1
  └── ...
```

---

## 💻 Implémentation Stratégie

### **1. GoldParquetReader avec Accumulation**

```python
# src/spark/adapters/gold_parquet_reader.py (STRATÉGIE)
from pathlib import Path
from datetime import date, timedelta
from pyspark.sql import DataFrame
from src.spark.session import get_spark_session

class GoldParquetReader:
    """Lit GOLD Parquet avec accumulation (actuel + jour J)"""
    
    def __init__(self, base_path: str = "data/gold"):
        self.base_path = Path(base_path)
        self.spark = get_spark_session()
    
    def _get_latest_partition_date(self) -> date | None:
        """Trouve la dernière partition complète (parquet actuel)"""
        partitions = sorted([
            d for d in self.base_path.iterdir()
            if d.is_dir() and d.name.startswith("date=")
        ], reverse=True)
        
        if not partitions:
            return None
        
        # Extraire date de la partition (date=YYYY-MM-DD)
        latest = partitions[0]
        date_str = latest.name.replace("date=", "")
        try:
            return date.fromisoformat(date_str)
        except:
            return None
    
    def _get_today_partition_date(self) -> date:
        """Retourne la date du jour (nouveau parquet du jour J)"""
        return date.today()
    
    def read_accumulated(self, include_today: bool = True) -> DataFrame:
        """
        Lit Parquet actuel + Parquet du jour J (accumulation)
        
        Args:
            include_today: Si True, inclut le parquet du jour J
        
        Returns:
            DataFrame combiné (actuel + jour J)
        """
        latest_date = self._get_latest_partition_date()
        today_date = self._get_today_partition_date()
        
        paths_to_read = []
        
        # 1. Parquet actuel (dernière partition complète)
        if latest_date:
            latest_path = self.base_path / f"date={latest_date:%Y-%m-%d}" / "articles.parquet"
            if latest_path.exists():
                paths_to_read.append(str(latest_path))
        
        # 2. Parquet du jour J (si différent de l'actuel)
        if include_today and today_date != latest_date:
            today_path = self.base_path / f"date={today_date:%Y-%m-%d}" / "articles.parquet"
            if today_path.exists():
                paths_to_read.append(str(today_path))
        
        if not paths_to_read:
            # Retourner DataFrame vide avec même schéma
            return self.spark.createDataFrame([], schema=self._get_schema())
        
        # Lire et combiner tous les Parquet
        dfs = []
        for path in paths_to_read:
            df = self.spark.read.parquet(path)
            dfs.append(df)
        
        # Union de tous les DataFrames
        if len(dfs) == 1:
            return dfs[0]
        else:
            # Union all (combine tous les DataFrames)
            result = dfs[0]
            for df in dfs[1:]:
                result = result.union(df)
            return result
    
    def read_accumulated_all_dates(self) -> DataFrame:
        """
        Lit TOUS les Parquet (toutes les dates) - pour historique complet
        """
        # Lire toutes les partitions avec wildcard
        path_pattern = str(self.base_path / "date=*" / "articles.parquet")
        return self.spark.read.parquet(path_pattern)
    
    def _get_schema(self):
        """Retourne le schéma attendu des Parquet"""
        # Schéma GOLD (exemple)
        from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType
        
        return StructType([
            StructField("id", IntegerType(), True),
            StructField("source", StringType(), True),
            StructField("title", StringType(), True),
            StructField("content", StringType(), True),
            StructField("topic_1", StringType(), True),
            StructField("topic_1_score", FloatType(), True),
            StructField("topic_2", StringType(), True),
            StructField("topic_2_score", FloatType(), True),
            StructField("sentiment", StringType(), True),
            StructField("sentiment_score", FloatType(), True),
            # ... autres colonnes
        ])
```

---

### **2. Endpoint FastAPI avec Accumulation**

```python
# src/api/endpoints/analytics.py (STRATÉGIE)
from fastapi import APIRouter, Depends, Query
from src.spark.adapters.gold_parquet_reader import GoldParquetReader
from src.api.services.permission_service import check_permission, Zone, Action

router = APIRouter()

@router.get("/gold-accumulated")
@check_permission(zone=Zone.ANALYTICS, action=Action.READ)
async def get_gold_accumulated(
    include_today: bool = Query(True, description="Inclure parquet du jour J"),
    limit: int = Query(100, description="Limite de résultats")
):
    """
    GET /api/v1/analytics/gold-accumulated
    
    Retourne : Parquet actuel + Parquet du jour J (accumulation)
    """
    reader = GoldParquetReader()
    df = reader.read_accumulated(include_today=include_today)
    
    # Limiter résultats
    if limit > 0:
        df = df.limit(limit)
    
    # Convertir en JSON
    return df.toPandas().to_dict('records')

@router.get("/gold-all-dates")
@check_permission(zone=Zone.ANALYTICS, action=Action.READ)
async def get_gold_all_dates():
    """
    GET /api/v1/analytics/gold-all-dates
    
    Retourne : TOUS les Parquet (historique complet)
    """
    reader = GoldParquetReader()
    df = reader.read_accumulated_all_dates()
    
    return df.toPandas().to_dict('records')
```

---

### **3. Service PySpark avec Cache**

```python
# src/spark/services/gold_accumulation_service.py (STRATÉGIE)
from datetime import date
from pyspark.sql import DataFrame
from src.spark.adapters.gold_parquet_reader import GoldParquetReader

class GoldAccumulationService:
    """Service pour gérer l'accumulation Parquet avec cache"""
    
    def __init__(self):
        self.reader = GoldParquetReader()
        self._cached_df: DataFrame | None = None
        self._cached_date: date | None = None
    
    def get_accumulated_gold(self, force_refresh: bool = False) -> DataFrame:
        """
        Retourne Parquet actuel + Parquet du jour J (avec cache)
        
        Args:
            force_refresh: Force le rechargement (ignore cache)
        
        Returns:
            DataFrame accumulé
        """
        today = date.today()
        
        # Vérifier cache
        if not force_refresh and self._cached_df is not None and self._cached_date == today:
            return self._cached_df
        
        # Recharger
        df = self.reader.read_accumulated(include_today=True)
        
        # Cache le DataFrame (optionnel : peut être coûteux en mémoire)
        # self._cached_df = df.cache()
        # self._cached_date = today
        
        return df
    
    def get_stats_accumulated(self) -> dict:
        """Statistiques sur les données accumulées"""
        df = self.get_accumulated_gold()
        
        from pyspark.sql.functions import count, countDistinct
        
        stats = {
            "total_articles": df.count(),
            "unique_sources": df.select("source").distinct().count(),
            "date_range": {
                "min": df.select("collected_at").rdd.min()[0] if df.count() > 0 else None,
                "max": df.select("collected_at").rdd.max()[0] if df.count() > 0 else None
            }
        }
        
        return stats
```

---

## 🔄 Workflow Complet

### **Jour 1 (J1)**

```
1. Pipeline E1 génère :
   - data/gold/date=2025-01-16/articles.parquet (nouveau)

2. PySpark lit :
   - Parquet actuel : date=2025-01-15/articles.parquet
   - Parquet jour J : date=2025-01-16/articles.parquet
   - Résultat : Union des deux

3. Jury voit :
   - Parquet 1 (2025-01-15) + Parquet jour J (2025-01-16)
```

---

### **Jour 2 (J2)**

```
1. Pipeline E1 génère :
   - data/gold/date=2025-01-17/articles.parquet (nouveau)

2. PySpark lit :
   - Parquet actuel : date=2025-01-16/articles.parquet (devient le nouveau "actuel")
   - Parquet jour J : date=2025-01-17/articles.parquet
   - Résultat : Union des deux

3. Jury voit :
   - Parquet 2 (2025-01-16) + Parquet jour J (2025-01-17)
```

---

## 📊 Visualisation pour le Jury

### **Endpoint Statistiques**

```python
# src/api/endpoints/analytics.py (STRATÉGIE)
@router.get("/stats-accumulated")
@check_permission(zone=Zone.ANALYTICS, action=Action.READ)
async def get_stats_accumulated():
    """
    GET /api/v1/analytics/stats-accumulated
    
    Statistiques sur Parquet actuel + Parquet jour J
    """
    service = GoldAccumulationService()
    stats = service.get_stats_accumulated()
    
    # Ajouter info sur les partitions lues
    reader = GoldParquetReader()
    latest_date = reader._get_latest_partition_date()
    today_date = reader._get_today_partition_date()
    
    stats["partitions_read"] = {
        "current": str(latest_date) if latest_date else None,
        "today": str(today_date),
        "accumulation": f"{latest_date} + {today_date}" if latest_date and today_date != latest_date else str(today_date)
    }
    
    return stats
```

---

## ✅ Avantages

### **1. Accumulation Temporelle**
- ✅ **Vue unifiée** : Parquet actuel + nouveaux du jour
- ✅ **Historique** : Possibilité de lire toutes les dates
- ✅ **Flexibilité** : Lecture sélective par date

### **2. Performance**
- ✅ **Partitionnement** : Lecture optimisée par date
- ✅ **Union** : Combinaison efficace des DataFrames
- ✅ **Cache** : Option de mise en cache (si nécessaire)

### **3. Traçabilité**
- ✅ **Dates claires** : Jury voit quelles partitions sont lues
- ✅ **Statistiques** : Info sur les données accumulées
- ✅ **Logs** : Traçabilité des opérations

---

## 📋 Checklist Implémentation

### **Phase 1 : Reader avec Accumulation**
- [ ] `GoldParquetReader.read_accumulated()` : Lit actuel + jour J
- [ ] `_get_latest_partition_date()` : Trouve dernière partition
- [ ] `_get_today_partition_date()` : Date du jour
- [ ] Union des DataFrames

### **Phase 2 : Service d'Accumulation**
- [ ] `GoldAccumulationService` : Gestion accumulation
- [ ] Cache optionnel
- [ ] Statistiques accumulées

### **Phase 3 : Endpoints FastAPI**
- [ ] `GET /api/v1/analytics/gold-accumulated` : Vue accumulée
- [ ] `GET /api/v1/analytics/gold-all-dates` : Toutes les dates
- [ ] `GET /api/v1/analytics/stats-accumulated` : Statistiques

### **Phase 4 : Tests**
- [ ] Test lecture actuel + jour J
- [ ] Test accumulation multiple dates
- [ ] Test performance (grands volumes)

---

## 🎯 Résumé

### **Logique d'Accumulation**

```
Jour J :
  Parquet actuel (J-1) + Parquet jour J = Vue accumulée

Jour J+1 :
  Parquet actuel (J) + Parquet jour J+1 = Vue accumulée
```

### **Implémentation**

- ✅ **GoldParquetReader** : Lit plusieurs partitions
- ✅ **Union** : Combine les DataFrames
- ✅ **FastAPI** : Expose la vue accumulée
- ✅ **Statistiques** : Info sur les partitions lues

---

**Status** : 📋 **STRATÉGIE DÉFINIE - PRÊT POUR IMPLÉMENTATION**
