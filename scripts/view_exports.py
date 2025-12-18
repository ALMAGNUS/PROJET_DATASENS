#!/usr/bin/env python3
"""Visualiser les fichiers CSV dans exports/"""
import pandas as pd
from pathlib import Path
import sys

def view_csv(file_path: Path, max_rows: int = 20):
    """Affiche un aperçu du CSV"""
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"\n{'='*80}")
        print(f"[CSV] {file_path.name}")
        print(f"{'='*80}")
        print(f"   Fichier: {file_path}")
        print(f"   Taille:  {file_path.stat().st_size / 1024:.1f} KB")
        print(f"   Lignes:  {len(df):,}")
        print(f"   Colonnes: {len(df.columns)}")
        print(f"\n   Colonnes: {', '.join(df.columns.tolist()[:10])}")
        if len(df.columns) > 10:
            print(f"            ... et {len(df.columns) - 10} autres")
        
        print(f"\n   Aperçu (premières {min(max_rows, len(df))} lignes):")
        print(f"   {'-'*80}")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        print(df.head(max_rows).to_string(index=False))
        
        if len(df) > max_rows:
            print(f"\n   ... et {len(df) - max_rows} lignes supplémentaires")
        
        print(f"\n{'='*80}\n")
    except Exception as e:
        print(f"   ERREUR: {str(e)}")

if __name__ == "__main__":
    exports_dir = Path(__file__).parent.parent / 'exports'
    
    if not exports_dir.exists():
        print(f"[ERREUR] Le dossier 'exports' n'existe pas")
        sys.exit(1)
    
    csv_files = {
        '1': 'raw.csv',
        '2': 'silver.csv',
        '3': 'gold.csv'
    }
    
    print("\n" + "="*80)
    print("[EXPORTS] VISUALISATION DES FICHIERS CSV")
    print("="*80)
    print("\nFichiers disponibles dans exports/:")
    for key, filename in csv_files.items():
        file_path = exports_dir / filename
        if file_path.exists():
            size = file_path.stat().st_size / 1024
            print(f"   {key}. {filename:20s} ({size:8.1f} KB)")
        else:
            print(f"   {key}. {filename:20s} (NON TROUVÉ)")
    
    print("\nOptions:")
    print("   - Tapez le numéro (1-3) pour voir un fichier")
    print("   - Tapez 'all' pour voir tous les fichiers")
    print("   - Tapez 'q' pour quitter")
    
    choice = input("\nVotre choix: ").strip().lower()
    
    if choice == 'q':
        sys.exit(0)
    elif choice == 'all':
        for filename in csv_files.values():
            file_path = exports_dir / filename
            if file_path.exists():
                view_csv(file_path, max_rows=10)
    elif choice in csv_files:
        filename = csv_files[choice]
        file_path = exports_dir / filename
        if file_path.exists():
            view_csv(file_path, max_rows=20)
        else:
            print(f"[ERREUR] {filename} n'existe pas")
    else:
        print("[ERREUR] Choix invalide")

