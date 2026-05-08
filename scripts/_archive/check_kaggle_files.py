#!/usr/bin/env python3
"""Vérifier que les fichiers Kaggle sont bien placés"""
import io
import json
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def load_sources_config():
    """Charge sources_config.json"""
    config_path = Path(__file__).parent.parent / "sources_config.json"
    if not config_path.exists():
        return {}

    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def check_kaggle_files():
    """Vérifie que les fichiers Kaggle sont bien placés"""
    print("=" * 70)
    print("VERIFICATION : Fichiers Kaggle dans data/raw")
    print("=" * 70)

    # Charger config
    config = load_sources_config()
    kaggle_sources = [
        s for s in config.get("sources", []) if "kaggle" in s.get("source_name", "").lower()
    ]

    if not kaggle_sources:
        print("\n[ATTENTION] Aucune source Kaggle trouvee dans sources_config.json")
        return

    # Dossiers possibles
    raw_dirs = [
        Path(__file__).parent.parent / "data" / "raw",
        Path.home() / "datasens_project" / "data" / "raw",
        Path.home() / "Desktop" / "DEV IA 2025" / "PROJET_DATASENS" / "data" / "raw",
    ]

    raw_dir = None
    for d in raw_dirs:
        if d.exists():
            raw_dir = d
            break

    if not raw_dir:
        print("\n[ERREUR] Dossier data/raw non trouve")
        return

    print(f"\nDossier verifie : {raw_dir}")
    print(f"\nSources Kaggle dans config : {len(kaggle_sources)}")

    # Vérifier chaque source
    print("\n" + "=" * 70)
    print("VERIFICATION PAR SOURCE")
    print("=" * 70)

    results = []

    for source in kaggle_sources:
        source_name = source["source_name"]
        active = source.get("active", True)
        source.get("partition_path", "")

        print(f"\n[{source_name}]")
        print(f"   Active : {'OUI' if active else 'NON'}")

        # Chercher le dossier
        source_dir = raw_dir / source_name
        if not source_dir.exists():
            print(f"   [MANQUANT] Dossier non trouve : {source_dir.name}")
            results.append(
                {"source": source_name, "status": "MANQUANT", "dossier": False, "fichiers": 0}
            )
            continue

        print(f"   [OK] Dossier existe : {source_dir.name}")

        # Chercher les fichiers CSV/JSON
        csv_files = list(source_dir.rglob("*.csv"))
        json_files = list(source_dir.rglob("*.json"))
        all_files = csv_files + json_files

        # Filtrer les manifest.txt et fichiers vides
        valid_files = []
        for f in all_files:
            if "manifest" in f.name.lower():
                continue
            try:
                size = f.stat().st_size
                if size > 100:  # Fichier > 100 bytes
                    valid_files.append(f)
            except:
                pass

        if not valid_files:
            print("   [VIDE] Aucun fichier valide trouve (CSV/JSON > 100 bytes)")
            print(f"   Fichiers trouves mais vides/ignores : {len(all_files)}")
            for f in all_files[:3]:  # Afficher les 3 premiers
                try:
                    size = f.stat().st_size
                    print(f"      - {f.name} ({size} bytes)")
                except:
                    print(f"      - {f.name}")
            results.append(
                {"source": source_name, "status": "VIDE", "dossier": True, "fichiers": 0}
            )
        else:
            print(f"   [OK] {len(valid_files)} fichier(s) valide(s) trouve(s) :")
            total_size = 0
            for f in valid_files[:5]:  # Afficher les 5 premiers
                try:
                    size = f.stat().st_size
                    total_size += size
                    size_kb = size / 1024
                    print(f"      - {f.name} ({size_kb:.1f} KB)")
                except:
                    print(f"      - {f.name}")
            if len(valid_files) > 5:
                print(f"      ... et {len(valid_files) - 5} autre(s)")

            print(f"   Total : {total_size / 1024:.1f} KB")

            results.append(
                {
                    "source": source_name,
                    "status": "OK",
                    "dossier": True,
                    "fichiers": len(valid_files),
                    "size_kb": total_size / 1024,
                }
            )

    # Résumé
    print("\n" + "=" * 70)
    print("RESUME")
    print("=" * 70)

    ok_count = sum(1 for r in results if r["status"] == "OK")
    vide_count = sum(1 for r in results if r["status"] == "VIDE")
    manquant_count = sum(1 for r in results if r["status"] == "MANQUANT")

    print(f"\nSources avec fichiers valides : {ok_count}")
    print(f"Sources avec dossiers vides    : {vide_count}")
    print(f"Sources manquantes             : {manquant_count}")
    print(f"Total                          : {len(results)}")

    # Recommandation
    print("\n" + "=" * 70)
    print("RECOMMANDATION")
    print("=" * 70)

    if vide_count > 0 or manquant_count > 0:
        print("\n[ATTENTION] Certaines sources Kaggle n'ont pas de fichiers valides")
        print("\nOptions :")
        print("1. Télécharger les datasets manquants depuis Kaggle")
        print("2. Désactiver les sources sans fichiers dans sources_config.json")
        print("   (mettre 'active': false)")
    else:
        print("\n[OK] Toutes les sources Kaggle ont des fichiers valides")

    # Liste des sources à désactiver (si vides)
    if vide_count > 0 or manquant_count > 0:
        print("\nSources à désactiver (sans fichiers) :")
        for r in results:
            if r["status"] in ["VIDE", "MANQUANT"]:
                print(f"   - {r['source']}")


if __name__ == "__main__":
    check_kaggle_files()
