"""Chargement GoldAI enrichi (prédictions + sentiment) pour les insights."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_THEME_KEYWORDS = {
    "politique": ["politiqu", "gouvern", "election", "president", "parti", "senat", "assemblee", "ministre"],
    "financier": ["financ", "economie", "econom", "bourse", "marche", "inflation", "bce", "fed", "taux", "banque"],
    "utilisateurs": [],
}

_PARTICIPATORY_SOURCES = {"reddit_france", "trustpilot_reviews", "monavis_citoyen", "agora_consultations"}
_MEDIA_SOURCES = {"rss_french_news", "google_news_rss", "yahoo_finance", "gdelt_events"}
_ECONOMIC_SOURCES = {"yahoo_finance", "insee_indicators", "datagouv_datasets"}
_WEATHER_SOURCES = {"openweather_api", "open_meteo"}

_goldai_memory_cache: tuple[str, pd.DataFrame, str] | None = None
_crisis_memory_cache: tuple[str, list[dict]] | None = None


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _mtime(path: Path) -> float:
    return path.stat().st_mtime if path.exists() else 0.0


def goldai_cache_key() -> str:
    """Clé d'invalidation cache (mtime des parquets GoldAI)."""
    root = _project_root() / "data" / "goldai"
    app_input = root / "app" / "gold_app_input.parquet"
    legacy = root / "merged_all_dates.parquet"
    pred_dir = root / "predictions"
    pred_mtime = 0.0
    if pred_dir.exists():
        candidates = sorted(
            pred_dir.glob("date=*/run=*/predictions.parquet"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            pred_mtime = _mtime(candidates[0])
    return f"{_mtime(app_input)}|{pred_mtime}|{_mtime(legacy)}"


def _normalize_ids(df: pd.DataFrame, col: str = "id") -> pd.DataFrame:
    if col not in df.columns:
        return df
    out = df.copy()
    out[col] = (
        out[col].astype("string").str.strip().fillna("").replace({"<NA>": "", "nan": "", "None": ""})
    )
    return out


def load_enriched_goldai() -> tuple[pd.DataFrame, str]:
    """Charge gold_app_input + dernières prédictions (+ fallback legacy sentiment)."""
    global _goldai_memory_cache
    cache_key = goldai_cache_key()
    if _goldai_memory_cache and _goldai_memory_cache[0] == cache_key:
        return _goldai_memory_cache[1], _goldai_memory_cache[2]

    root = _project_root()
    goldai_root = root / "data" / "goldai"
    app_input_path = goldai_root / "app" / "gold_app_input.parquet"
    pred_dir = goldai_root / "predictions"
    pred_candidates = (
        sorted(pred_dir.glob("date=*/run=*/predictions.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)
        if pred_dir.exists()
        else []
    )
    latest_pred_path = pred_candidates[0] if pred_candidates else None
    data_label = "GoldAI merged (legacy)"

    if app_input_path.exists() and latest_pred_path is not None:
        df = _normalize_ids(pd.read_parquet(app_input_path))
        pred_df = _normalize_ids(pd.read_parquet(latest_pred_path))
        pred_cols = [c for c in ["id", "predicted_sentiment", "predicted_sentiment_score", "confidence"] if c in pred_df.columns]
        pred_df = pred_df[pred_cols].drop_duplicates(subset=["id"], keep="last")
        df = df.merge(pred_df, on="id", how="left")
        coverage = float(df["predicted_sentiment"].notna().mean()) if "predicted_sentiment" in df.columns else 0.0
        if coverage < 0.3:
            legacy_path = goldai_root / "merged_all_dates.parquet"
            if legacy_path.exists() and "id" in pd.read_parquet(legacy_path, columns=["id"]).columns:
                legacy_df = _normalize_ids(
                    pd.read_parquet(legacy_path, columns=["id", "sentiment", "sentiment_score"])
                ).drop_duplicates(subset=["id"], keep="last")
                df = df.merge(
                    legacy_df.rename(columns={"sentiment": "sentiment_legacy", "sentiment_score": "sentiment_score_legacy"}),
                    on="id",
                    how="left",
                )
            if "predicted_sentiment" in df.columns:
                df["sentiment"] = df["predicted_sentiment"].fillna(df.get("sentiment_legacy"))
            if "predicted_sentiment_score" in df.columns:
                df["sentiment_score"] = df["predicted_sentiment_score"].fillna(df.get("sentiment_score_legacy"))
            data_label = f"GoldAI app + predictions ({coverage:.0%}) + legacy"
        else:
            if "predicted_sentiment" in df.columns:
                df["sentiment"] = df["predicted_sentiment"]
            if "predicted_sentiment_score" in df.columns:
                df["sentiment_score"] = df["predicted_sentiment_score"]
            data_label = f"GoldAI app + predictions ({coverage:.0%})"
    else:
        goldai_path = goldai_root / "merged_all_dates.parquet"
        if not goldai_path.exists():
            gold_dir = root / "data" / "gold"
            if gold_dir.exists():
                for d in sorted(gold_dir.iterdir(), reverse=True):
                    if d.is_dir() and d.name.startswith("date="):
                        p = d / "articles.parquet"
                        if p.exists():
                            goldai_path = p
                            break
        if not goldai_path.exists():
            raise FileNotFoundError("Aucune donnée GoldAI disponible.")
        df = pd.read_parquet(goldai_path)
        data_label = "GoldAI merged / GOLD fallback"

    _goldai_memory_cache = (cache_key, df, data_label)
    return df, data_label


def get_crisis_signals_cached(df: pd.DataFrame) -> list[dict]:
    """Signaux crise mis en cache (recalcul si parquet GoldAI change)."""
    global _crisis_memory_cache
    from src.insights.cross_context import scan_crisis_signals

    cache_key = goldai_cache_key()
    if _crisis_memory_cache and _crisis_memory_cache[0] == cache_key:
        return _crisis_memory_cache[1]
    signals = scan_crisis_signals(df)
    _crisis_memory_cache = (cache_key, signals)
    return signals


def filter_theme_df(df: pd.DataFrame, theme: str) -> pd.DataFrame:
    kws = _THEME_KEYWORDS.get(theme.lower(), [])
    if not kws or "topic_1" not in df.columns:
        return df
    mask = df["topic_1"].astype(str).str.lower().str.contains("|".join(kws), na=False)
    if "title" in df.columns:
        mask |= df["title"].astype(str).str.lower().str.contains("|".join(kws), na=False)
    if mask.sum() > 10:
        return df[mask].copy()
    return df


def add_date_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ("published_at", "collected_at"):
        if col in out.columns:
            out["_dt"] = pd.to_datetime(out[col], errors="coerce")
            return out.dropna(subset=["_dt"])
    return out


def mean_score(df: pd.DataFrame) -> float | None:
    if "sentiment_score" not in df.columns or len(df) == 0:
        return None
    val = df["sentiment_score"].mean()
    return None if pd.isna(val) else float(val)


def sentiment_distribution(df: pd.DataFrame) -> dict[str, dict]:
    if "sentiment" not in df.columns or len(df) == 0:
        return {}
    total = len(df)
    sv = df["sentiment"].value_counts()
    return {str(k): {"count": int(v), "pct": float(v) / total} for k, v in sv.items()}


def filter_sources(df: pd.DataFrame, sources: set[str]) -> pd.DataFrame:
    if "source" not in df.columns:
        return df.iloc[0:0]
    return df[df["source"].astype(str).isin(sources)].copy()


def latest_weather_rows(df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    if "source" not in df.columns:
        return df.iloc[0:0]
    mask = df["source"].astype(str).isin(_WEATHER_SOURCES)
    if "topic_1" in df.columns:
        mask |= df["topic_1"].astype(str).str.lower().eq("meteo")
    w = df[mask].copy()
    if len(w) == 0:
        return w
    w = add_date_column(w) if "_dt" not in w.columns else w
    if "_dt" in w.columns:
        w = w.sort_values("_dt", ascending=False)
    return w.head(limit)
