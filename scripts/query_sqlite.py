#!/usr/bin/env python3
"""Interroger directement SQLite - Simple et direct"""
import os
import sqlite3
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def get_db_path():
    """Retourne le chemin de la base de données"""
    return os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))

def query(sql):
    """Exécute une requête SQL et affiche les résultats"""
    db_path = get_db_path()
    if not Path(db_path).exists():
        print(f"[ERREUR] Base de données introuvable: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()

        if rows:
            # Afficher les noms de colonnes
            columns = [description[0] for description in cursor.description]
            print("\n" + " | ".join(f"{col:20s}" for col in columns))
            print("-" * (len(columns) * 23))

            # Afficher les résultats
            for row in rows:
                print(" | ".join(f"{str(val)[:20]:20s}" for val in row))

            print(f"\n{len(rows)} ligne(s)")
        else:
            print("Aucun résultat")

    except Exception as e:
        print(f"[ERREUR] {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Requête passée en argument
        sql = " ".join(sys.argv[1:])
        query(sql)
    else:
        # Mode interactif simple
        print("\n" + "="*80)
        print("[SQLITE] Requêtes Directes")
        print("="*80)
        print(f"\nBase de données: {get_db_path()}")
        print("\nExemples de requêtes:")
        print("  python scripts/query_sqlite.py \"SELECT label, COUNT(*) FROM model_output WHERE model_name='sentiment_keyword' GROUP BY label\"")
        print("\nOu utilisez SQLite directement:")
        print(f"  sqlite3 {get_db_path()}")
        print("\n")
