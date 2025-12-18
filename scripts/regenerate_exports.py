#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Régénère les exports RAW/SILVER/GOLD avec les nouvelles données"""
import sys
import os
from pathlib import Path
from datetime import date

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from aggregator import DataAggregator
from exporter import GoldExporter

if __name__ == "__main__":
    db_path = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))
    
    print("\n" + "="*80)
    print("[RÉGÉNÉRATION] EXPORTS RAW/SILVER/GOLD")
    print("="*80)
    
    agg = DataAggregator(db_path)
    exp = GoldExporter()
    
    # RAW
    print("\n[RAW] Génération...")
    df_raw = agg.aggregate_raw()
    r_raw = exp.export_raw(df_raw)
    print(f"   OK: {r_raw['csv']} ({r_raw['rows']} rows)")
    
    # SILVER
    print("\n[SILVER] Génération...")
    df_silver = agg.aggregate_silver()
    r_silver = exp.export_silver(df_silver)
    print(f"   OK: {r_silver['csv']} ({r_silver['rows']} rows)")
    
    # GOLD
    print("\n[GOLD] Génération...")
    df_gold = agg.aggregate()
    r_gold = exp.export_all(df_gold, date.today())
    print(f"   OK Parquet: {r_gold['parquet']}")
    print(f"   OK CSV: {r_gold['csv']} ({r_gold['rows']} rows)")
    
    # Statistiques sentiment
    if 'sentiment' in df_gold.columns:
        sentiment_counts = df_gold['sentiment'].value_counts()
        print(f"\n[SENTIMENT] Distribution dans GOLD:")
        for sent, count in sentiment_counts.items():
            pct = (count / len(df_gold)) * 100
            emoji = {'positif': '✅', 'neutre': '⚪', 'négatif': '❌'}.get(sent, '📊')
            print(f"   {emoji} {sent:10s}: {count:4d} articles ({pct:5.1f}%)")
    
    agg.close()
    print("\n" + "="*80)
    print("[OK] EXPORTS RÉGÉNÉRÉS")
    print("="*80 + "\n")
