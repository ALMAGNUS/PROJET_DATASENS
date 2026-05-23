"""Contexte riche pour analyse croisée Mistral (météo, politique, économie, crises)."""

from __future__ import annotations

import re

import pandas as pd

from src.insights.goldai_data import (
    _ECONOMIC_SOURCES,
    add_date_column,
    filter_sources,
    filter_theme_df,
    latest_weather_rows,
    mean_score,
    sentiment_distribution,
)

_CRISIS_PATTERNS: dict[str, list[str]] = {
    "Intempéries (inondations, crues)": ["inond", "crue", "submers", "débord", "inondation"],
    "Canicule / sécheresse": ["canicule", "sécheresse", "vague de chaleur", "chaleur extrême"],
    "Épidémies / santé publique": ["épidém", "epidem", "hantavirus", "pandém", "contamination", "virus"],
    "Sécurité / insécurité": ["insécurité", "casse", "violence urbaine", "attentat"],
    "Environnement": ["pollution", "biodivers", "climat", "réchauffement"],
}


def _text_series(df: pd.DataFrame) -> pd.Series:
    parts = []
    if "title" in df.columns:
        parts.append(df["title"].astype(str))
    if "content" in df.columns:
        parts.append(df["content"].astype(str))
    if not parts:
        return pd.Series(dtype=str)
    if len(parts) == 1:
        return parts[0].str.lower()
    return (parts[0] + " " + parts[1]).str.lower()


def scan_crisis_signals(df: pd.DataFrame, limit_titles: int = 3) -> list[dict]:
    """Repère articles liés intempéries, épidémies, etc. (titres uniquement — perf)."""
    if len(df) == 0 or "title" not in df.columns:
        return []
    text = df["title"].astype(str).str.lower()
    out: list[dict] = []
    for label, patterns in _CRISIS_PATTERNS.items():
        mask = pd.Series(False, index=df.index)
        for pat in patterns:
            mask |= text.str.contains(pat, na=False, regex=False)
        sub = df[mask]
        if len(sub) == 0:
            continue
        titles = sub["title"].astype(str).head(limit_titles).tolist() if "title" in sub.columns else []
        sc = mean_score(sub)
        dist = sentiment_distribution(sub)
        dom = max(dist.items(), key=lambda x: x[1]["count"])[0] if dist else "—"
        out.append(
            {
                "theme": label,
                "count": len(sub),
                "dominant_sentiment": dom,
                "mean_score": sc,
                "sample_titles": [t[:100] for t in titles if t.strip()],
            }
        )
    return sorted(out, key=lambda x: -x["count"])


def topic_snapshot(df: pd.DataFrame, top_n: int = 6) -> list[tuple[str, int]]:
    if "topic_1" not in df.columns or len(df) == 0:
        return []
    vc = df["topic_1"].dropna().value_counts().head(top_n)
    return [(str(k), int(v)) for k, v in vc.items()]


def build_cross_context_block(
    df_full: pd.DataFrame,
    df_theme: pd.DataFrame,
    theme: str,
    theme_label: str,
    cards: list[dict],
) -> str:
    """Assemble le bloc factuel envoyé à Mistral pour croisement analytique."""
    lines: list[str] = [
        f"Question utilisateur : thème {theme_label}",
        f"Corpus thème filtré : {len(df_theme):,} articles",
    ]

    dist = sentiment_distribution(df_theme)
    if dist:
        parts = [f"{k}={v['count']} ({v['pct']:.0%})" for k, v in dist.items()]
        lines.append(f"Sentiment {theme_label} : " + " | ".join(parts))
    ms = mean_score(df_theme)
    if ms is not None:
        lines.append(f"Score moyen continu {theme_label} : {ms:+.3f}")

    for card in cards:
        if card.get("type") in ("weather", "economy", "trend", "risk"):
            lines.append(f"[{card['title']}] {card['summary']}")

    weather = latest_weather_rows(df_full, limit=6)
    if len(weather) > 0 and "title" in weather.columns:
        lines.append("Bulletins météo récents (source OpenWeather/Météo dans GoldAI) :")
        for t in weather["title"].astype(str).head(5):
            lines.append(f"  - {t[:120]}")

    dt_theme = add_date_column(df_theme)
    if "_dt" in dt_theme.columns and len(dt_theme) > 10:
        recent = dt_theme.nlargest(min(7, len(dt_theme)), "_dt")
        if "title" in recent.columns:
            lines.append("Titres récents (thème) :")
            for t in recent["title"].astype(str).head(4):
                if t.strip():
                    lines.append(f"  - {t[:100]}")

    crises = scan_crisis_signals(df_full, limit_titles=2)
    if crises:
        lines.append("Signaux crise / événements dans tout GoldAI :")
        for c in crises[:6]:
            titles = "; ".join(c["sample_titles"][:2]) if c["sample_titles"] else "—"
            sc = f", score {c['mean_score']:+.2f}" if c["mean_score"] is not None else ""
            lines.append(
                f"  - {c['theme']} : {c['count']} articles, dominant {c['dominant_sentiment']}{sc}. "
                f"Ex. titres : {titles}"
            )
    else:
        lines.append("Signaux crise : aucun mot-clé inondation/épidémie/hantavirus détecté dans les titres/contenus.")

    topics = topic_snapshot(df_theme)
    if topics:
        lines.append("Topics dominants : " + " | ".join(f"{t} ({n})" for t, n in topics))

    eco = filter_sources(df_full, _ECONOMIC_SOURCES)
    if len(eco) > 0:
        ed = sentiment_distribution(eco)
        eco_dom = max(ed.items(), key=lambda x: x[1]["count"])[0] if ed else "—"
        lines.append(f"Flux économique (Yahoo/INSEE) : {len(eco):,} articles, sentiment dominant {eco_dom}")

    df_pol = filter_theme_df(df_full, "politique")
    df_fin = filter_theme_df(df_full, "financier")
    if theme != "politique" and len(df_pol) > 0:
        d = sentiment_distribution(df_pol)
        dom = max(d.items(), key=lambda x: x[1]["count"])[0] if d else "—"
        lines.append(f"Rappel politique (croisement) : {len(df_pol):,} art., dominant {dom}")
    if theme != "financier" and len(df_fin) > 0:
        d = sentiment_distribution(df_fin)
        dom = max(d.items(), key=lambda x: x[1]["count"])[0] if d else "—"
        lines.append(f"Rappel financier (croisement) : {len(df_fin):,} art., dominant {dom}")

    return "\n".join(lines)
