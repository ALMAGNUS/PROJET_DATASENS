"""
Trace par les lignes - preuve directe du lineage de la donnée.

Affiche les MEMES lignes physiques (identifiées par `fingerprint`) telles qu'elles
existent dans :
  1. SQLite `raw_data` (stockage opérationnel temps réel)
  2. Parquet GOLD du jour (snapshot enrichi quotidien)
  3. Parquet GoldAI consolidé (stock IA all-time)
  4. Parquet lu depuis MongoDB GridFS (sauvegarde long terme)

Utilité : montrer qu'un même article voyage de bout en bout, et qu'on peut le
récupérer depuis chaque couche par sa clé naturelle (`fingerprint`).
"""

from __future__ import annotations

import io
import os
import sqlite3
from collections.abc import Iterable
from pathlib import Path

import pandas as pd
import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
    mongo_get_file_bytes,
    mongo_status,
)

# Colonnes affichées par étape, dans l'ordre de lecture.
_RAW_COLUMNS = [
    "raw_data_id",
    "fingerprint",
    "title",
    "url",
    "collected_at",
    "quality_score",
]
_GOLD_COLUMNS = [
    "fingerprint",
    "title",
    "url",
    "source_type",
    "topic_1",
    "sentiment",
    "sentiment_score",
    "collected_at",
]
_GOLDAI_COLUMNS = [
    "fingerprint",
    "raw_data_id",
    "title",
    "url",
    "topic_1",
    "sentiment",
    "processed_at",
    "pipeline_version",
]


def _resolve_db_path() -> Path | None:
    """Résout le chemin SQLite à partir de DB_PATH ou de la config par défaut."""
    candidate = os.getenv("DB_PATH")
    if candidate and Path(candidate).exists():
        return Path(candidate)
    home_default = Path.home() / "datasens_project" / "datasens.db"
    if home_default.exists():
        return home_default
    project_default = Path.cwd() / "datasens.db"
    return project_default if project_default.exists() else None


def _resolve_latest_gold_parquet(root: Path) -> tuple[Path | None, str | None]:
    """Retourne (chemin du dernier `articles.parquet` GOLD, date au format YYYY-MM-DD)."""
    base = root / "data" / "gold"
    if not base.exists():
        return None, None
    candidates: list[tuple[str, Path]] = []
    for d in base.iterdir():
        if not d.is_dir() or not d.name.startswith("date="):
            continue
        partition = d.name.split("=", 1)[1]
        parquet = d / "articles.parquet"
        if parquet.exists():
            candidates.append((partition, parquet))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: x[0])
    partition, path = candidates[-1]
    return path, partition


@st.cache_data(ttl=60, show_spinner=False)
def _sample_recent_raw(db_path: str, sample_size: int, _cache_buster: int = 0) -> pd.DataFrame:
    """N articles SQLite les plus récents avec colonnes brutes."""
    if not db_path or not Path(db_path).exists():
        return pd.DataFrame()
    cols = ",".join(_RAW_COLUMNS)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                f"SELECT {cols} FROM raw_data "
                "WHERE fingerprint IS NOT NULL AND fingerprint != '' "
                "ORDER BY raw_data_id DESC LIMIT ?",
                (int(sample_size),),
            ).fetchall()
            return pd.DataFrame([dict(r) for r in rows])
        finally:
            conn.close()
    except Exception as exc:
        st.warning(f"Lecture SQLite impossible : {exc!s}")
        return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def _filter_parquet(path: str, fingerprints: tuple[str, ...], columns: tuple[str, ...]) -> pd.DataFrame:
    """Lit le parquet, filtre sur fingerprint, retourne les colonnes demandées."""
    if not path or not Path(path).exists():
        return pd.DataFrame()
    try:
        df = pd.read_parquet(path, columns=list(columns))
    except Exception:
        df = pd.read_parquet(path)
        keep = [c for c in columns if c in df.columns]
        df = df[keep] if keep else df
    if "fingerprint" not in df.columns:
        return pd.DataFrame()
    return df[df["fingerprint"].isin(fingerprints)].copy()


def _filter_gridfs(
    root: Path,
    file_id: str,
    fingerprints: tuple[str, ...],
    columns: tuple[str, ...],
) -> pd.DataFrame:
    """Télécharge un parquet depuis GridFS, le lit en mémoire et filtre."""
    payload, _meta, _filename = mongo_get_file_bytes(root, file_id)
    if not payload:
        return pd.DataFrame()
    try:
        df = pd.read_parquet(io.BytesIO(payload))
    except Exception as exc:
        st.warning(f"Lecture parquet GridFS impossible : {exc!s}")
        return pd.DataFrame()
    if "fingerprint" not in df.columns:
        return pd.DataFrame()
    keep = [c for c in columns if c in df.columns]
    df = df[df["fingerprint"].isin(fingerprints)].copy()
    return df[keep] if keep else df


def _resolve_gridfs_file_id(mongo: dict, logical_name: str) -> tuple[str | None, dict | None]:
    """Cherche dans `mongo_status.files` le fichier le plus récent correspondant au nom logique."""
    if not mongo or not mongo.get("connected"):
        return None, None
    files = mongo.get("files", []) or []
    matches = []
    for f in files:
        meta = f.get("metadata", {}) or {}
        if meta.get("logical_name") == logical_name or (f.get("filename") or "").endswith(
            f"{logical_name}.parquet"
        ):
            matches.append(f)
    if not matches:
        return None, None
    matches.sort(key=lambda x: x.get("uploadDate") or "", reverse=True)
    top = matches[0]
    file_id = str(top.get("_id") or top.get("id") or "")
    return (file_id or None), top


def _format_dataframe(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Réordonne les colonnes et tronque les longs textes pour l'affichage."""
    if df.empty:
        return df
    keep = [c for c in columns if c in df.columns]
    df = df[keep].copy() if keep else df
    for col in ("title", "url"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.slice(0, 80)
    return df


def render_row_trace(ctx: PageContext, default_sample: int = 5) -> None:
    """
    Panneau "Trace par les lignes" : montre les MEMES articles dans les 4 couches.
    """
    st.markdown("### Trace par les lignes")
    st.caption(
        "Mêmes articles physiques (clé `fingerprint`) lus dans chaque couche du lineage. "
        "Preuve directe que la donnée traverse SQLite → Parquet GOLD → GoldAI → GridFS sans perte."
    )

    project_root = ctx.project_root
    db_path = _resolve_db_path()
    if db_path is None:
        st.warning("Base SQLite introuvable. Lancez `python main.py` pour initialiser le pipeline.")
        return

    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        sample_size = st.slider(
            "Articles à tracer", min_value=3, max_value=15, value=default_sample, step=1, key="row_trace_n"
        )
    with col_b:
        cache_buster = st.session_state.get("row_trace_buster", 0)
        if st.button("Rafraîchir l'échantillon", key="row_trace_refresh"):
            st.session_state["row_trace_buster"] = cache_buster + 1
            cache_buster += 1
    with col_c:
        st.caption(
            "L'échantillon prend les `raw_data_id` les plus récents. "
            "Cliquez `Rafraîchir` pour relancer la requête SQLite."
        )

    raw_df = _sample_recent_raw(str(db_path), sample_size, cache_buster)
    if raw_df.empty:
        st.warning("Aucune ligne SQLite récente avec `fingerprint`. Lancez le pipeline `main.py`.")
        return

    fingerprints = tuple(raw_df["fingerprint"].astype(str).tolist())
    st.caption(f"Échantillon : `{len(fingerprints)}` fingerprints — clé universelle conservée à toutes les étapes.")

    gold_path, gold_partition = _resolve_latest_gold_parquet(project_root)
    goldai_path = project_root / "data" / "goldai" / "merged_all_dates.parquet"
    if not goldai_path.exists():
        goldai_path = None

    gold_df = (
        _filter_parquet(str(gold_path), fingerprints, tuple(_GOLD_COLUMNS))
        if gold_path
        else pd.DataFrame()
    )
    goldai_df = (
        _filter_parquet(str(goldai_path), fingerprints, tuple(_GOLDAI_COLUMNS))
        if goldai_path
        else pd.DataFrame()
    )

    mongo = mongo_status(project_root)
    mongo_connected = bool(mongo.get("connected"))
    gridfs_logical = f"gold_articles_{gold_partition}" if gold_partition else None
    gridfs_file_id: str | None = None
    gridfs_meta: dict | None = None
    gridfs_df = pd.DataFrame()
    if mongo_connected and gridfs_logical:
        gridfs_file_id, gridfs_meta = _resolve_gridfs_file_id(mongo, gridfs_logical)
        if gridfs_file_id:
            gridfs_df = _filter_gridfs(
                project_root, gridfs_file_id, fingerprints, tuple(_GOLD_COLUMNS)
            )

    counts = {
        "SQLite raw_data": len(raw_df),
        f"Parquet GOLD ({gold_partition or 'aucun'})": len(gold_df),
        "Parquet GoldAI consolidé": len(goldai_df),
        "GridFS MongoDB": len(gridfs_df),
    }
    summary = pd.DataFrame(
        {
            "Source": list(counts.keys()),
            "Lignes retrouvées": list(counts.values()),
            "Sur l'échantillon": [f"{v}/{len(fingerprints)}" for v in counts.values()],
        }
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)

    if not mongo_connected:
        st.info(
            "MongoDB hors ligne : la 4ème étape (GridFS) reste vide. "
            "Démarrez le service Mongo puis cliquez `Rafraîchir l'échantillon`."
        )

    tabs = st.tabs(
        [
            f"1. SQLite raw_data ({len(raw_df)})",
            f"2. Parquet GOLD {gold_partition or 'absent'} ({len(gold_df)})",
            f"3. Parquet GoldAI consolidé ({len(goldai_df)})",
            f"4. GridFS MongoDB ({len(gridfs_df)})",
        ]
    )

    with tabs[0]:
        st.caption(
            f"Source : `{db_path}` — table `raw_data` — colonnes brutes. "
            "Aucun enrichissement à ce stade."
        )
        st.dataframe(_format_dataframe(raw_df, _RAW_COLUMNS), use_container_width=True, hide_index=True)

    with tabs[1]:
        if gold_path:
            st.caption(
                f"Source : `data/gold/date={gold_partition}/articles.parquet` — "
                "schéma enrichi (topic, sentiment, source_type)."
            )
        else:
            st.warning("Aucun Parquet GOLD partitionné disponible. Lancez `python main.py`.")
        st.dataframe(_format_dataframe(gold_df, _GOLD_COLUMNS), use_container_width=True, hide_index=True)

    with tabs[2]:
        if goldai_path:
            st.caption(
                "Source : `data/goldai/merged_all_dates.parquet` — stock IA all-time, "
                "avec `processed_at` et `pipeline_version`."
            )
        else:
            st.warning("Stock GoldAI consolidé absent. Lancez `scripts/merge_parquet_goldai.py`.")
        st.dataframe(_format_dataframe(goldai_df, _GOLDAI_COLUMNS), use_container_width=True, hide_index=True)

    with tabs[3]:
        if not mongo_connected:
            st.warning("Mongo hors ligne. Pas de lecture GridFS possible.")
        elif not gridfs_file_id:
            st.warning(
                f"Aucun fichier `{gridfs_logical}` archivé dans GridFS. "
                "Lancez `python scripts/backup_parquet_to_mongo.py`."
            )
        else:
            size_mb = (gridfs_meta or {}).get("metadata", {}).get("size_mb")
            archived_at = (gridfs_meta or {}).get("uploadDate")
            st.caption(
                f"Source : GridFS MongoDB → `{gridfs_logical}` (file_id `{gridfs_file_id[:8]}…`)"
                + (f" — {size_mb} MB" if size_mb else "")
                + (f" — archivé le {archived_at}" if archived_at else "")
                + ". Téléchargement bytes → lecture parquet en mémoire → filtre fingerprint."
            )
            st.dataframe(
                _format_dataframe(gridfs_df, _GOLD_COLUMNS),
                use_container_width=True,
                hide_index=True,
            )

    if mongo_connected and gridfs_file_id and not gridfs_df.empty:
        common = set(raw_df["fingerprint"]) & set(gridfs_df["fingerprint"])
        st.success(
            f"Lineage validé : {len(common)}/{len(fingerprints)} `fingerprint` retrouvés "
            "depuis SQLite jusqu'au fichier physique archivé dans GridFS."
        )
    elif gold_df.shape[0] and goldai_df.shape[0]:
        common = set(raw_df["fingerprint"]) & set(gold_df["fingerprint"]) & set(goldai_df["fingerprint"])
        st.info(
            f"Lineage local validé : {len(common)}/{len(fingerprints)} `fingerprint` "
            "retrouvés sur les 3 couches locales (la 4ème étape GridFS est facultative)."
        )
