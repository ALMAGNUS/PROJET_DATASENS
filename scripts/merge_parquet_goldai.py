#!/usr/bin/env python3
"""
Script de Fusion Incrémentale Parquet GOLD → GoldAI
Fusionne les Parquet GOLD quotidiens en GoldAI pour l'IA/Mistral.
Architecture OOP/SOLID/DRY : séparation des responsabilités.
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from pyspark.sql import DataFrame
    from pyspark.sql.functions import (
        coalesce,
        col,
        countDistinct,
        length,
        lit,
        row_number,
        to_timestamp,
        trim,
        when,
    )
    from pyspark.sql.window import Window

    from src.config import get_settings
    from src.spark.adapters.gold_parquet_reader import GoldParquetReader
    from src.spark.session import close_spark_session, get_spark_session
except ImportError as e:
    print(f"ERREUR Import: {e}")
    sys.exit(1)

settings = get_settings()


class GoldAIMetadataManager:
    """Gestion des métadonnées GoldAI (SRP: metadata uniquement)"""

    def __init__(self, metadata_path: Path):
        self.metadata_path = metadata_path

    def load(self) -> dict:
        """Charge les métadonnées"""
        if not self.metadata_path.exists():
            return {"dates_included": [], "total_rows": 0, "last_merge": None, "version": 0}
        try:
            with open(self.metadata_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lecture metadata: {e}")
            return {"dates_included": [], "total_rows": 0, "last_merge": None, "version": 0}

    def save(self, metadata: dict) -> None:
        """Sauvegarde les métadonnées"""
        try:
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Erreur sauvegarde metadata: {e}")

    def get_new_dates(self, gold_dates: list[date], metadata: dict) -> list[date]:
        """Identifie les nouvelles dates à fusionner"""
        included = {
            date.fromisoformat(d) if isinstance(d, str) else d
            for d in metadata.get("dates_included", [])
        }
        return sorted([d for d in gold_dates if d not in included])


class GoldAIDeduplicator:
    """Déduplication par id (SRP: déduplication uniquement)"""

    @staticmethod
    def _non_empty_str(column_name: str, columns: list[str]):
        if column_name not in columns:
            return lit(None).cast("string")
        c = trim(col(column_name).cast("string"))
        return when(length(c) > 0, c).otherwise(lit(None).cast("string"))

    def harmonize_id(self, df: DataFrame) -> DataFrame:
        """
        Harmonise l'identifiant métier:
        - priorité à id
        - fallback fingerprint, puis url, puis title
        """
        cols = df.columns
        id_candidate = self._non_empty_str("id", cols)
        fp_candidate = self._non_empty_str("fingerprint", cols)
        url_candidate = self._non_empty_str("url", cols)
        title_candidate = self._non_empty_str("title", cols)
        stable_id = coalesce(id_candidate, fp_candidate, url_candidate, title_candidate)

        if "id" in cols:
            out = df.withColumn("id", coalesce(id_candidate, stable_id))
        else:
            out = df.withColumn("id", stable_id)

        null_after = out.filter(col("id").isNull()).count()
        if null_after > 0:
            print(f"ATTENTION: {null_after:,} lignes sans identifiant stable restent présentes.")
        return out

    @staticmethod
    def deduplicate(df: DataFrame, by: str = "id") -> DataFrame:
        """Déduplique par colonne (keep='last' basé sur collected_at)"""
        if by not in df.columns:
            print(f"Colonne '{by}' non trouvée, pas de déduplication")
            return df

        print(f"Déduplication par '{by}' (keep='last')...")
        before_count = df.count()

        order_col = (
            coalesce(
                to_timestamp(col("collected_at"), "yyyy-MM-dd HH:mm:ss"),
                to_timestamp(lit("1970-01-01 00:00:00"), "yyyy-MM-dd HH:mm:ss"),
            )
            if "collected_at" in df.columns
            else lit(1)
        )

        window = Window.partitionBy(by).orderBy(order_col.desc())
        result = df.withColumn("_rn", row_number().over(window)).filter(col("_rn") == 1).drop("_rn")

        after_count = result.count()
        print(
            f"{before_count - after_count:,} doublons supprimés ({before_count:,} -> {after_count:,} lignes)"
        )
        return result


class GoldAIDataLoader:
    """Chargement des données (SRP: lecture uniquement)"""

    def __init__(self, gold_reader: GoldParquetReader, spark):
        self.gold_reader = gold_reader
        self.spark = spark

    def load_existing(self, goldai_path: Path) -> DataFrame | None:
        """Charge GoldAI existant"""
        merged_path = goldai_path / "merged_all_dates.parquet"
        if not merged_path.exists():
            return None
        try:
            print(f"Chargement GoldAI existant: {merged_path}")
            df = self.spark.read.parquet(str(merged_path))
            print(f"{df.count():,} lignes chargées")
            return df
        except Exception as e:
            print(f"Erreur chargement GoldAI existant: {e}")
            return None

    def load_gold_dates(self, dates: list[date]) -> list[DataFrame]:
        """Charge les dates GOLD"""
        dfs = []
        for target_date in dates:
            try:
                print(f"Ajout GOLD date {target_date:%Y-%m-%d}...")
                df = self.gold_reader.read_gold(date=target_date)
                count = df.count()
                print(f"{count:,} lignes")
                dfs.append(df)
            except Exception as e:
                print(f"Erreur lecture GOLD {target_date:%Y-%m-%d}: {e}")
        return dfs


class GoldAIDataMerger:
    """Fusion de DataFrames (SRP: union uniquement)"""

    @staticmethod
    def union_all(dfs: list[DataFrame]) -> DataFrame:
        """Union de tous les DataFrames avec gestion schémas"""
        if not dfs:
            raise ValueError("Aucune donnée à fusionner")
        print(f"Fusion de {len(dfs)} DataFrames...")
        result = dfs[0]
        for df in dfs[1:]:
            try:
                result = result.union(df)
            except Exception:
                try:
                    result = result.unionByName(df, allowMissingColumns=True)
                except Exception as e:
                    print(f"Erreur union: {e}")
        return result


class GoldAISaver:
    """Sauvegarde GoldAI (SRP: écriture uniquement)
    Utilise pandas/pyarrow pour l'écriture (évite HADOOP_HOME sous Windows).
    """

    def __init__(self, goldai_base: Path):
        self.goldai_base = goldai_base
        self.goldai_base.mkdir(parents=True, exist_ok=True)

    def _spark_to_pandas(self, df: DataFrame):
        """Convertit Spark DataFrame en pandas (évite Spark write = Hadoop sur Windows)"""
        return df.toPandas()

    def save(self, df: DataFrame, target_date: date, version: int = 0) -> None:
        """Sauvegarde partition incrémentale + fusion complète (pandas/pyarrow)"""
        import shutil

        pdf = self._spark_to_pandas(df)
        count = len(pdf)

        # Partition incrémentale
        partition_dir = self.goldai_base / f"date={target_date:%Y-%m-%d}"
        partition_dir.mkdir(parents=True, exist_ok=True)
        partition_path = (partition_dir / "goldai.parquet").resolve()

        # Nettoyer résidu d'un échec Spark (Spark crée goldai.parquet/ comme dossier)
        if partition_path.exists():
            try:
                if partition_path.is_dir():
                    shutil.rmtree(partition_path)
                else:
                    partition_path.unlink()
            except (PermissionError, OSError):
                pass

        print(f"Sauvegarde partition incrémentale: {partition_path}")
        pdf.to_parquet(str(partition_path), index=False)
        print(f"{count:,} lignes sauvegardées")

        # Fusion complète avec backup
        merged_path = self.goldai_base / "merged_all_dates.parquet"
        if merged_path.exists() and version > 0:
            backup_path = self.goldai_base / f"merged_all_dates_v{version}.parquet"
            print(f"Backup version précédente: {backup_path}")
            shutil.copy2(merged_path, backup_path)

        print(f"Sauvegarde fusion complète: {merged_path}")
        pdf.to_parquet(str(merged_path.resolve()), index=False)
        print(f"{count:,} lignes sauvegardées")


class GoldAIMerger:
    """Orchestrateur principal (OCP: extensible via composition)"""

    def __init__(self, gold_path: str | None = None, goldai_path: str | None = None):
        self.gold_reader = GoldParquetReader(base_path=gold_path)
        self.goldai_base = Path(goldai_path or settings.goldai_base_path)
        self.spark = get_spark_session()

        # Composition: délégation des responsabilités
        self.metadata_mgr = GoldAIMetadataManager(self.goldai_base / "metadata.json")
        self.loader = GoldAIDataLoader(self.gold_reader, self.spark)
        self.merger = GoldAIDataMerger()
        self.deduplicator = GoldAIDeduplicator()
        self.saver = GoldAISaver(self.goldai_base)

    @staticmethod
    def _distinct_id_count(df: DataFrame | None) -> int:
        if df is None or "id" not in df.columns:
            return 0
        non_null = df.filter(col("id").isNotNull())
        return int(non_null.select(countDistinct("id").alias("n")).collect()[0]["n"])

    def run_merge(self, force_full: bool = False) -> dict:
        """Exécute la fusion incrémentale complète"""
        print("\n" + "=" * 70)
        print("FUSION INCREMENTALE PARQUET GOLD -> GOLDAI")
        print("=" * 70)

        metadata = self.metadata_mgr.load()
        print(
            f"\nMetadonnees GoldAI: {len(metadata.get('dates_included', []))} dates, "
            f"{metadata.get('total_rows', 0):,} lignes, version {metadata.get('version', 0)}"
        )

        gold_dates = self.gold_reader.get_available_dates()
        print(f"\nDates GOLD disponibles: {len(gold_dates)}")
        if gold_dates:
            print(f"Periode GOLD: {gold_dates[0]:%Y-%m-%d} -> {gold_dates[-1]:%Y-%m-%d}")

        new_dates = (
            gold_dates if force_full else self.metadata_mgr.get_new_dates(gold_dates, metadata)
        )
        print(
            f"\n{'Mode FORCE FULL' if force_full else 'Nouvelles dates a fusionner'}: {len(new_dates)}"
        )
        if new_dates:
            if len(new_dates) <= 10:
                print("Dates cibles: " + ", ".join(f"{d:%Y-%m-%d}" for d in new_dates))
            else:
                first = ", ".join(f"{d:%Y-%m-%d}" for d in new_dates[:5])
                last = ", ".join(f"{d:%Y-%m-%d}" for d in new_dates[-5:])
                print(f"Dates cibles (aperçu): {first} ... {last}")

        if not new_dates and not force_full:
            print("\nAucune nouvelle date a fusionner. GoldAI a jour.")
            return metadata

        # Chargement données
        dfs_to_merge = []
        existing_df = None
        existing_rows = 0
        existing_unique_ids = 0
        if not force_full:
            existing_df = self.loader.load_existing(self.goldai_base)
            if existing_df:
                existing_rows = existing_df.count()
                existing_unique_ids = self._distinct_id_count(existing_df)
                print(f"Ajout GoldAI existant: {existing_rows:,} lignes")
                dfs_to_merge.append(existing_df)

        new_dfs = self.loader.load_gold_dates(new_dates)
        dfs_to_merge.extend(new_dfs)

        # Diagnostics explicites: combien de nouveaux IDs réels apportent les dates du jour
        if new_dfs:
            new_union = self.merger.union_all(new_dfs)
            new_rows = new_union.count()
            new_unique_ids = self._distinct_id_count(new_union)
            print(f"IDs distincts dans les nouvelles dates: {new_unique_ids:,}")

            if existing_df and "id" in existing_df.columns and "id" in new_union.columns:
                existing_ids = existing_df.select("id").dropDuplicates()
                new_ids = new_union.select("id").dropDuplicates()
                overlap = new_ids.join(existing_ids, on="id", how="inner").count()
                new_unique_vs_existing = max(new_unique_ids - overlap, 0)
                print(f"IDs déjà présents dans GoldAI existant: {overlap:,}")
                print(f"Nouveaux IDs potentiels (vs GoldAI existant): {new_unique_vs_existing:,}")
            else:
                print("Nouveaux IDs potentiels (vs GoldAI existant): n/a")
            print(f"Lignes brutes nouvelles dates: {new_rows:,}")

        # Fusion + déduplication
        merged_df = self.merger.union_all(dfs_to_merge)
        merged_df = self.deduplicator.harmonize_id(merged_df)
        merged_df = self.deduplicator.deduplicate(merged_df, by="id")
        total_rows = merged_df.count()
        total_unique_ids = self._distinct_id_count(merged_df)
        print(f"IDs distincts après fusion: {total_unique_ids:,}")
        if existing_rows > 0:
            growth_rows = total_rows - existing_rows
            growth_ids = total_unique_ids - existing_unique_ids
            print(f"Croissance GoldAI (lignes): {growth_rows:+,}")
            print(f"Croissance GoldAI (IDs distincts): {growth_ids:+,}")
            if growth_ids <= 0:
                print(
                    "AVERTISSEMENT: aucune croissance d'IDs GoldAI. "
                    "Si la DB augmente, envisager un --force-full pour recalage."
                )

        # Sauvegarde
        latest_date = (
            max(new_dates) if new_dates else gold_dates[-1] if gold_dates else date.today()
        )
        new_version = metadata.get("version", 0) + 1
        self.saver.save(merged_df, latest_date, version=new_version)

        # Mise à jour métadonnées
        all_dates = sorted(
            set(metadata.get("dates_included", [])) | {d.isoformat() for d in gold_dates}
        )
        new_metadata = {
            "dates_included": all_dates,
            "total_rows": total_rows,
            "last_merge": datetime.now().isoformat(),
            "version": new_version,
            "last_date_merged": latest_date.isoformat(),
        }
        self.metadata_mgr.save(new_metadata)

        # Stats finales
        print("\n" + "=" * 70)
        print("FUSION TERMINEE")
        print("=" * 70)
        print(f"Total lignes GoldAI: {total_rows:,}")
        print(f"Dates incluses: {len(all_dates)}")
        print(f"Version: {new_version}")
        print("Fichiers sauvegardes:")
        print(f"  - {self.goldai_base / f'date={latest_date:%Y-%m-%d}' / 'goldai.parquet'}")
        print(f"  - {self.goldai_base / 'merged_all_dates.parquet'}")

        return new_metadata


def main():
    """Point d'entrée principal"""
    import argparse

    parser = argparse.ArgumentParser(description="Fusion incrémentale Parquet GOLD -> GoldAI")
    parser.add_argument(
        "--force-full", action="store_true", help="Refaire fusion complète depuis zéro"
    )
    parser.add_argument("--gold-path", type=str, default=None, help="Chemin vers Parquet GOLD")
    parser.add_argument("--goldai-path", type=str, default=None, help="Chemin vers GoldAI")

    args = parser.parse_args()

    try:
        merger = GoldAIMerger(gold_path=args.gold_path, goldai_path=args.goldai_path)
        merger.run_merge(force_full=args.force_full)
        print("\nScript terminé avec succès")
        return 0
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        close_spark_session()


if __name__ == "__main__":
    sys.exit(main())
