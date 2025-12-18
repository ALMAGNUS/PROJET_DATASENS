#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exemples d'exploration des datasets avec Python"""
import pandas as pd
from pathlib import Path
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    """Exemples d'exploration des datasets"""
    exports_dir = Path(__file__).parent.parent / 'exports'
    
    print("\n" + "="*80)
    print("[EXEMPLES] EXPLORATION DES DATASETS AVEC PYTHON")
    print("="*80)
    
    # Charger les datasets
    print("\n[1] Chargement des datasets...")
    df_raw = pd.read_csv(exports_dir / 'raw.csv', encoding='utf-8')
    df_silver = pd.read_csv(exports_dir / 'silver.csv', encoding='utf-8')
    df_gold = pd.read_csv(exports_dir / 'gold.csv', encoding='utf-8')
    
    print(f"   ✅ RAW:   {len(df_raw):,} lignes, {len(df_raw.columns)} colonnes")
    print(f"   ✅ SILVER: {len(df_silver):,} lignes, {len(df_silver.columns)} colonnes")
    print(f"   ✅ GOLD:   {len(df_gold):,} lignes, {len(df_gold.columns)} colonnes")
    
    # Exemple 1: Voir les premières lignes
    print("\n" + "="*80)
    print("[EXEMPLE 1] Premières lignes du dataset GOLD")
    print("="*80)
    print("\nCode:")
    print("   df_gold.head(10)")
    print("\nRésultat:")
    display_cols = ['id', 'source', 'title', 'sentiment', 'sentiment_score']
    print(df_gold[display_cols].head(10).to_string(index=False))
    
    # Exemple 2: Distribution du sentiment
    print("\n" + "="*80)
    print("[EXEMPLE 2] Distribution du sentiment")
    print("="*80)
    print("\nCode:")
    print("   df_gold['sentiment'].value_counts()")
    print("\nRésultat:")
    sentiment_counts = df_gold['sentiment'].value_counts()
    for sent, count in sentiment_counts.items():
        pct = (count / len(df_gold)) * 100
        emoji = {'positif': '✅', 'neutre': '⚪', 'négatif': '❌'}.get(sent, '📊')
        print(f"   {emoji} {sent:10s}: {count:4d} articles ({pct:5.1f}%)")
    
    # Exemple 3: Filtrer par sentiment
    print("\n" + "="*80)
    print("[EXEMPLE 3] Filtrer les articles positifs")
    print("="*80)
    print("\nCode:")
    print("   positifs = df_gold[df_gold['sentiment'] == 'positif']")
    print("   print(f\"Articles positifs: {len(positifs)}\")")
    print("   positifs[['source', 'title', 'sentiment_score']].head(5)")
    print("\nRésultat:")
    positifs = df_gold[df_gold['sentiment'] == 'positif']
    print(f"   Articles positifs: {len(positifs)}")
    print("\n   Top 5 articles positifs:")
    print(positifs[['source', 'title', 'sentiment_score']].head(5).to_string(index=False))
    
    # Exemple 4: Filtrer par source
    print("\n" + "="*80)
    print("[EXEMPLE 4] Filtrer par source (trustpilot_reviews)")
    print("="*80)
    print("\nCode:")
    print("   trustpilot = df_gold[df_gold['source'] == 'trustpilot_reviews']")
    print("   trustpilot['sentiment'].value_counts()")
    print("\nRésultat:")
    trustpilot = df_gold[df_gold['source'] == 'trustpilot_reviews']
    print(f"   Total articles Trustpilot: {len(trustpilot)}")
    sentiment_tp = trustpilot['sentiment'].value_counts()
    for sent, count in sentiment_tp.items():
        pct = (count / len(trustpilot)) * 100
        emoji = {'positif': '✅', 'neutre': '⚪', 'négatif': '❌'}.get(sent, '📊')
        print(f"   {emoji} {sent:10s}: {count:4d} ({pct:5.1f}%)")
    
    # Exemple 5: Filtrer par topic
    print("\n" + "="*80)
    print("[EXEMPLE 5] Filtrer par topic (technologie)")
    print("="*80)
    print("\nCode:")
    print("   tech = df_gold[df_gold['topic_1'] == 'technologie']")
    print("   tech['sentiment'].value_counts()")
    print("\nRésultat:")
    tech = df_gold[df_gold['topic_1'] == 'technologie']
    print(f"   Total articles technologie: {len(tech)}")
    sentiment_tech = tech['sentiment'].value_counts()
    for sent, count in sentiment_tech.items():
        pct = (count / len(tech)) * 100
        emoji = {'positif': '✅', 'neutre': '⚪', 'négatif': '❌'}.get(sent, '📊')
        print(f"   {emoji} {sent:10s}: {count:4d} ({pct:5.1f}%)")
    
    # Exemple 6: Statistiques par source
    print("\n" + "="*80)
    print("[EXEMPLE 6] Statistiques par source")
    print("="*80)
    print("\nCode:")
    print("   df_gold.groupby('source')['sentiment'].value_counts().unstack(fill_value=0)")
    print("\nRésultat:")
    source_sentiment = df_gold.groupby('source')['sentiment'].value_counts().unstack(fill_value=0)
    print(source_sentiment.head(10).to_string())
    
    # Exemple 7: Articles avec score élevé
    print("\n" + "="*80)
    print("[EXEMPLE 7] Articles avec sentiment score élevé (>0.9)")
    print("="*80)
    print("\nCode:")
    print("   high_score = df_gold[df_gold['sentiment_score'] > 0.9]")
    print("   high_score[['source', 'title', 'sentiment', 'sentiment_score']].head(5)")
    print("\nRésultat:")
    high_score = df_gold[df_gold['sentiment_score'] > 0.9]
    print(f"   Articles avec score > 0.9: {len(high_score)}")
    print("\n   Top 5:")
    print(high_score[['source', 'title', 'sentiment', 'sentiment_score']].head(5).to_string(index=False))
    
    # Exemple 8: Combinaison de filtres
    print("\n" + "="*80)
    print("[EXEMPLE 8] Articles positifs de technologie")
    print("="*80)
    print("\nCode:")
    print("   pos_tech = df_gold[(df_gold['sentiment'] == 'positif') & (df_gold['topic_1'] == 'technologie')]")
    print("   pos_tech[['source', 'title', 'sentiment_score']]")
    print("\nRésultat:")
    pos_tech = df_gold[(df_gold['sentiment'] == 'positif') & (df_gold['topic_1'] == 'technologie')]
    print(f"   Articles positifs sur technologie: {len(pos_tech)}")
    if len(pos_tech) > 0:
        print("\n   Exemples:")
        print(pos_tech[['source', 'title', 'sentiment_score']].head(5).to_string(index=False))
    else:
        print("   Aucun article trouvé")
    
    # Exemple 9: Statistiques descriptives
    print("\n" + "="*80)
    print("[EXEMPLE 9] Statistiques descriptives des scores")
    print("="*80)
    print("\nCode:")
    print("   df_gold['sentiment_score'].describe()")
    print("\nRésultat:")
    print(df_gold['sentiment_score'].describe().to_string())
    
    # Exemple 10: Top sources par sentiment
    print("\n" + "="*80)
    print("[EXEMPLE 10] Top 5 sources avec le plus d'articles positifs")
    print("="*80)
    print("\nCode:")
    print("   positifs_by_source = df_gold[df_gold['sentiment'] == 'positif'].groupby('source').size().sort_values(ascending=False)")
    print("   positifs_by_source.head(5)")
    print("\nRésultat:")
    positifs_by_source = df_gold[df_gold['sentiment'] == 'positif'].groupby('source').size().sort_values(ascending=False)
    for source, count in positifs_by_source.head(5).items():
        print(f"   • {source:30s}: {count:3d} articles positifs")
    
    print("\n" + "="*80)
    print("[FIN] EXEMPLES D'EXPLORATION")
    print("="*80)
    print("\n💡 Pour explorer interactivement:")
    print("   python scripts/explore_datasets.py")
    print("\n💡 Pour voir les datasets rapidement:")
    print("   python scripts/view_datasets.py")
    print("\n")

if __name__ == "__main__":
    main()
