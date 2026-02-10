"""Exporter - RAW/SILVER/GOLD (CSV + Parquet)"""
from datetime import date
from pathlib import Path

import pandas as pd


class GoldExporter:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path("data/gold")
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)

    def export_raw(self, df: pd.DataFrame) -> dict:
        """Export RAW: données brutes"""
        csv_file = self.export_dir / "raw.csv"
        df.to_csv(csv_file, index=False, encoding="utf-8")
        return {"csv": csv_file, "rows": len(df), "columns": list(df.columns)}

    def export_silver(self, df: pd.DataFrame) -> dict:
        """Export SILVER: RAW + topics"""
        csv_file = self.export_dir / "silver.csv"
        df.to_csv(csv_file, index=False, encoding="utf-8")
        return {"csv": csv_file, "rows": len(df), "columns": list(df.columns)}

    def export_all(self, df: pd.DataFrame, partition_date: date | None = None) -> dict:
        """Export GOLD: SILVER + sentiment (Parquet + CSV) avec partitionnement par date et source"""
        d = partition_date or date.today()

        # Partitionnement principal par date
        p_path = self.base_dir / f"date={d:%Y-%m-%d}"
        p_path.mkdir(parents=True, exist_ok=True)

        # Export global (toutes sources)
        parquet = p_path / "articles.parquet"
        csv = self.export_dir / "gold.csv"
        df.to_parquet(parquet, index=False, engine="pyarrow")
        df.to_csv(csv, index=False, encoding="utf-8")

        # Partitionnement spécifique ZZDB (isolation données synthétiques)
        if "source" in df.columns:
            # zzdb_synthetic
            zzdb_synthetic_df = df[df["source"] == "zzdb_synthetic"].copy()
            if len(zzdb_synthetic_df) > 0:
                zzdb_synthetic_path = p_path / "source=zzdb_synthetic"
                zzdb_synthetic_path.mkdir(exist_ok=True)
                zzdb_synthetic_parquet = zzdb_synthetic_path / "zzdb_articles.parquet"
                zzdb_synthetic_df.to_parquet(zzdb_synthetic_parquet, index=False, engine="pyarrow")

            # zzdb_csv
            zzdb_csv_df = df[df["source"] == "zzdb_csv"].copy()
            if len(zzdb_csv_df) > 0:
                zzdb_csv_path = p_path / "source=zzdb_csv"
                zzdb_csv_path.mkdir(exist_ok=True)
                zzdb_csv_parquet = zzdb_csv_path / "zzdb_csv_articles.parquet"
                zzdb_csv_df.to_parquet(zzdb_csv_parquet, index=False, engine="pyarrow")

        return {"parquet": parquet, "csv": csv, "rows": len(df), "columns": list(df.columns)}
