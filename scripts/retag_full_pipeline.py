#!/usr/bin/env python3
"""Re-tag complet du pipeline avec le tagger v2 (bilingue FR+EN).

Chaîne d'exécution :
  1. Snapshot horodaté des fichiers critiques (SQLite + parquet GoldAI + splits IA)
  2. Résumé avant/après (dry-run intégré) : demande confirmation utilisateur
  3. Re-tag des 61k+ lignes `raw_data` via TopicTagger v2
     (DELETE FROM document_topic puis INSERT propre)
  4. Régénération du GOLD du jour : DataAggregator.aggregate() + GoldExporter.export_all()
  5. Régénération du GoldAI consolidé : scripts/merge_parquet_goldai.py --force-full
  6. Régénération des splits IA : scripts/create_ia_copy.py
  7. Rapport final : distribution topics, temps, chemins de backup

Options CLI :
  --dry-run   : simule uniquement, n'écrit rien en base ni sur disque
  --yes       : ne demande pas la confirmation interactive
  --limit N   : re-tagge seulement N lignes (pour test rapide)
  --skip-gold : ne pas régénérer le GOLD/GoldAI/IA (utile si on veut juste retag SQLite)

Réversibilité : chaque run crée `backups/retag_<timestamp>/` avec tous les
fichiers originaux → restauration possible par simple copie inverse.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from src.config import get_db_path, get_goldai_dir, get_gold_dir  # noqa: E402
from src.e1.aggregator import DataAggregator  # noqa: E402
from src.e1.exporter import GoldExporter  # noqa: E402
from src.e1.tagger import TopicTagger  # noqa: E402


# ---------------------------------------------------------------------------
# Logging sobre (stdout, pas de coloration pour compat Windows PowerShell)
# ---------------------------------------------------------------------------


def info(msg: str) -> None:
    print(f"[retag] {msg}", flush=True)


def step(title: str) -> None:
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}", flush=True)


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------


def make_backup(project_root: Path, timestamp: str) -> Path:
    """Crée un snapshot horodaté des fichiers critiques."""
    backup_root = project_root / "backups" / f"retag_{timestamp}"
    backup_root.mkdir(parents=True, exist_ok=True)

    targets: list[tuple[Path, Path]] = []
    db_path = get_db_path()
    if db_path.exists():
        targets.append((db_path, backup_root / "datasens.db"))

    goldai_dir = get_goldai_dir()
    merged = goldai_dir / "merged_all_dates.parquet"
    if merged.exists():
        targets.append((merged, backup_root / "merged_all_dates.parquet"))

    ia_dir = goldai_dir / "ia"
    for name in ("train.parquet", "val.parquet", "test.parquet"):
        src = ia_dir / name
        if src.exists():
            (backup_root / "ia").mkdir(exist_ok=True)
            targets.append((src, backup_root / "ia" / name))

    today_gold = get_gold_dir() / f"date={date.today():%Y-%m-%d}" / "articles.parquet"
    if today_gold.exists():
        (backup_root / "gold_today").mkdir(exist_ok=True)
        targets.append((today_gold, backup_root / "gold_today" / "articles.parquet"))

    for src, dst in targets:
        shutil.copy2(src, dst)
        info(f"backup : {src.name} -> {dst.relative_to(project_root)}")

    return backup_root


# ---------------------------------------------------------------------------
# Résumé avant/après
# ---------------------------------------------------------------------------


def current_topic_distribution(db_path: Path) -> pd.Series:
    """Distribution actuelle des topics dominants (topic_1) via SQLite."""
    conn = sqlite3.connect(str(db_path))
    q = """
    SELECT t.name AS topic, COUNT(*) AS n
    FROM document_topic dt
    JOIN topic t ON dt.topic_id = t.topic_id
    JOIN (
        SELECT raw_data_id, MIN(document_topic_id) AS first_dt
        FROM document_topic
        GROUP BY raw_data_id
    ) dt_first ON dt.document_topic_id = dt_first.first_dt
    GROUP BY t.name
    ORDER BY n DESC
    """
    try:
        df = pd.read_sql_query(q, conn)
    except Exception:
        # Fallback : pas d'ordre stable par document_topic_id, on prend juste la distribution
        q2 = (
            "SELECT t.name AS topic, COUNT(*) AS n "
            "FROM document_topic dt JOIN topic t ON dt.topic_id = t.topic_id "
            "GROUP BY t.name ORDER BY n DESC"
        )
        df = pd.read_sql_query(q2, conn)
    conn.close()
    return df.set_index("topic")["n"] if len(df) else pd.Series(dtype=int)


def print_distribution(label: str, series: pd.Series, top: int = 25) -> None:
    total = int(series.sum()) if len(series) else 0
    info(f"--- {label} (total={total:,}) ---")
    if not len(series):
        info("  (vide)")
        return
    for name, n in series.head(top).items():
        pct = (n / total * 100) if total else 0.0
        info(f"  {name:<16s} {int(n):>7,} ({pct:5.1f}%)")


# ---------------------------------------------------------------------------
# Re-tag SQLite
# ---------------------------------------------------------------------------


def retag_sqlite(db_path: Path, limit: int | None, dry_run: bool) -> tuple[int, float]:
    """Parcourt raw_data et re-tag toutes les lignes via TopicTagger v2.

    Retourne (nb_lignes_retaggees, duree_secondes).
    """
    info(f"lecture raw_data depuis {db_path}")
    conn = sqlite3.connect(str(db_path))
    q = (
        "SELECT r.raw_data_id, r.title, r.content, s.name AS source_name "
        "FROM raw_data r LEFT JOIN source s ON r.source_id = s.source_id "
        "ORDER BY r.raw_data_id"
    )
    if limit is not None:
        q += f" LIMIT {int(limit)}"
    rows = conn.execute(q).fetchall()
    conn.close()
    info(f"{len(rows):,} lignes à re-tagger")

    if dry_run:
        info("dry-run actif : aucune écriture ne sera effectuée")
        return len(rows), 0.0

    tagger = TopicTagger(str(db_path))
    t0 = time.monotonic()
    for i, (raw_id, title, content, source_name) in enumerate(rows, 1):
        tagger.tag(int(raw_id), title or "", content or "", source_name or "")
        if i % 2000 == 0:
            elapsed = time.monotonic() - t0
            rate = i / elapsed if elapsed else 0.0
            eta = (len(rows) - i) / rate if rate else 0.0
            info(f"  {i:>6,}/{len(rows):,} ({rate:.0f} lignes/s, ETA {eta:.0f}s)")
    tagger.close()
    duration = time.monotonic() - t0
    info(f"re-tag terminé en {duration:.1f}s ({len(rows) / max(duration, 0.001):.0f} lignes/s)")
    return len(rows), duration


# ---------------------------------------------------------------------------
# Régénération GOLD / GoldAI / splits IA
# ---------------------------------------------------------------------------


def regenerate_gold_today(db_path: Path) -> dict:
    """Régénère la partition GOLD du jour à partir de SQLite."""
    info("régénération GOLD du jour (DataAggregator.aggregate -> GoldExporter)")
    agg = DataAggregator(str(db_path))
    df_gold = agg.aggregate()
    agg.close()
    exporter = GoldExporter()
    res = exporter.export_all(df_gold)
    info(f"GOLD : {res['rows']:,} lignes -> {res['parquet']}")
    return res


def run_script(args: list[str]) -> None:
    info(f"exécution : {' '.join(args)}")
    result = subprocess.run(
        args,
        cwd=str(PROJECT_ROOT),
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"[retag] échec de la commande : {' '.join(args)} (code {result.returncode})")


def refresh_ia_labelled_source(goldai_dir: Path) -> None:
    """Synchronise `ia/gold_ia_labelled.parquet` sur `merged_all_dates.parquet`.

    Sans ça, `scripts/create_ia_copy.py` privilégie l'ancien fichier figé et
    les splits train/val/test restent sur les anciens tags v1 même après
    un re-tag complet.
    """
    merged = goldai_dir / "merged_all_dates.parquet"
    labelled_dir = goldai_dir / "ia"
    labelled_dir.mkdir(parents=True, exist_ok=True)
    labelled = labelled_dir / "gold_ia_labelled.parquet"
    if not merged.exists():
        info("warning : merged_all_dates.parquet absent, saut du refresh labelled.")
        return
    shutil.copy2(merged, labelled)
    info(f"refresh : {labelled.name} synchronisé depuis merged_all_dates.parquet")


def regenerate_goldai_and_ia() -> None:
    py = sys.executable
    run_script([py, str(PROJECT_ROOT / "scripts" / "merge_parquet_goldai.py"), "--force-full"])
    # Ré-applique le tagger v2 sur le parquet consolidé : les partitions GOLD
    # historiques sont des snapshots figés, elles restent sur les tags v1
    # jusqu'à ce qu'on ré-inflige le scoring en aval de la fusion.
    run_script([py, str(PROJECT_ROOT / "scripts" / "retag_goldai_consolide.py")])
    # Garantit que la source utilisée par create_ia_copy.py est bien la
    # version fraîche (sinon le script retomberait sur un fichier figé).
    refresh_ia_labelled_source(get_goldai_dir())
    run_script([py, str(PROJECT_ROOT / "scripts" / "create_ia_copy.py")])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Re-tag complet du pipeline DataSens avec le tagger v2."
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Simule sans écrire (affiche juste le volume à traiter).",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Ne pas demander de confirmation interactive.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limiter le re-tag aux N premières lignes raw_data (debug).",
    )
    p.add_argument(
        "--skip-gold",
        action="store_true",
        help="Ne régénérer ni le GOLD du jour, ni GoldAI, ni les splits IA.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    step("DATASENS — Re-tag complet du pipeline (tagger v2)")
    info(f"timestamp run : {timestamp}")
    info(f"racine projet : {PROJECT_ROOT}")
    db_path = get_db_path()
    info(f"base SQLite   : {db_path}")
    info(f"dry-run       : {args.dry_run}")
    if args.limit:
        info(f"limit         : {args.limit}")

    # --- Distribution actuelle
    step("Distribution actuelle (topic_1 dominant)")
    current = current_topic_distribution(db_path)
    print_distribution("AVANT re-tag", current)

    # --- Confirmation
    if not args.dry_run and not args.yes:
        print()
        resp = input("[retag] Confirmer le re-tag complet ? Tapez OUI pour continuer : ")
        if resp.strip().upper() != "OUI":
            info("abandon utilisateur.")
            return 1

    # --- Backup
    backup_path: Path | None = None
    if not args.dry_run:
        step("Snapshot de sécurité")
        backup_path = make_backup(PROJECT_ROOT, timestamp)
        info(f"backup racine : {backup_path}")

    # --- Re-tag
    step("Re-tag SQLite")
    n_rows, duration = retag_sqlite(db_path, args.limit, args.dry_run)

    if args.dry_run:
        info("arrêt à la fin du dry-run (--dry-run).")
        return 0

    # --- Distribution après re-tag SQLite
    step("Distribution après re-tag (topic_1 dominant)")
    new_dist = current_topic_distribution(db_path)
    print_distribution("APRÈS re-tag", new_dist)

    # --- Régénération GOLD / GoldAI / IA
    if args.skip_gold:
        info("--skip-gold : régénération GOLD/GoldAI/IA ignorée.")
    else:
        step("Régénération GOLD (partition du jour)")
        regenerate_gold_today(db_path)
        step("Régénération GoldAI consolidé + splits IA")
        regenerate_goldai_and_ia()

    # --- Rapport final
    step("Rapport final")
    info(f"lignes re-taggées : {n_rows:,}")
    info(f"durée re-tag      : {duration:.1f}s")
    if backup_path is not None:
        info(f"backup disponible : {backup_path.relative_to(PROJECT_ROOT)}")
    info("Terminé. Rafraîchir le cockpit Streamlit pour visualiser l'impact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
