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
    from pyspark.sql.functions import coalesce, col, lit, row_number, to_timestamp
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
        included = {date.fromisoformat(d) if isinstance(d, str) else d
                   for d in metadata.get("dates_included", [])}
        return sorted([d for d in gold_dates if d not in included])


class GoldAIDeduplicator:
    """Déduplication par id (SRP: déduplication uniquement)"""

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
                to_timestamp(lit("1970-01-01 00:00:00"), "yyyy-MM-dd HH:mm:ss")
            ) if "collected_at" in df.columns else lit(1)
        )

        window = Window.partitionBy(by).orderBy(order_col.desc())
        result = df.withColumn("_rn", row_number().over(window)) \
                  .filter(col("_rn") == 1) \
                  .drop("_rn")

        after_count = result.count()
        print(f"{before_count - after_count:,} doublons supprimés ({before_count:,} -> {after_count:,} lignes)")
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
    """Sauvegarde GoldAI (SRP: écriture uniquement)"""

    def __init__(self, goldai_base: Path):
        self.goldai_base = goldai_base
        self.goldai_base.mkdir(parents=True, exist_ok=True)

    def save(self, df: DataFrame, target_date: date, version: int = 0) -> None:
        """Sauvegarde partition incrémentale + fusion complète"""
        import shutil

        # Partition incrémentale
        partition_dir = self.goldai_base / f"date={target_date:%Y-%m-%d}"
        partition_dir.mkdir(parents=True, exist_ok=True)
        partition_path = partition_dir / "goldai.parquet"

        print(f"Sauvegarde partition incrémentale: {partition_path}")
        df.write.mode("overwrite").parquet(str(partition_path))
        count = df.count()
        print(f"{count:,} lignes sauvegardées")

        # Fusion complète avec backup
        merged_path = self.goldai_base / "merged_all_dates.parquet"
        if merged_path.exists() and version > 0:
            backup_path = self.goldai_base / f"merged_all_dates_v{version}.parquet"
            print(f"Backup version précédente: {backup_path}")
            shutil.copy2(merged_path, backup_path)

        print(f"Sauvegarde fusion complète: {merged_path}")
        df.write.mode("overwrite").parquet(str(merged_path))
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

    def run_merge(self, force_full: bool = False) -> dict:
        """Exécute la fusion incrémentale complète"""
        print("\n" + "=" * 70)
        print("FUSION INCREMENTALE PARQUET GOLD -> GOLDAI")
        print("=" * 70)

        metadata = self.metadata_mgr.load()
        print(f"\nMetadonnees GoldAI: {len(metadata.get('dates_included', []))} dates, "
              f"{metadata.get('total_rows', 0):,} lignes, version {metadata.get('version', 0)}")

        gold_dates = self.gold_reader.get_available_dates()
        print(f"\nDates GOLD disponibles: {len(gold_dates)}")
        for d in gold_dates:
            print(f"  - {d:%Y-%m-%d}")

        new_dates = gold_dates if force_full else self.metadata_mgr.get_new_dates(gold_dates, metadata)
        print(f"\n{'Mode FORCE FULL' if force_full else 'Nouvelles dates a fusionner'}: {len(new_dates)}")
        for d in new_dates:
            print(f"  - {d:%Y-%m-%d}")

        if not new_dates and not force_full:
            print("\nAucune nouvelle date a fusionner. GoldAI a jour.")
            return metadata

        # Chargement données
        dfs_to_merge = []
        if not force_full:
            existing_df = self.loader.load_existing(self.goldai_base)
            if existing_df:
                print(f"Ajout GoldAI existant: {existing_df.count():,} lignes")
                dfs_to_merge.append(existing_df)

        dfs_to_merge.extend(self.loader.load_gold_dates(new_dates))

        # Fusion + déduplication
        merged_df = self.merger.union_all(dfs_to_merge)
        merged_df = self.deduplicator.deduplicate(merged_df, by="id")
        total_rows = merged_df.count()

        # Sauvegarde
        latest_date = max(new_dates) if new_dates else gold_dates[-1] if gold_dates else date.today()
        new_version = metadata.get("version", 0) + 1
        self.saver.save(merged_df, latest_date, version=new_version)

        # Mise à jour métadonnées
        all_dates = sorted(set(metadata.get("dates_included", [])) | {d.isoformat() for d in gold_dates})
        new_metadata = {
            "dates_included": all_dates,
            "total_rows": total_rows,
            "last_merge": datetime.now().isoformat(),
            "version": new_version,
            "last_date_merged": latest_date.isoformat()
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
    parser.add_argument("--force-full", action="store_true", help="Refaire fusion complète depuis zéro")
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
