"""Construction d'insights métier multi-cartes (croisements GoldAI)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

from src.insights.cross_context import build_cross_context_block
from src.insights.mistral_synthesis import mistral_cross_analysis
from src.insights.goldai_data import (
    _ECONOMIC_SOURCES,
    _MEDIA_SOURCES,
    _PARTICIPATORY_SOURCES,
    add_date_column,
    filter_sources,
    filter_theme_df,
    get_crisis_signals_cached,
    latest_weather_rows,
    load_enriched_goldai,
    mean_score,
    sentiment_distribution,
)


@dataclass
class InsightPack:
    reply: str
    insights: list[dict] = field(default_factory=list)
    data_label: str = ""


def _card(card_id: str, card_type: str, title: str, summary: str, facts: dict | None = None) -> dict:
    return {
        "id": card_id,
        "type": card_type,
        "title": title,
        "summary": summary,
        "facts": facts or {},
    }


def _dominant(dist: dict[str, dict]) -> tuple[str, float]:
    if not dist:
        return "—", 0.0
    best = max(dist.items(), key=lambda x: x[1]["count"])
    return best[0], best[1]["pct"]


def _neg_pct(dist: dict[str, dict]) -> float:
    total_neg = 0.0
    for label, info in dist.items():
        if any(x in str(label).lower() for x in ("neg", "nég", "negative")):
            total_neg += info["pct"]
    return total_neg


def _risk_score(neg_pct: float) -> int:
    if neg_pct >= 0.45:
        return 8
    if neg_pct >= 0.35:
        return 6
    if neg_pct >= 0.25:
        return 4
    return 2


def _temporal_trend(df: pd.DataFrame) -> dict | None:
    if "sentiment_score" not in df.columns:
        return None
    dt = add_date_column(df)
    if "_dt" not in dt.columns or len(dt) < 20:
        return None
    median = dt["_dt"].median()
    recent = dt[dt["_dt"] >= median]["sentiment_score"].mean()
    old = dt[dt["_dt"] < median]["sentiment_score"].mean()
    if pd.isna(recent) or pd.isna(old):
        return None
    trend = "hausse" if recent > old + 0.05 else ("baisse" if recent < old - 0.05 else "stable")
    return {"score_recent": float(recent), "score_old": float(old), "trend": trend}


def _weather_cross(df_full: pd.DataFrame, df_theme: pd.DataFrame) -> dict | None:
    weather = latest_weather_rows(df_full, limit=8)
    if len(weather) == 0:
        return None

    cities: list[str] = []
    for title in weather.get("title", pd.Series(dtype=str)).astype(str).head(5):
        m = re.search(r"meteo\s+([A-Za-zÀ-ÿ\-]+)", title, re.I)
        if m:
            cities.append(m.group(1))

    w_score = mean_score(weather)
    t_score = mean_score(df_theme)
    w_dist = sentiment_distribution(weather)
    w_dom, w_pct = _dominant(w_dist)

    # Croisement temporel : même semaine
    overlap_note = ""
    dt_full = add_date_column(df_full)
    dt_theme = add_date_column(df_theme)
    if "_dt" in dt_full.columns and "_dt" in dt_theme.columns and len(weather) > 0:
        w_dt = add_date_column(weather)
        if "_dt" in w_dt.columns:
            latest_w = w_dt["_dt"].max()
            week_start = latest_w - pd.Timedelta(days=7)
            theme_week = dt_theme[(dt_theme["_dt"] >= week_start) & (dt_theme["_dt"] <= latest_w)]
            if len(theme_week) > 0:
                tw_score = mean_score(theme_week)
                if tw_score is not None:
                    overlap_note = f"Sentiment thème sur 7j (avec météo récente) : {tw_score:+.2f}"

    return {
        "weather_count": len(weather),
        "cities": cities[:5],
        "weather_dominant": w_dom,
        "weather_dominant_pct": w_pct,
        "weather_mean_score": w_score,
        "theme_mean_score": t_score,
        "overlap_note": overlap_note,
        "latest_titles": weather["title"].astype(str).head(3).tolist() if "title" in weather.columns else [],
    }


def _source_breakdown(df: pd.DataFrame, top_n: int = 4) -> list[tuple[str, int, float]]:
    if "source" not in df.columns or len(df) == 0:
        return []
    total = len(df)
    vc = df["source"].dropna().value_counts().head(top_n)
    return [(str(k), int(v), float(v) / total) for k, v in vc.items()]


def _compose_reply(cards: list[dict], message: str) -> str:
    if not cards:
        return "Aucun insight disponible pour ce thème."
    lines = [cards[0]["summary"]]
    for c in cards[1:4]:
        lines.append(f"- {c['title']} : {c['summary']}")
    return "\n".join(lines)


def build_insight_pack(theme: str, message: str, *, include_mistral: bool = True) -> InsightPack:
    """Génère plusieurs cartes insight + reply synthétique."""
    theme = theme.lower()
    theme_labels = {"politique": "Politique", "financier": "Financier", "utilisateurs": "Sources"}
    label = theme_labels.get(theme, theme.capitalize())

    df_full, data_label = load_enriched_goldai()
    df_theme = filter_theme_df(df_full, theme)
    if len(df_theme) == 0:
        df_theme = df_full.copy()

    total = len(df_theme)
    dist = sentiment_distribution(df_theme)
    dom, dom_pct = _dominant(dist)
    m_score = mean_score(df_theme)
    cards: list[dict] = []

    # 1 — Vue sentiment
    dist_txt = " · ".join(f"{k} {v['pct']:.0%}" for k, v in sorted(dist.items(), key=lambda x: -x[1]["count"])[:3])
    score_txt = f" Score moyen {m_score:+.2f}." if m_score is not None else ""
    cards.append(
        _card(
            "sentiment_overview",
            "sentiment",
            f"Sentiment {label}",
            f"{total:,} articles — dominant {dom} ({dom_pct:.0%}). Répartition : {dist_txt}.{score_txt}",
            {"total": total, "dominant": dom, "dominant_pct": dom_pct, "mean_score": m_score, "distribution": dist},
        )
    )

    # 2 — Mix sources
    sources = _source_breakdown(df_theme)
    if sources:
        src_txt = " · ".join(f"{s} {pct:.0%}" for s, _, pct in sources)
        cards.append(
            _card(
                "source_mix",
                "sources",
                "Mix des sources",
                f"Principales sources {label} : {src_txt}.",
                {"sources": [{"name": s, "count": n, "pct": pct} for s, n, pct in sources]},
            )
        )

    # 3 — Tendance temporelle
    trend = _temporal_trend(df_theme)
    if trend:
        cards.append(
            _card(
                "temporal_trend",
                "trend",
                "Tendance temporelle",
                f"Sentiment en {trend['trend']} : récent {trend['score_recent']:+.2f} vs période antérieure {trend['score_old']:+.2f}.",
                trend,
            )
        )

    # 4 — Croisement météo
    wx = _weather_cross(df_full, df_theme)
    if wx:
        cities = ", ".join(wx["cities"]) if wx["cities"] else "France"
        extra = f" {wx['overlap_note']}." if wx.get("overlap_note") else ""
        latest = wx.get("latest_titles") or []
        sample = f" Ex. : {latest[0][:70]}…" if latest else ""
        w_sc = wx["weather_mean_score"]
        t_sc = wx["theme_mean_score"]
        scores_txt = ""
        if w_sc is not None and t_sc is not None:
            scores_txt = f" Score météo {w_sc:+.2f} vs thème {t_sc:+.2f}."
        elif w_sc is not None:
            scores_txt = f" Score météo {w_sc:+.2f}."
        cards.append(
            _card(
                "weather_cross",
                "weather",
                "Croisement météo",
                f"{wx['weather_count']} bulletins OpenWeather/Météo dans GoldAI ({cities}). "
                f"Sentiment météo : {wx['weather_dominant']} ({wx['weather_dominant_pct']:.0%})."
                f"{scores_txt}{extra}{sample}",
                wx,
            )
        )

    # 5 — Économie / INSEE (financier ou toujours si data)
    eco_df = filter_sources(df_full, _ECONOMIC_SOURCES)
    if len(eco_df) >= 5 and theme in ("financier", "politique"):
        eco_dist = sentiment_distribution(eco_df)
        eco_dom, eco_pct = _dominant(eco_dist)
        eco_sources = _source_breakdown(eco_df, 3)
        src_e = " · ".join(f"{s} ({n:,})" for s, n, _ in eco_sources)
        cards.append(
            _card(
                "economic_cross",
                "economy",
                "Signal économique",
                f"{len(eco_df):,} articles Yahoo/INSEE/Data.gouv — sentiment dominant {eco_dom} ({eco_pct:.0%}). Sources : {src_e}.",
                {"total": len(eco_df), "dominant": eco_dom, "sources": src_e},
            )
        )

    # 6 — Participatif vs médias
    part = filter_sources(df_theme, _PARTICIPATORY_SOURCES)
    media = filter_sources(df_theme, _MEDIA_SOURCES)
    if len(part) > 0 or len(media) > 0:
        p_score = mean_score(part)
        m_score_media = mean_score(media)
        p_pct = len(part) / total if total else 0
        m_pct = len(media) / total if total else 0
        p_txt = f"participatif {p_pct:.0%} (score {p_score:+.2f})" if p_score is not None else f"participatif {p_pct:.0%}"
        m_txt = (
            f"médias {m_pct:.0%} (score {m_score_media:+.2f})"
            if m_score_media is not None
            else f"médias {m_pct:.0%}"
        )
        cards.append(
            _card(
                "participatory_vs_media",
                "sources_bias",
                "Participatif vs médias",
                f"Croisement voix : {p_txt} · {m_txt}.",
                {
                    "participatory_pct": p_pct,
                    "media_pct": m_pct,
                    "participatory_score": p_score,
                    "media_score": m_score_media,
                },
            )
        )

    # 7b — Signaux crise (inondation, épidémie, etc.)
    crises = get_crisis_signals_cached(df_full)
    if crises:
        parts = []
        for c in crises[:4]:
            ex = c["sample_titles"][0][:60] + "…" if c.get("sample_titles") else ""
            parts.append(f"{c['theme']} ({c['count']} art.)")
        cards.append(
            _card(
                "crisis_signals",
                "crisis",
                "Signaux crise & santé",
                f"Détectés dans GoldAI : {' · '.join(parts)}.",
                {"signals": crises[:5]},
            )
        )

    # 8 — Score risque
    neg = _neg_pct(dist)
    risk = _risk_score(neg)
    cards.append(
        _card(
            "risk_score",
            "risk",
            "Score de risque",
            f"Risque {risk}/10 — part négative {neg:.0%} sur le périmètre {label}.",
            {"risk_score": risk, "neg_pct": neg},
        )
    )

    # Filtrer cartes selon question (prioriser)
    q = message.lower()
    if any(w in q for w in ("source", "contenu", "utilisateur")):
        cards.sort(key=lambda c: 0 if c["type"] in ("sources", "sources_bias") else 1)
    elif any(w in q for w in ("meteo", "météo", "weather", "croiser")):
        cards.sort(key=lambda c: 0 if c["type"] == "weather" else 1)
    elif any(w in q for w in ("risque", "alerte")):
        cards.sort(key=lambda c: 0 if c["type"] == "risk" else 1)
    elif theme in ("politique", "financier"):
        cards.sort(key=lambda c: (0 if c["type"] in ("cross_analysis", "crisis", "weather") else 1, c.get("id", "")))

    # Analyse croisée Mistral (météo × politique × économie × crises)
    if include_mistral:
        context = build_cross_context_block(df_full, df_theme, theme, label, cards)
        analysis = mistral_cross_analysis(context, message, label)
        if analysis:
            cards.insert(
                0,
                _card(
                    "cross_analysis",
                    "cross_analysis",
                    "Analyse croisée Mistral",
                    analysis,
                    {"provider": "mistral", "grounded": True},
                ),
            )
            reply = analysis
        else:
            reply = _compose_reply(cards, message)
    else:
        reply = _compose_reply(cards, message)

    return InsightPack(reply=reply, insights=cards[:8], data_label=data_label)
