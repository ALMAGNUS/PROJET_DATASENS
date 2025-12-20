#!/usr/bin/env python3
"""Ré-analyse tous les articles avec l'analyseur de sentiment"""
import os
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
import sqlite3

from analyzer import SentimentAnalyzer


def reanalyze_all_sentiments():
    """Ré-analyse tous les articles avec le nouvel analyseur amélioré"""
    db_path = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))

    if not Path(db_path).exists():
        print(f"[ERREUR] Base de données introuvable: {db_path}")
        print("   Lancez d'abord: python main.py")
        return

    print("\n" + "="*80)
    print("[RÉ-ANALYSE] SENTIMENT")
    print("="*80)

    # Connexions
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    analyzer = SentimentAnalyzer(db_path)

    # Récupérer tous les articles
    cursor.execute("""
        SELECT raw_data_id, title, content
        FROM raw_data
        ORDER BY raw_data_id
    """)
    articles = cursor.fetchall()

    print(f"\n[INFO] {len(articles):,} articles à analyser")
    print("\n[PROGRESSION] Analyse en cours...")

    stats = {'positif': 0, 'neutre': 0, 'négatif': 0, 'erreurs': 0}

    for idx, (raw_data_id, title, content) in enumerate(articles, 1):
        try:
            # Analyser le sentiment
            sent, score = analyzer.analyze(f"{title or ''} {content or ''}")
            stats[sent] = stats.get(sent, 0) + 1

            # Mettre à jour dans la DB
            cursor.execute("""
                DELETE FROM model_output
                WHERE raw_data_id = ? AND model_name = 'sentiment_keyword'
            """, (raw_data_id,))
            cursor.execute("""
                INSERT INTO model_output (raw_data_id, model_name, label, score, created_at)
                VALUES (?, 'sentiment_keyword', ?, ?, datetime('now'))
            """, (raw_data_id, sent, score))

            # Afficher progression tous les 100 articles
            if idx % 100 == 0:
                print(f"   [{idx:5d}/{len(articles):5d}] Traités... ({stats['positif']} pos, {stats['négatif']} neg, {stats['neutre']} neu)")
        except Exception as e:
            stats['erreurs'] += 1
            if idx % 100 == 0:
                print(f"   [ERREUR] Article {raw_data_id}: {str(e)[:50]}")

    conn.commit()

    # Statistiques finales
    print("\n" + "="*80)
    print("[RÉSULTATS] DISTRIBUTION DES SENTIMENTS")
    print("="*80)

    total = len(articles) - stats['erreurs']
    for label in ['positif', 'neutre', 'négatif']:
        count = stats[label]
        pct = (count / total * 100) if total > 0 else 0
        emoji = {'positif': '✅', 'neutre': '⚪', 'négatif': '❌'}.get(label, '📊')
        print(f"   {emoji} {label:10s}: {count:4d} articles ({pct:5.1f}%)")

    if stats['erreurs'] > 0:
        print(f"\n   ⚠️  Erreurs: {stats['erreurs']} articles")

    print(f"\n   📊 TOTAL: {total:,} articles analysés")

    # Distribution finale
    cursor.execute("""
        SELECT label, COUNT(*) as count, AVG(score) as avg_score
        FROM model_output
        WHERE model_name = 'sentiment_keyword'
        GROUP BY label
        ORDER BY count DESC
    """)

    print("\n[STATISTIQUES] Distribution dans la base de données:")
    for label, count, avg_score in cursor.fetchall():
        pct = (count / total * 100) if total > 0 else 0
        emoji = {'positif': '✅', 'neutre': '⚪', 'négatif': '❌'}.get(label, '📊')
        print(f"   {emoji} {label:10s}: {count:4d} articles ({pct:5.1f}%) - Score moyen: {avg_score:.3f}")

    print("\n" + "="*80)
    print("[OK] ANALYSE TERMINÉE")
    print("="*80)
    print("\nPour voir les résultats:")
    print("   - python scripts/visualize_sentiment.py  (graphiques)")
    print("   - python scripts/quick_view.py           (aperçu)")
    print("   - python scripts/show_dashboard.py        (dashboard)")
    print("\n")

    # Fermer les connexions
    analyzer.close()
    conn.close()

if __name__ == "__main__":
    try:
        reanalyze_all_sentiments()
    except Exception as e:
        print(f"[ERREUR] {e!s}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
