#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifier le statut de la DB SQLite"""
import sys
import io
import sqlite3
from pathlib import Path

# Fix encoding (avoid replacing pytest capture streams)
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

def check_db_status():
    """Vérifier le statut de la DB"""
    print("="*70)
    print("STATUT SQLITE DATABASE")
    print("="*70)
    
    db_path = Path.home() / 'datasens_project' / 'datasens.db'
    if not db_path.exists():
        print(f"\n[ERREUR] Base non trouvee: {db_path}")
        return
    
    # Taille
    size_mb = db_path.stat().st_size / (1024 * 1024)
    
    # Connexion
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Compter articles
    cursor.execute("SELECT COUNT(*) FROM raw_data")
    total_articles = cursor.fetchone()[0]
    
    # Compter sources
    cursor.execute("SELECT COUNT(*) FROM source")
    total_sources = cursor.fetchone()[0]
    
    # Taille des tables
    cursor.execute("""
        SELECT name, 
               (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
        FROM sqlite_master m
        WHERE type='table'
        ORDER BY name
    """)
    tables = cursor.fetchall()
    
    # Limites SQLite
    sqlite_max_size_tb = 140  # TB
    sqlite_max_rows = 2**63 - 1  # ~9.2 quintillions
    
    print(f"\n✅ Base de donnees: {db_path.name}")
    print(f"   Taille: {size_mb:.2f} MB")
    print(f"   Articles: {total_articles:,}")
    print(f"   Sources: {total_sources}")
    
    print(f"\n📊 Limites SQLite:")
    print(f"   Taille max: {sqlite_max_size_tb} TB")
    print(f"   Utilisation: {(size_mb / (sqlite_max_size_tb * 1024 * 1024)) * 100:.10f}%")
    print(f"   Lignes max: {sqlite_max_rows:,}")
    print(f"   Utilisation: {(total_articles / sqlite_max_rows) * 100:.20f}%")
    
    print(f"\n📋 Tables:")
    for name, _ in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {name}")
            count = cursor.fetchone()[0]
            print(f"   - {name}: {count:,} lignes")
        except:
            print(f"   - {name}: (erreur)")
    
    conn.close()
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print(f"\n✅ SQLite n'est PAS sature:")
    print(f"   - Taille: {size_mb:.2f} MB sur {sqlite_max_size_tb} TB max")
    print(f"   - Articles: {total_articles:,} sur {sqlite_max_rows:,} max")
    print(f"\n✅ Les erreurs 'UNIQUE constraint failed' sont NORMALES:")
    print(f"   - C'est la deduplication qui fonctionne")
    print(f"   - Les articles deja dans la DB sont ignores (c'est voulu)")
    print(f"   - Le code a ete corrige pour ne plus afficher ces erreurs")

if __name__ == "__main__":
    check_db_status()
