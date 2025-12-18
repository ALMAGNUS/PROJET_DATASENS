#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Visualisation des sentiments avec graphiques"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import sys
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def visualize_sentiment():
    """Crée des visualisations pour les sentiments"""
    gold_file = Path(__file__).parent.parent / 'exports' / 'gold.csv'
    
    if not gold_file.exists():
        print(f"[ERREUR] {gold_file} n'existe pas")
        print("   Lancez d'abord: python main.py")
        return
    
    df = pd.read_csv(gold_file, encoding='utf-8')
    
    if 'sentiment' not in df.columns:
        print("[ERREUR] Colonne 'sentiment' introuvable dans gold.csv")
        return
    
    print("\n" + "="*80)
    print("[VISUALISATION] SENTIMENT ANALYSIS - DATASENS E1")
    print("="*80)
    
    # Statistiques sentiment
    print(f"\n[STATISTIQUES] Distribution du sentiment:")
    sentiment_counts = df['sentiment'].value_counts()
    total = len(df)
    
    for sent, count in sentiment_counts.items():
        pct = (count / total) * 100
        avg_score = df[df['sentiment'] == sent]['sentiment_score'].mean()
        print(f"   • {sent:10s}: {count:4d} articles ({pct:5.1f}%) - Score moyen: {avg_score:.3f}")
    
    # Exemples d'articles par sentiment
    print(f"\n[EXEMPLES] Articles par sentiment:")
    for sentiment in ['positif', 'neutre', 'négatif']:
        if sentiment in sentiment_counts.index:
            sample = df[df['sentiment'] == sentiment].head(3)
            print(f"\n   {sentiment.upper()} ({sentiment_counts[sentiment]} articles):")
            for idx, (_, row) in enumerate(sample.iterrows(), 1):
                title = str(row['title'])[:70] if pd.notna(row['title']) else 'N/A'
                score = float(row['sentiment_score']) if pd.notna(row['sentiment_score']) else 0.0
                print(f"      [{idx}] {title}... (score: {score:.2f})")
    
    # Créer les graphiques
    output_dir = Path(__file__).parent.parent / 'visualizations'
    output_dir.mkdir(exist_ok=True)
    
    # 1. Graphique en barres - Distribution sentiment
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('DataSens E1 - Analyse de Sentiment', fontsize=16, fontweight='bold')
    
    # Graphique 1: Distribution sentiment (barres)
    ax1 = axes[0, 0]
    colors = {'positif': '#2ecc71', 'neutre': '#95a5a6', 'négatif': '#e74c3c'}
    sentiment_counts.plot(kind='bar', ax=ax1, color=[colors.get(s, '#3498db') for s in sentiment_counts.index])
    ax1.set_title('Distribution du Sentiment', fontweight='bold')
    ax1.set_xlabel('Sentiment')
    ax1.set_ylabel('Nombre d\'articles')
    ax1.set_xticklabels(sentiment_counts.index, rotation=0)
    ax1.grid(axis='y', alpha=0.3)
    for i, v in enumerate(sentiment_counts.values):
        ax1.text(i, v + max(sentiment_counts.values) * 0.01, str(v), ha='center', va='bottom')
    
    # Graphique 2: Distribution sentiment (camembert)
    ax2 = axes[0, 1]
    sentiment_counts.plot(kind='pie', ax=ax2, autopct='%1.1f%%', 
                          colors=[colors.get(s, '#3498db') for s in sentiment_counts.index],
                          startangle=90)
    ax2.set_title('Répartition du Sentiment (%)', fontweight='bold')
    ax2.set_ylabel('')
    
    # Graphique 3: Score moyen par sentiment
    ax3 = axes[1, 0]
    avg_scores = df.groupby('sentiment')['sentiment_score'].mean().sort_values(ascending=False)
    avg_scores.plot(kind='bar', ax=ax3, color=[colors.get(s, '#3498db') for s in avg_scores.index])
    ax3.set_title('Score Moyen par Sentiment', fontweight='bold')
    ax3.set_xlabel('Sentiment')
    ax3.set_ylabel('Score moyen')
    ax3.set_xticklabels(avg_scores.index, rotation=0)
    ax3.grid(axis='y', alpha=0.3)
    ax3.set_ylim(0, 1.0)
    for i, v in enumerate(avg_scores.values):
        ax3.text(i, v + 0.02, f'{v:.3f}', ha='center', va='bottom')
    
    # Graphique 4: Distribution des scores (histogramme)
    ax4 = axes[1, 1]
    for sentiment in ['positif', 'neutre', 'négatif']:
        if sentiment in df['sentiment'].values:
            scores = df[df['sentiment'] == sentiment]['sentiment_score']
            ax4.hist(scores, bins=20, alpha=0.6, label=sentiment, 
                    color=colors.get(sentiment, '#3498db'))
    ax4.set_title('Distribution des Scores de Sentiment', fontweight='bold')
    ax4.set_xlabel('Score')
    ax4.set_ylabel('Fréquence')
    ax4.legend()
    ax4.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Sauvegarder les 4 graphiques ensemble (2x2) avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    chart_file = output_dir / f'sentiment_analysis_{timestamp}.png'
    plt.savefig(chart_file, dpi=150, bbox_inches='tight')
    plt.close(fig)  # Fermer la figure principale
    print(f"\n[OK] Graphiques sauvegardés: {chart_file}")
    print(f"     → 4 graphiques dans un seul fichier PNG (2x2)")
    print(f"     → Fichier avec timestamp pour conserver l'historique")
    
    
    # Statistiques par source
    print(f"\n[SENTIMENT PAR SOURCE] Top 10 sources:")
    source_sentiment = df.groupby(['source', 'sentiment']).size().unstack(fill_value=0)
    source_sentiment['total'] = source_sentiment.sum(axis=1)
    source_sentiment = source_sentiment.sort_values('total', ascending=False).head(10)
    
    for source in source_sentiment.index:
        total = source_sentiment.loc[source, 'total']
        pos = source_sentiment.loc[source, 'positif'] if 'positif' in source_sentiment.columns else 0
        neg = source_sentiment.loc[source, 'négatif'] if 'négatif' in source_sentiment.columns else 0
        neu = source_sentiment.loc[source, 'neutre'] if 'neutre' in source_sentiment.columns else 0
        print(f"   • {source:30s}: {total:3d} articles (P:{pos:2d} N:{neg:2d} Neu:{neu:2d})")
    
    # Statistiques par topic
    if 'topic_1' in df.columns:
        print(f"\n[SENTIMENT PAR TOPIC] Top 10 topics:")
        topic_sentiment = df[df['topic_1'] != ''].groupby(['topic_1', 'sentiment']).size().unstack(fill_value=0)
        topic_sentiment['total'] = topic_sentiment.sum(axis=1)
        topic_sentiment = topic_sentiment.sort_values('total', ascending=False).head(10)
        
        for topic in topic_sentiment.index:
            total = topic_sentiment.loc[topic, 'total']
            pos = topic_sentiment.loc[topic, 'positif'] if 'positif' in topic_sentiment.columns else 0
            neg = topic_sentiment.loc[topic, 'négatif'] if 'négatif' in topic_sentiment.columns else 0
            neu = topic_sentiment.loc[topic, 'neutre'] if 'neutre' in topic_sentiment.columns else 0
            print(f"   • {topic:20s}: {total:3d} articles (P:{pos:2d} N:{neg:2d} Neu:{neu:2d})")
    
    print("\n" + "="*80)
    print(f"\n[INFO] Total articles analysés: {total:,}")
    print(f"[INFO] Articles avec sentiment: {df['sentiment'].notna().sum():,}")
    print(f"[INFO] Graphiques sauvegardés dans: {chart_file}")
    print("\n")

if __name__ == "__main__":
    try:
        visualize_sentiment()
    except ImportError:
        print("[ERREUR] matplotlib n'est pas installé")
        print("   Installez avec: pip install matplotlib")
        sys.exit(1)
    except Exception as e:
        print(f"[ERREUR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
