#!/usr/bin/env python3
"""
Script de Nettoyage Buffer SQLite
==================================
Nettoie le buffer SQLite (datasens.db) après export Parquet GOLD.

⚠️ ATTENTION: Ne nettoyer QUE après export Parquet réussi
Les données doivent être sauvegardées dans Parquet avant nettoyage.
"""

import sqlite3
import sys
from datetime import date
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    import io

    try:
        if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != "utf-8":
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def get_db_path():
    """Trouve le chemin de la base de données"""
    # Chercher dans le projet
    project_db = Path(__file__).parent.parent / "datasens.db"
    if project_db.exists():
        return str(project_db)

    # Chercher dans datasens_project
    home_db = Path.home() / "datasens_project" / "datasens.db"
    if home_db.exists():
        return str(home_db)

    # Chercher via variable d'environnement
    import os

    env_db = os.getenv("DB_PATH")
    if env_db and Path(env_db).exists():
        return env_db

    return None


def check_parquet_export(target_date: date | None = None) -> bool:
    """Vérifie qu'un export Parquet existe pour la date donnée"""
    check_date = target_date or date.today()
    parquet_path = Path("data/gold") / f"date={check_date:%Y-%m-%d}" / "articles.parquet"

    if parquet_path.exists():
        import pyarrow.parquet as pq

        try:
            num_rows = pq.ParquetFile(parquet_path).metadata.num_rows
            print(f"  ✅ Parquet trouve: {parquet_path}")
            print(f"     {num_rows:,} lignes")
            return True
        except Exception as e:
            print(f"  ⚠️ Parquet existe mais erreur lecture: {e}")
            return False
    else:
        print(f"  ❌ Parquet non trouve: {parquet_path}")
        return False


def get_db_stats(conn: sqlite3.Connection) -> dict:
    """Récupère les statistiques de la base de données"""
    cursor = conn.cursor()

    stats = {}

    # Compter articles
    cursor.execute("SELECT COUNT(*) FROM raw_data")
    stats["raw_data_count"] = cursor.fetchone()[0]

    # Compter topics
    cursor.execute("SELECT COUNT(*) FROM document_topic")
    stats["document_topic_count"] = cursor.fetchone()[0]

    # Compter sentiment
    cursor.execute("SELECT COUNT(*) FROM model_output")
    stats["model_output_count"] = cursor.fetchone()[0]

    # Date la plus ancienne
    cursor.execute("SELECT MIN(collected_at) FROM raw_data")
    oldest = cursor.fetchone()[0]
    stats["oldest_date"] = oldest

    # Date la plus récente
    cursor.execute("SELECT MAX(collected_at) FROM raw_data")
    newest = cursor.fetchone()[0]
    stats["newest_date"] = newest

    return stats


def cleanup_buffer(
    db_path: str, keep_days: int = 7, target_date: date | None = None, dry_run: bool = False
) -> dict:
    """
    Nettoie le buffer SQLite

    Args:
        db_path: Chemin vers la base de données
        keep_days: Nombre de jours à garder (articles plus récents)
        target_date: Date spécifique à nettoyer (optionnel)
        dry_run: Si True, simule sans supprimer

    Returns:
        Dictionnaire avec statistiques de nettoyage
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Statistiques avant nettoyage
    stats_before = get_db_stats(conn)

    print("\n" + "=" * 70)
    print("STATISTIQUES AVANT NETTOYAGE")
    print("=" * 70)
    print(f"Articles (raw_data): {stats_before['raw_data_count']:,}")
    print(f"Topics (document_topic): {stats_before['document_topic_count']:,}")
    print(f"Sentiment (model_output): {stats_before['model_output_count']:,}")
    print(f"Date la plus ancienne: {stats_before['oldest_date']}")
    print(f"Date la plus récente: {stats_before['newest_date']}")

    if target_date:
        # Nettoyer articles d'une date spécifique
        date_str = target_date.isoformat()
        print(f"\nNettoyage articles de la date: {date_str}")

        if not dry_run:
            # Supprimer articles de cette date
            cursor.execute(
                """
                DELETE FROM raw_data
                WHERE date(collected_at) = date(?)
            """,
                (date_str,),
            )
            deleted_raw = cursor.rowcount

            # Nettoyer tables liées
            cursor.execute(
                """
                DELETE FROM document_topic
                WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)
            """
            )
            deleted_topics = cursor.rowcount

            cursor.execute(
                """
                DELETE FROM model_output
                WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)
            """
            )
            deleted_sentiment = cursor.rowcount

            conn.commit()
        else:
            # Simulation
            cursor.execute(
                """
                SELECT COUNT(*) FROM raw_data
                WHERE date(collected_at) = date(?)
            """,
                (date_str,),
            )
            deleted_raw = cursor.fetchone()[0]
            deleted_topics = 0
            deleted_sentiment = 0
    else:
        # Nettoyer articles plus anciens que keep_days
        print(f"\nNettoyage articles plus anciens que {keep_days} jours")

        if not dry_run:
            # Supprimer articles anciens
            cursor.execute(
                """
                DELETE FROM raw_data
                WHERE collected_at < date('now', '-' || ? || ' days')
            """,
                (keep_days,),
            )
            deleted_raw = cursor.rowcount

            # Nettoyer tables liées
            cursor.execute(
                """
                DELETE FROM document_topic
                WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)
            """
            )
            deleted_topics = cursor.rowcount

            cursor.execute(
                """
                DELETE FROM model_output
                WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)
            """
            )
            deleted_sentiment = cursor.rowcount

            conn.commit()
        else:
            # Simulation
            cursor.execute(
                """
                SELECT COUNT(*) FROM raw_data
                WHERE collected_at < date('now', '-' || ? || ' days')
            """,
                (keep_days,),
            )
            deleted_raw = cursor.fetchone()[0]
            deleted_topics = 0
            deleted_sentiment = 0

    # Statistiques après nettoyage
    stats_after = get_db_stats(conn)

    print("\n" + "=" * 70)
    if dry_run:
        print("SIMULATION - STATISTIQUES APRES NETTOYAGE")
    else:
        print("STATISTIQUES APRES NETTOYAGE")
    print("=" * 70)
    print(
        f"Articles (raw_data): {stats_after['raw_data_count']:,} ({stats_before['raw_data_count'] - stats_after['raw_data_count']:,} supprimes)"
    )
    print(
        f"Topics (document_topic): {stats_after['document_topic_count']:,} ({stats_before['document_topic_count'] - stats_after['document_topic_count']:,} supprimes)"
    )
    print(
        f"Sentiment (model_output): {stats_after['model_output_count']:,} ({stats_before['model_output_count'] - stats_after['model_output_count']:,} supprimes)"
    )

    conn.close()

    return {
        "deleted_raw": deleted_raw,
        "deleted_topics": deleted_topics,
        "deleted_sentiment": deleted_sentiment,
        "stats_before": stats_before,
        "stats_after": stats_after,
    }


def main():
    """Fonction principale"""
    print("=" * 70)
    print("NETTOYAGE BUFFER SQLite (datasens.db)")
    print("=" * 70)
    print("\n⚠️ ATTENTION: Ce script supprime des donnees du buffer SQLite")
    print("   Assurez-vous que les donnees sont exportees en Parquet GOLD avant!")
    print()

    # Trouver la base de données
    db_path = get_db_path()
    if not db_path:
        print("ERREUR: Base de donnees datasens.db non trouvee")
        print("   Cherche dans:")
        print("   - Projet: datasens.db")
        print("   - Home: ~/datasens_project/datasens.db")
        print("   - Variable DB_PATH")
        sys.exit(1)

    print(f"Base de donnees trouvee: {db_path}")

    # Vérifier export Parquet
    print("\nVerification export Parquet GOLD...")
    if not check_parquet_export():
        print("\n⚠️ ATTENTION: Aucun export Parquet trouve pour aujourd'hui!")
        confirm = input("   Continuer quand meme? (o/n): ").strip().lower()
        if confirm != "o":
            print("   Nettoyage annule")
            sys.exit(0)

    # Options de nettoyage
    print("\n" + "=" * 70)
    print("OPTIONS DE NETTOYAGE")
    print("=" * 70)
    print("1. Nettoyer articles plus anciens que X jours (defaut: 7 jours)")
    print("2. Nettoyer articles d'une date specifique")
    print("3. Simulation (dry-run) - voir ce qui sera supprime sans supprimer")
    print("0. Annuler")

    choice = input("\nVotre choix: ").strip()

    if choice == "0":
        print("Nettoyage annule")
        sys.exit(0)
    elif choice == "1":
        keep_days_input = input("Nombre de jours a garder (defaut: 7): ").strip()
        keep_days = int(keep_days_input) if keep_days_input else 7

        print(f"\nNettoyage des articles plus anciens que {keep_days} jours...")
        result = cleanup_buffer(db_path, keep_days=keep_days, dry_run=False)

    elif choice == "2":
        date_str = input("Date a nettoyer (YYYY-MM-DD): ").strip()
        try:
            target_date = date.fromisoformat(date_str)
            print(f"\nNettoyage des articles de la date {target_date}...")
            result = cleanup_buffer(db_path, target_date=target_date, dry_run=False)
        except ValueError:
            print("ERREUR: Format date invalide (utiliser YYYY-MM-DD)")
            sys.exit(1)

    elif choice == "3":
        keep_days_input = input("Nombre de jours a garder (defaut: 7): ").strip()
        keep_days = int(keep_days_input) if keep_days_input else 7

        print(f"\nSIMULATION: Nettoyage des articles plus anciens que {keep_days} jours...")
        result = cleanup_buffer(db_path, keep_days=keep_days, dry_run=True)
        print("\n⚠️ SIMULATION - Aucune donnee n'a ete supprimee")
    else:
        print("ERREUR: Choix invalide")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("NETTOYAGE TERMINE")
    print("=" * 70)
    print(f"Articles supprimes: {result['deleted_raw']:,}")
    print(f"Topics supprimes: {result['deleted_topics']:,}")
    print(f"Sentiment supprimes: {result['deleted_sentiment']:,}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nNettoyage interrompu par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
