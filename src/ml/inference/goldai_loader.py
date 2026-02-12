"""
GoldAI Loader - ML Inference
=============================
Charge les données GoldAI (Parquet) pour l'inférence ML.
Source: data/goldai/merged_all_dates.parquet ou data/goldai/date=YYYY-MM-DD/
"""

from pathlib import Path

import pandas as pd

from src.config import get_goldai_dir, get_settings

_settings = get_settings()


def load_goldai(
    limit: int | None = None,
    use_merged: bool = True,
    date: str | None = None,
) -> pd.DataFrame:
    """
    Charge les données GoldAI pour l'inférence ML.

    Args:
        limit: Nombre max de lignes (None = tout)
        use_merged: True = merged_all_dates.parquet, False = partitions par date
        date: Si use_merged=False, date au format YYYY-MM-DD

    Returns:
        DataFrame avec colonnes: id, source, title, content, sentiment, topic_1, topic_2, etc.

    Raises:
        FileNotFoundError: Si GoldAI n'existe pas
    """
    base = Path(_settings.goldai_base_path)
    if not base.exists():
        base = get_goldai_dir()
    base = base.resolve()

    if use_merged:
        path = base / "merged_all_dates.parquet"
        if not path.exists():
            raise FileNotFoundError(
                f"GoldAI merged not found: {path}. "
                "Run: python scripts/merge_parquet_goldai.py"
            )
        df = pd.read_parquet(path)
    else:
        if not date:
            raise ValueError("date required when use_merged=False")
        path = base / f"date={date}" / "goldai.parquet"
        if not path.exists():
            raise FileNotFoundError(f"GoldAI partition not found: {path}")
        df = pd.read_parquet(path)

    if limit:
        df = df.head(limit)

    return df


def get_goldai_texts(df: pd.DataFrame) -> list[tuple[int, str, str]]:
    """
    Extrait (id, title, content) pour chaque article.

    Args:
        df: DataFrame GoldAI

    Returns:
        Liste de (id, title, content)
    """
    id_col = "id" if "id" in df.columns else df.columns[0]
    title_col = "title" if "title" in df.columns else "headline"
    content_col = "content" if "content" in df.columns else "text"

    if title_col not in df.columns:
        title_col = df.columns[1] if len(df.columns) > 1 else "title"
    if content_col not in df.columns:
        content_col = df.columns[2] if len(df.columns) > 2 else "content"

    results = []
    for _, row in df.iterrows():
        aid = int(row.get(id_col, 0)) if pd.notna(row.get(id_col)) else 0
        title = str(row.get(title_col, "") or "")[:500]
        content = str(row.get(content_col, "") or "")[:2000]
        text = f"{title} {content}".strip()
        if text:
            results.append((aid, title, text))
    return results
