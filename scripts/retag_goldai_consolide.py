"""Re-tagge en place `data/goldai/merged_all_dates.parquet` avec le tagger v2.

Pourquoi :
- Les partitions GOLD historiques sont des snapshots statiques figés.
- Le re-tag SQLite ne touche que la partition du jour régénérée par
  `DataAggregator.aggregate()` → le GoldAI consolidé reste partiellement v1.
- Ce script applique la logique du TopicTagger v2 (dictionnaire bilingue,
  pondération titre ×3, règles par source) directement sur les colonnes
  `title` / `content` / `source` du parquet, puis réécrit topic_1 / topic_2.

Usage :
    python scripts/retag_goldai_consolide.py              # run complet
    python scripts/retag_goldai_consolide.py --limit 500  # échantillon
    python scripts/retag_goldai_consolide.py --dry-run    # sans écriture

Effets :
- backup : backups/retag_goldai_<ts>/merged_all_dates.parquet
- rewrite : data/goldai/merged_all_dates.parquet (topic_1, topic_2 mis à jour)

À relancer derrière pour propager les splits :
    python scripts/create_ia_copy.py
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings  # noqa: E402
from src.e1.tagger import (  # noqa: E402
    MIN_TOPIC2_SCORE,
    SOURCE_RULES,
    TOPIC_KEYWORDS,
    _count_occurrences,
    _strip_accents,
)


def _score_topics(title: str, content: str) -> dict[str, float]:
    title_n = _strip_accents(title or "")
    content_n = _strip_accents(content or "")
    scores: dict[str, float] = {}
    for topic, bundle in TOPIC_KEYWORDS.items():
        all_kw = bundle["fr"] + bundle["en"]
        n_total = len(all_kw) or 1
        title_hits = _count_occurrences(title_n, all_kw)
        content_hits = _count_occurrences(content_n, all_kw)
        weighted = title_hits * 3 + content_hits
        if weighted == 0:
            continue
        scores[topic] = min(weighted / n_total, 1.0)
    return scores


def _source_rule(source_name: str) -> tuple[str, float] | None:
    if not source_name:
        return None
    src_low = source_name.lower()
    for pattern, topic, score in SOURCE_RULES:
        if pattern in src_low:
            return topic, score
    return None


def _tag_row(title: str, content: str, source_name: str) -> tuple[str, str | None, float, float | None]:
    """Retourne (topic_1, topic_2, score_1, score_2). topic_2 peut être None."""
    scores = _score_topics(title, content)
    rule = _source_rule(source_name)
    if rule is not None:
        rule_topic, rule_score = rule
        scores[rule_topic] = max(scores.get(rule_topic, 0.0), rule_score)

    sorted_topics = sorted(scores.items(), key=lambda x: -x[1])
    if not sorted_topics:
        return ("autre", None, 0.3, None)

    t1_name, t1_score = sorted_topics[0]
    t2_name: str | None = None
    t2_score: float | None = None
    if len(sorted_topics) >= 2 and sorted_topics[1][1] >= MIN_TOPIC2_SCORE:
        t2_name, t2_score = sorted_topics[1]

    return (t1_name, t2_name, float(t1_score), t2_score if t2_score is None else float(t2_score))


def _resolve_goldai_dir() -> Path:
    settings = get_settings()
    p = Path(settings.goldai_base_path)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


def _pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Limiter à N lignes pour tester (0 = tout).")
    parser.add_argument("--dry-run", action="store_true", help="Ne réécrit pas le parquet.")
    args = parser.parse_args()

    goldai_dir = _resolve_goldai_dir()
    target = goldai_dir / "merged_all_dates.parquet"
    if not target.exists():
        print(f"ERREUR: {target} introuvable. Lance d'abord merge_parquet_goldai.py --force-full.")
        return 1

    print("=" * 70)
    print("  Re-tag GoldAI consolidé (tagger v2)")
    print("=" * 70)
    print(f"[goldai-retag] cible : {target}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = PROJECT_ROOT / "backups" / f"retag_goldai_{ts}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / "merged_all_dates.parquet"
    if not args.dry_run:
        shutil.copy2(target, backup_path)
        print(f"[goldai-retag] backup : {backup_path}")
    else:
        print("[goldai-retag] dry-run actif, pas de backup ni écriture")

    print("[goldai-retag] lecture parquet ...")
    df = pd.read_parquet(target)
    n_total = len(df)
    print(f"[goldai-retag] {n_total:,} lignes chargées")

    title_col = _pick_column(df, ["title", "headline"])
    content_col = _pick_column(df, ["content", "summary", "description", "body"])
    source_col = _pick_column(df, ["source_name", "source", "feed", "provider"])
    if title_col is None:
        print("ERREUR: aucune colonne de titre détectée (attendu title/headline).")
        return 1
    if content_col is None:
        print("WARNING: aucune colonne de contenu détectée, scoring sur titre uniquement.")
    print(f"[goldai-retag] colonnes utilisées : title={title_col}, content={content_col}, source={source_col}")

    n_iter = min(n_total, args.limit) if args.limit > 0 else n_total
    topic_1_list: list[str] = [""] * n_iter
    topic_2_list: list[str | None] = [None] * n_iter
    conf_1_list: list[float] = [0.0] * n_iter
    conf_2_list: list[float | None] = [None] * n_iter

    t0 = time.time()
    step = max(1000, n_iter // 40)
    for i in range(n_iter):
        row = df.iloc[i]
        title = str(row[title_col]) if title_col and pd.notna(row[title_col]) else ""
        content = str(row[content_col]) if content_col and pd.notna(row[content_col]) else ""
        source = str(row[source_col]) if source_col and pd.notna(row[source_col]) else ""
        t1, t2, s1, s2 = _tag_row(title, content, source)
        topic_1_list[i] = t1
        topic_2_list[i] = t2
        conf_1_list[i] = s1
        conf_2_list[i] = s2

        if (i + 1) % step == 0 or (i + 1) == n_iter:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (n_iter - (i + 1)) / rate if rate > 0 else 0
            print(f"[goldai-retag]   {i + 1:>7,}/{n_iter:,} ({rate:.0f} lignes/s, ETA {eta:.0f}s)")

    print(f"[goldai-retag] scoring terminé en {time.time() - t0:.1f}s")

    # Distribution avant / après (sur la partie re-taggée)
    old_t1 = df[_pick_column(df, ["topic_1"]) or "topic_1"].head(n_iter).astype(str).str.strip().str.lower()
    new_t1 = pd.Series(topic_1_list).astype(str).str.strip().str.lower()

    print()
    print("--- Distribution AVANT (topic_1 sur les lignes re-taggées) ---")
    for name, n in old_t1.value_counts().head(8).items():
        print(f"  {name:<18s} {int(n):>7,}")
    print("--- Distribution APRÈS (topic_1 v2) ---")
    for name, n in new_t1.value_counts().head(8).items():
        print(f"  {name:<18s} {int(n):>7,}")
    n_autre_new = int((new_t1 == "autre").sum())
    print(f"\n[goldai-retag] autre (après) : {n_autre_new:,} ({n_autre_new/n_iter*100:.1f}%)")

    if args.dry_run:
        print("[goldai-retag] dry-run : pas d'écriture du parquet.")
        return 0

    # Applique les colonnes. Pour conserver l'intégrité du parquet si --limit
    # est utilisé, on ne touche que les n_iter premières lignes.
    if args.limit > 0 and args.limit < n_total:
        df_tail = df.iloc[n_iter:].copy()
        df = df.iloc[:n_iter].copy()
        df["topic_1"] = topic_1_list
        df["topic_2"] = topic_2_list
        if "topic_1_confidence" in df.columns or "topic_2_confidence" in df.columns:
            df["topic_1_confidence"] = conf_1_list
            df["topic_2_confidence"] = conf_2_list
        df = pd.concat([df, df_tail], ignore_index=True)
    else:
        df["topic_1"] = topic_1_list
        df["topic_2"] = topic_2_list
        if "topic_1_confidence" in df.columns:
            df["topic_1_confidence"] = conf_1_list
        if "topic_2_confidence" in df.columns:
            df["topic_2_confidence"] = conf_2_list

    df.to_parquet(target, index=False)
    print(f"[goldai-retag] parquet réécrit : {target} ({len(df):,} lignes)")
    print(f"[goldai-retag] backup disponible : {backup_path}")
    print()
    print("Étape suivante : relancer les splits IA")
    print("  .\\.venv\\Scripts\\python.exe scripts\\create_ia_copy.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
