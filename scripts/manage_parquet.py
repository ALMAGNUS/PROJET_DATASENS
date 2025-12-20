#!/usr/bin/env python3
"""
Script de Gestion Parquet - PySpark
=====================================
Permet de manipuler les fichiers Parquet GOLD :
- Lire et afficher les données
- Modifier/compléter les données
- Supprimer des lignes/colonnes
- Créer de nouveaux fichiers Parquet
"""

import sys
from pathlib import Path
from datetime import date
from typing import Optional

# Ajouter racine projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

try:
    from spark.session import get_spark_session, close_spark_session
    from spark.adapters import GoldParquetReader
    from spark.processors import GoldDataProcessor
    from pyspark.sql import DataFrame
    from pyspark.sql.functions import col, when, lit
    print("OK Imports reussis")
except ImportError as e:
    print(f"ERREUR Import: {e}")
    sys.exit(1)


def show_parquet_info(reader: GoldParquetReader):
    """Affiche les informations sur les fichiers Parquet disponibles"""
    print("\n" + "=" * 70)
    print("INFORMATIONS PARQUET GOLD")
    print("=" * 70)
    
    dates = reader.get_available_dates()
    print(f"\nDates disponibles: {len(dates)}")
    for d in dates:
        partition_path = reader.base_path / f"date={d:%Y-%m-%d}" / "articles.parquet"
        if partition_path.exists():
            import pyarrow.parquet as pq
            try:
                num_rows = pq.ParquetFile(partition_path).metadata.num_rows
                size_mb = partition_path.stat().st_size / (1024 * 1024)
                print(f"  - {d:%Y-%m-%d}: {num_rows:,} lignes ({size_mb:.2f} MB)")
            except Exception as e:
                print(f"  - {d:%Y-%m-%d}: ERREUR lecture ({e})")
    
    print()


def read_parquet(reader: GoldParquetReader, target_date: Optional[date] = None) -> DataFrame:
    """Lit un fichier Parquet"""
    try:
        if target_date:
            print(f"Lecture Parquet pour date: {target_date:%Y-%m-%d}")
            df = reader.read_gold(date=target_date)
        else:
            print("Lecture Parquet pour toutes les dates")
            df = reader.read_gold()
        
        print(f"OK: {df.count():,} lignes, {len(df.columns)} colonnes")
        return df
    except FileNotFoundError as e:
        print(f"ERREUR: {e}")
        return None
    except Exception as e:
        print(f"ERREUR: {e}")
        return None


def show_dataframe_info(df: DataFrame):
    """Affiche les informations sur un DataFrame"""
    if df is None:
        return
    
    print("\n" + "=" * 70)
    print("INFORMATIONS DATAFRAME")
    print("=" * 70)
    print(f"Lignes: {df.count():,}")
    print(f"Colonnes: {len(df.columns)}")
    print(f"\nColonnes disponibles:")
    for i, col_name in enumerate(df.columns, 1):
        print(f"  {i}. {col_name}")
    
    # Afficher schéma
    print("\nSchema:")
    df.printSchema()
    
    # Afficher quelques lignes
    print("\nPremieres lignes (5):")
    df.show(5, truncate=False)


def filter_dataframe(df: DataFrame, condition: str) -> DataFrame:
    """Filtre un DataFrame avec une condition SQL"""
    try:
        # Détecter si c'est juste une valeur (pas d'opérateur SQL)
        # Si pas de =, <, >, !=, LIKE, IN, etc., essayer de deviner
        condition_clean = condition.strip()
        
        # Si c'est juste une valeur sans opérateur, essayer de deviner la colonne
        if not any(op in condition_clean for op in ['=', '<', '>', '!=', '<>', 'LIKE', 'IN', 'IS', 'BETWEEN']):
            # Essayer avec sentiment (le plus commun)
            if condition_clean.lower() in ['positif', 'negatif', 'neutre', 'positive', 'negative', 'neutral']:
                condition_clean = f"sentiment = '{condition_clean}'"
                print(f"INFO: Condition interpretee comme: {condition_clean}")
            # Essayer avec source
            elif condition_clean in df.columns:
                print(f"ERREUR: Colonne '{condition_clean}' detectee mais valeur manquante.")
                print(f"       Utilisez: {condition_clean} = 'valeur'")
                return df
            else:
                # Essayer avec sentiment par défaut
                condition_clean = f"sentiment = '{condition_clean}'"
                print(f"INFO: Condition interpretee comme: {condition_clean}")
        
        # Créer vue temporaire
        df.createOrReplaceTempView("temp_df")
        
        # Exécuter requête SQL
        spark = get_spark_session()
        filtered = spark.sql(f"SELECT * FROM temp_df WHERE {condition_clean}")
        
        print(f"OK: {filtered.count():,} lignes apres filtre")
        return filtered
    except Exception as e:
        print(f"ERREUR filtre: {e}")
        print("\nAIDE: La condition SQL doit etre complete, par exemple:")
        print("  - sentiment = 'positif'")
        print("  - source = 'google_news_rss'")
        print("  - sentiment_score > 0.7")
        print("  - sentiment IN ('positif', 'negatif')")
        return df


def modify_dataframe(df: DataFrame, column: str, old_value: str, new_value: str) -> DataFrame:
    """Modifie une valeur dans un DataFrame"""
    try:
        modified = df.withColumn(
            column,
            when(col(column) == old_value, lit(new_value))
            .otherwise(col(column))
        )
        print(f"OK: Modification appliquee (colonne: {column})")
        return modified
    except Exception as e:
        print(f"ERREUR modification: {e}")
        return df


def add_column(df: DataFrame, column_name: str, default_value) -> DataFrame:
    """Ajoute une colonne au DataFrame"""
    try:
        modified = df.withColumn(column_name, lit(default_value))
        print(f"OK: Colonne '{column_name}' ajoutee avec valeur: {default_value}")
        return modified
    except Exception as e:
        print(f"ERREUR ajout colonne: {e}")
        return df


def delete_rows(df: DataFrame, condition: str) -> DataFrame:
    """Supprime des lignes selon une condition"""
    try:
        # Détecter si c'est juste une valeur (pas d'opérateur SQL)
        condition_clean = condition.strip()
        
        # Si c'est juste une valeur sans opérateur, essayer de deviner la colonne
        if not any(op in condition_clean for op in ['=', '<', '>', '!=', '<>', 'LIKE', 'IN', 'IS', 'BETWEEN']):
            # Essayer avec sentiment (le plus commun)
            if condition_clean.lower() in ['positif', 'negatif', 'neutre', 'positive', 'negative', 'neutral']:
                condition_clean = f"sentiment = '{condition_clean}'"
                print(f"INFO: Condition interpretee comme: {condition_clean}")
            else:
                # Essayer avec sentiment par défaut
                condition_clean = f"sentiment = '{condition_clean}'"
                print(f"INFO: Condition interpretee comme: {condition_clean}")
        
        # Créer vue temporaire
        df.createOrReplaceTempView("temp_df")
        
        # Exécuter requête SQL avec NOT condition
        spark = get_spark_session()
        filtered = spark.sql(f"SELECT * FROM temp_df WHERE NOT ({condition_clean})")
        
        deleted_count = df.count() - filtered.count()
        print(f"OK: {deleted_count:,} lignes supprimees")
        return filtered
    except Exception as e:
        print(f"ERREUR suppression: {e}")
        print("\nAIDE: La condition SQL doit etre complete, par exemple:")
        print("  - sentiment = 'neutre'")
        print("  - sentiment_score < 0.3")
        print("  - source = 'zzdb_csv'")
        return df


def save_parquet(df: DataFrame, output_path: str, partition_date: Optional[date] = None):
    """Sauvegarde un DataFrame en Parquet"""
    try:
        path_obj = Path(output_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        if partition_date:
            # Sauvegarder avec partitionnement par date
            partition_path = path_obj.parent / f"date={partition_date:%Y-%m-%d}"
            partition_path.mkdir(parents=True, exist_ok=True)
            final_path = partition_path / path_obj.name
        else:
            final_path = path_obj
        
        df.write.mode("overwrite").parquet(str(final_path))
        print(f"OK: Parquet sauvegarde dans {final_path}")
        print(f"    {df.count():,} lignes, {len(df.columns)} colonnes")
    except Exception as e:
        print(f"ERREUR sauvegarde: {e}")


def interactive_menu():
    """Menu interactif pour manipuler les Parquet"""
    reader = GoldParquetReader()
    processor = GoldDataProcessor()
    current_df: Optional[DataFrame] = None
    
    print("\n" + "=" * 70)
    print("GESTION PARQUET GOLD - MENU INTERACTIF")
    print("=" * 70)
    
    while True:
        print("\nOptions disponibles:")
        print("  1. Afficher informations Parquet disponibles")
        print("  2. Lire Parquet (toutes dates)")
        print("  3. Lire Parquet (date specifique)")
        print("  4. Afficher informations DataFrame actuel")
        print("  5. Filtrer DataFrame (condition SQL)")
        print("  6. Modifier valeur (colonne, ancienne valeur, nouvelle valeur)")
        print("  7. Ajouter colonne")
        print("  8. Supprimer lignes (condition SQL)")
        print("  9. Sauvegarder DataFrame en Parquet")
        print("  10. Appliquer traitement (aggregation, statistiques)")
        print("  0. Quitter")
        
        choice = input("\nVotre choix: ").strip()
        
        if choice == "0":
            print("Au revoir!")
            break
        elif choice == "1":
            show_parquet_info(reader)
        elif choice == "2":
            current_df = read_parquet(reader)
        elif choice == "3":
            date_str = input("Date (YYYY-MM-DD): ").strip()
            try:
                target_date = date.fromisoformat(date_str)
                current_df = read_parquet(reader, target_date)
            except ValueError:
                print("ERREUR: Format date invalide (utiliser YYYY-MM-DD)")
        elif choice == "4":
            show_dataframe_info(current_df)
        elif choice == "5":
            if current_df is None:
                print("ERREUR: Aucun DataFrame charge")
                continue
            condition = input("Condition SQL (ex: sentiment = 'positif'): ").strip()
            current_df = filter_dataframe(current_df, condition)
        elif choice == "6":
            if current_df is None:
                print("ERREUR: Aucun DataFrame charge")
                continue
            column = input("Nom colonne: ").strip()
            old_value = input("Ancienne valeur: ").strip()
            new_value = input("Nouvelle valeur: ").strip()
            current_df = modify_dataframe(current_df, column, old_value, new_value)
        elif choice == "7":
            if current_df is None:
                print("ERREUR: Aucun DataFrame charge")
                continue
            column_name = input("Nom nouvelle colonne: ").strip()
            default_value = input("Valeur par defaut: ").strip()
            # Essayer de convertir en nombre si possible
            try:
                if '.' in default_value:
                    default_value = float(default_value)
                else:
                    default_value = int(default_value)
            except ValueError:
                pass  # Garder comme string
            current_df = add_column(current_df, column_name, default_value)
        elif choice == "8":
            if current_df is None:
                print("ERREUR: Aucun DataFrame charge")
                continue
            print("\nExemples de conditions SQL:")
            print("  - sentiment = 'neutre'")
            print("  - sentiment_score < 0.3")
            print("  - source = 'zzdb_csv'")
            print("\nAstuce: Vous pouvez aussi entrer juste 'neutre' (sera interprete comme sentiment = 'neutre')")
            condition = input("\nCondition SQL pour supprimer: ").strip()
            current_df = delete_rows(current_df, condition)
        elif choice == "9":
            if current_df is None:
                print("ERREUR: Aucun DataFrame charge")
                continue
            output_path = input("Chemin sortie (ex: data/gold/custom/articles.parquet): ").strip()
            partition_date_str = input("Date partition (YYYY-MM-DD, optionnel): ").strip()
            partition_date = None
            if partition_date_str:
                try:
                    partition_date = date.fromisoformat(partition_date_str)
                except ValueError:
                    print("ERREUR: Format date invalide")
                    continue
            save_parquet(current_df, output_path, partition_date)
        elif choice == "10":
            if current_df is None:
                print("ERREUR: Aucun DataFrame charge")
                continue
            print("\nTraitements disponibles:")
            print("  a. Aggregation par sentiment")
            print("  b. Aggregation par source")
            print("  c. Distribution sentiment")
            print("  d. Statistiques generales")
            sub_choice = input("Votre choix: ").strip().lower()
            if sub_choice == "a":
                result = processor.aggregate_by_sentiment(current_df)
                result.show(20, truncate=False)
            elif sub_choice == "b":
                result = processor.aggregate_by_source(current_df)
                result.show(20, truncate=False)
            elif sub_choice == "c":
                result = processor.get_sentiment_distribution(current_df)
                result.show(20, truncate=False)
            elif sub_choice == "d":
                stats = processor.get_statistics(current_df)
                print("\nStatistiques:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            else:
                print("ERREUR: Choix invalide")
        else:
            print("ERREUR: Choix invalide")


if __name__ == "__main__":
    try:
        # Initialiser SparkSession
        spark = get_spark_session()
        print(f"SparkSession cree: {spark.sparkContext.master}")
        
        # Lancer menu interactif
        interactive_menu()
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Fermer SparkSession
        close_spark_session()
        print("\nSparkSession fermee")
