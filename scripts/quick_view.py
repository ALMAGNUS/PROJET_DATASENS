#!/usr/bin/env python3
"""Visualisation rapide des données enrichies"""
import sys
from pathlib import Path

import pandas as pd

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def view_gold():
    """Affiche un aperçu du fichier GOLD avec topics et sentiment"""
    gold_file = Path(__file__).parent.parent / 'exports' / 'gold.csv'

    if not gold_file.exists():
        print(f"[ERROR] {gold_file} n'existe pas")
        print("   Lancez d'abord: python main.py")
        return

    df = pd.read_csv(gold_file, encoding='utf-8')

    print("\n" + "="*80)
    print("[VISUALISATION] GOLD DATASET - DONNÉES ENRICHIES")
    print("="*80)
    print(f"\n   Fichier: {gold_file}")
    print(f"   Total articles: {len(df):,}")
    print(f"   Colonnes: {len(df.columns)}")

    # Statistiques par topic
    print("\n[TOPICS] Distribution des topics:")
    topic1_counts = df[df['topic_1'] != '']['topic_1'].value_counts()
    for topic, count in topic1_counts.head(10).items():
        pct = (count / len(df)) * 100
        print(f"   • {topic:25s}: {count:4d} articles ({pct:5.1f}%)")

    # Statistiques par sentiment
    print("\n[SENTIMENT] Distribution du sentiment:")
    if 'sentiment' in df.columns:
        sentiment_counts = df['sentiment'].value_counts()
        total_sent = len(df[df['sentiment'].notna()])
        for sent, count in sentiment_counts.items():
            pct = (count / total_sent) * 100 if total_sent > 0 else 0
            avg_score = df[df['sentiment'] == sent]['sentiment_score'].mean()
            # Emoji pour visualisation
            emoji = {'positif': '✅', 'neutre': '⚪', 'négatif': '❌'}.get(sent, '📊')
            print(f"   {emoji} {sent:10s}: {count:4d} articles ({pct:5.1f}%) - Score moyen: {avg_score:.3f}")

        # Afficher le total
        print(f"\n   📊 TOTAL: {total_sent:,} articles avec sentiment analysé")
    else:
        print("   ⚠️  Colonne 'sentiment' introuvable dans gold.csv")

    # Statistiques par source
    print("\n[SOURCES] Top 10 sources:")
    source_counts = df['source'].value_counts()
    for source, count in source_counts.head(10).items():
        pct = (count / len(df)) * 100
        print(f"   • {source:30s}: {count:4d} articles ({pct:5.1f}%)")

    # Exemples d'articles enrichis
    print("\n[EXEMPLES] 5 articles enrichis (avec topics + sentiment):")
    print("   " + "-"*76)
    # Filtrer les articles avec topics non vides
    enriched = df[df['topic_1'].notna() & (df['topic_1'] != '') & (df['sentiment'] != '')].head(5)
    if len(enriched) == 0:
        enriched = df[df['sentiment'] != ''].head(5)  # Fallback: juste avec sentiment

    for idx, (_, row) in enumerate(enriched.iterrows(), 1):
        print(f"\n   [{idx}] {row['source']}")
        title = str(row['title'])[:60] if pd.notna(row['title']) else 'N/A'
        print(f"       Titre: {title}...")
        topic1 = str(row['topic_1']) if pd.notna(row['topic_1']) and row['topic_1'] != '' else 'autre'
        score1 = float(row['topic_1_score']) if pd.notna(row['topic_1_score']) else 0.0
        topics_str = f"{topic1} ({score1:.2f})"
        if pd.notna(row['topic_2']) and str(row['topic_2']) != '':
            score2 = float(row['topic_2_score']) if pd.notna(row['topic_2_score']) else 0.0
            topics_str += f" + {row['topic_2']} ({score2:.2f})"
        print(f"       Topics: {topics_str}")
        print(f"       Sentiment: {row['sentiment']} (score: {row['sentiment_score']:.2f})")

    print("\n" + "="*80)
    print("\nPour voir plus de détails:")
    print("   - Ouvrir exports/gold.csv dans Excel")
    print("   - Utiliser: python scripts/view_exports.py")
    print("\n")

if __name__ == "__main__":
    view_gold()

