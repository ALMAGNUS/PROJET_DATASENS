#!/usr/bin/env python3
"""Visualisation des datasets dans exports/ avec statistiques détaillées"""
import sys
from pathlib import Path

import pandas as pd

# Fix encoding for Windows console
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def view_dataset(file_path: Path, dataset_name: str):
    """Affiche un aperçu détaillé d'un dataset"""
    try:
        df = pd.read_csv(file_path, encoding="utf-8")

        print("\n" + "=" * 80)
        print(f"[DATASET] {dataset_name.upper()}")
        print("=" * 80)
        print(f"   Fichier: {file_path.name}")
        print(f"   Taille:  {file_path.stat().st_size / 1024:.1f} KB")
        print(f"   Lignes:  {len(df):,}")
        print(f"   Colonnes: {len(df.columns)}")

        # Colonnes
        print(f"\n   Colonnes ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            non_null = df[col].notna().sum()
            pct = (non_null / len(df)) * 100 if len(df) > 0 else 0
            print(f"      {i:2d}. {col:25s} ({non_null:5d} valeurs, {pct:5.1f}% non-null)")

        # Statistiques spécifiques selon le dataset
        if dataset_name == "GOLD" and "sentiment" in df.columns:
            print("\n   [SENTIMENT] Distribution:")
            sentiment_counts = df["sentiment"].value_counts()
            for sent, count in sentiment_counts.items():
                pct = (count / len(df)) * 100
                emoji = {"positif": "✅", "neutre": "⚪", "négatif": "❌"}.get(sent, "📊")
                print(f"      {emoji} {sent:10s}: {count:4d} articles ({pct:5.1f}%)")

        if dataset_name == "GOLD" and "topic_1" in df.columns:
            print("\n   [TOPICS] Distribution (topic_1):")
            topic_counts = df[df["topic_1"] != ""]["topic_1"].value_counts().head(10)
            for topic, count in topic_counts.items():
                pct = (count / len(df)) * 100
                print(f"      • {topic:20s}: {count:4d} articles ({pct:5.1f}%)")

        # Aperçu des données
        print("\n   [APERÇU] Premières 5 lignes:")
        print("   " + "-" * 76)

        # Afficher seulement les colonnes principales
        display_cols = (
            ["id", "source", "title", "sentiment", "sentiment_score"]
            if "sentiment" in df.columns
            else ["id", "source", "title"]
        )
        display_cols = [c for c in display_cols if c in df.columns]

        if display_cols:
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", 40)
            print(df[display_cols].head(5).to_string(index=False))
        else:
            print(df.head(5).to_string(index=False))

        if len(df) > 5:
            print(f"\n   ... et {len(df) - 5:,} lignes supplémentaires")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"   ERREUR: {e!s}")
        import traceback

        traceback.print_exc()


def main():
    """Affiche tous les datasets disponibles"""
    exports_dir = Path(__file__).parent.parent / "exports"

    if not exports_dir.exists():
        print("[ERREUR] Le dossier 'exports' n'existe pas")
        print("   Lancez d'abord: python main.py")
        sys.exit(1)

    datasets = {"RAW": "raw.csv", "SILVER": "silver.csv", "GOLD": "gold.csv"}

    print("\n" + "=" * 80)
    print("[DATASETS] VISUALISATION DES DATASETS DANS exports/")
    print("=" * 80)

    # Vérifier quels fichiers existent
    available = {}
    for name, filename in datasets.items():
        file_path = exports_dir / filename
        if file_path.exists():
            available[name] = file_path

    if not available:
        print("\n[ERREUR] Aucun fichier CSV trouvé dans exports/")
        print("   Lancez d'abord: python main.py")
        sys.exit(1)

    print(f"\n[INFO] {len(available)} dataset(s) disponible(s):")
    for name, file_path in available.items():
        size = file_path.stat().st_size / 1024
        print(f"   • {name:10s}: {file_path.name:20s} ({size:8.1f} KB)")

    # Afficher chaque dataset
    for name, file_path in available.items():
        view_dataset(file_path, name)

    print("\n[INFO] Pour ouvrir dans Excel/LibreOffice:")
    for name, file_path in available.items():
        print(f"   • {name:10s}: {file_path}")

    print("\n[INFO] Pour explorer interactivement:")
    print("   python scripts/view_exports.py")
    print("\n")


if __name__ == "__main__":
    main()
