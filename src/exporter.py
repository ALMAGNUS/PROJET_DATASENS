"""Exporter - RAW/SILVER/GOLD (CSV + Parquet)"""
import pandas as pd
from pathlib import Path
from datetime import date

class GoldExporter:
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path('data/gold')
        self.export_dir = Path('exports')
        self.export_dir.mkdir(exist_ok=True)
    
    def export_raw(self, df: pd.DataFrame) -> dict:
        """Export RAW: données brutes"""
        csv_file = self.export_dir / 'raw.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8')
        return {'csv': csv_file, 'rows': len(df), 'columns': list(df.columns)}
    
    def export_silver(self, df: pd.DataFrame) -> dict:
        """Export SILVER: RAW + topics"""
        csv_file = self.export_dir / 'silver.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8')
        return {'csv': csv_file, 'rows': len(df), 'columns': list(df.columns)}
    
    def export_all(self, df: pd.DataFrame, partition_date: date = None) -> dict:
        """Export GOLD: SILVER + sentiment (Parquet + CSV)"""
        d = partition_date or date.today()
        p_path = self.base_dir / f"date={d:%Y-%m-%d}"
        p_path.mkdir(parents=True, exist_ok=True)
        parquet = p_path / 'articles.parquet'
        csv = self.export_dir / 'gold.csv'
        df.to_parquet(parquet, index=False, engine='pyarrow')
        df.to_csv(csv, index=False, encoding='utf-8')
        return {'parquet': parquet, 'csv': csv, 'rows': len(df), 'columns': list(df.columns)}

