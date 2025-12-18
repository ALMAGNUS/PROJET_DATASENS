#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test du pipeline E1 et vérification des sentiments"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_sentiment_in_db():
    """Vérifie que les sentiments sont bien dans la DB"""
    import sqlite3
    from pathlib import Path
    import os
    
    db_path = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))
    
    if not Path(db_path).exists():
        print(f"[ERREUR] Base de données introuvable: {db_path}")
        print("   Lancez d'abord: python main.py")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier les sentiments dans model_output
    cursor.execute("""
        SELECT label, COUNT(*) as count, AVG(score) as avg_score
        FROM model_output 
        WHERE model_name = 'sentiment_keyword'
        GROUP BY label
    """)
    results = cursor.fetchall()
    
    print("\n" + "="*80)
    print("[TEST] VÉRIFICATION DES SENTIMENTS DANS LA BASE DE DONNÉES")
    print("="*80)
    
    if not results:
        print("\n   ⚠️  AUCUN SENTIMENT trouvé dans model_output")
        print("   → Les articles n'ont pas été analysés")
        print("   → Solution: Lancez 'python main.py' pour analyser les articles")
        conn.close()
        return False
    
    print(f"\n[OK] Sentiments trouvés dans la base de données:")
    total = sum(r[1] for r in results)
    for label, count, avg_score in results:
        pct = (count / total) * 100 if total > 0 else 0
        emoji = {'positif': '✅', 'neutre': '⚪', 'négatif': '❌'}.get(label, '📊')
        print(f"   {emoji} {label:10s}: {count:4d} articles ({pct:5.1f}%) - Score moyen: {avg_score:.3f}")
    
    print(f"\n   📊 TOTAL: {total:,} articles avec sentiment")
    
    # Vérifier les articles sans sentiment
    cursor.execute("""
        SELECT COUNT(*) FROM raw_data r
        WHERE NOT EXISTS (
            SELECT 1 FROM model_output mo 
            WHERE mo.raw_data_id = r.raw_data_id 
            AND mo.model_name = 'sentiment_keyword'
        )
    """)
    without_sentiment = cursor.fetchone()[0]
    
    if without_sentiment > 0:
        print(f"\n   ⚠️  {without_sentiment:,} articles SANS sentiment")
        print(f"   → Solution: Lancez 'python scripts/enrich_all_articles.py' pour enrichir tous les articles")
    
    conn.close()
    return True

def test_sentiment_in_csv():
    """Vérifie que les sentiments sont bien dans gold.csv"""
    gold_file = Path(__file__).parent.parent / 'exports' / 'gold.csv'
    
    if not gold_file.exists():
        print(f"\n[ERREUR] {gold_file} n'existe pas")
        print("   Lancez d'abord: python main.py")
        return False
    
    import pandas as pd
    df = pd.read_csv(gold_file, encoding='utf-8')
    
    print("\n" + "="*80)
    print("[TEST] VÉRIFICATION DES SENTIMENTS DANS gold.csv")
    print("="*80)
    
    if 'sentiment' not in df.columns:
        print("\n   ⚠️  Colonne 'sentiment' introuvable dans gold.csv")
        print(f"   Colonnes disponibles: {', '.join(df.columns)}")
        return False
    
    # Compter les sentiments
    sentiment_counts = df['sentiment'].value_counts()
    total = len(df[df['sentiment'].notna()])
    
    print(f"\n[OK] Sentiments trouvés dans gold.csv:")
    for sent, count in sentiment_counts.items():
        pct = (count / total) * 100 if total > 0 else 0
        avg_score = df[df['sentiment'] == sent]['sentiment_score'].mean()
        emoji = {'positif': '✅', 'neutre': '⚪', 'négatif': '❌'}.get(sent, '📊')
        print(f"   {emoji} {sent:10s}: {count:4d} articles ({pct:5.1f}%) - Score moyen: {avg_score:.3f}")
    
    print(f"\n   📊 TOTAL: {total:,} articles avec sentiment sur {len(df):,} articles totaux")
    
    # Afficher quelques exemples
    print(f"\n[EXEMPLES] 5 articles avec sentiment:")
    sample = df[df['sentiment'].notna()].head(5)
    for idx, (_, row) in enumerate(sample.iterrows(), 1):
        title = str(row['title'])[:60] if pd.notna(row['title']) else 'N/A'
        sentiment = row['sentiment']
        score = row['sentiment_score']
        emoji = {'positif': '✅', 'neutre': '⚪', 'négatif': '❌'}.get(sentiment, '📊')
        print(f"   [{idx}] {emoji} {sentiment:8s} (score: {score:.3f}) - {title}...")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("[TEST] PIPELINE E1 - VÉRIFICATION DES SENTIMENTS")
    print("="*80)
    
    # Test 1: Sentiments dans la DB
    db_ok = test_sentiment_in_db()
    
    # Test 2: Sentiments dans CSV
    csv_ok = test_sentiment_in_csv()
    
    # Résumé
    print("\n" + "="*80)
    print("[RÉSUMÉ] RÉSULTATS DES TESTS")
    print("="*80)
    print(f"   Base de données: {'✅ OK' if db_ok else '❌ ERREUR'}")
    print(f"   Fichier gold.csv: {'✅ OK' if csv_ok else '❌ ERREUR'}")
    
    if db_ok and csv_ok:
        print("\n   ✅ TOUS LES TESTS RÉUSSIS")
        print("\n   Pour voir les visualisations:")
        print("      - python scripts/visualize_sentiment.py  (graphiques)")
        print("      - python scripts/quick_view.py           (aperçu texte)")
        print("      - python scripts/show_dashboard.py        (dashboard complet)")
    else:
        print("\n   ⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("\n   Solutions:")
        if not db_ok:
            print("      - Lancez: python main.py")
            print("      - Ou: python scripts/enrich_all_articles.py")
        if not csv_ok:
            print("      - Lancez: python main.py (pour générer gold.csv)")
    
    print("\n" + "="*80 + "\n")
