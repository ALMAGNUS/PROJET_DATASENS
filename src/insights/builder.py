"""Construction d'insights métier multi-cartes (croisements GoldAI)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

from src.insights.cross_context import build_cross_context_block
from src.insights.macro_narrative import (
    narrate_crisis,
    narrate_economy,
    narrate_risk,
    narrate_sport,
    narrate_weather_cross,
    parse_weather_conditions,
    scan_sport_signals,
)
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

    latest_titles = weather["title"].astype(str).head(5).tolist() if "title" in weather.columns else []

    return {
        "weather_count": len(weather),
        "cities": cities[:5],
        "weather_dominant": w_dom,
        "weather_dominant_pct": w_pct,
        "weather_mean_score": w_score,
        "theme_mean_score": t_score,
        "overlap_note": overlap_note,
        "latest_titles": latest_titles[:3],
        "conditions": parse_weather_conditions(latest_titles),
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


def _curate_cards(cards: list[dict], theme: str, question: str, *, max_cards: int = 6) -> list[dict]:
    """Priorise les cartes à forte valeur métier (6 bulles + 1 synthèse Mistral)."""
    q = question.lower()
    if any(w in q for w in ("source", "contenu", "utilisateur")):
        order = ("sources", "sources_bias", "sentiment", "crisis", "weather", "sport", "economy", "risk", "trend")
    elif any(w in q for w in ("meteo", "météo", "weather", "canicule", "climat")):
        order = ("weather", "crisis", "sentiment", "sport", "economy", "risk", "sources", "sources_bias", "trend")
    elif any(w in q for w in ("sport", "psg", "coupe", "football")):
        order = ("sport", "economy", "sentiment", "weather", "crisis", "risk", "sources", "sources_bias", "trend")
    elif any(w in q for w in ("risque", "alerte")):
        order = ("risk", "crisis", "sentiment", "weather", "economy", "sport", "sources", "sources_bias", "trend")
    elif theme == "financier":
        order = ("economy", "weather", "sport", "crisis", "sentiment", "risk", "trend", "sources", "sources_bias")
    else:
        order = ("crisis", "weather", "sport", "economy", "sentiment", "risk", "trend", "sources", "sources_bias")

    rank = {t: i for i, t in enumerate(order)}
    sorted_cards = sorted(cards, key=lambda c: (rank.get(c.get("type"), 99), c.get("id", "")))
    skip_optional = {"sources", "sources_bias", "trend"}
    if theme in ("politique", "financier") and not any(
        w in q for w in ("source", "contenu", "utilisateur", "tendance", "trend")
    ):
        sorted_cards = [c for c in sorted_cards if c.get("type") not in skip_optional]
    return sorted_cards[:max_cards]


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
    neg = _neg_pct(dist)
    risk = _risk_score(neg)
    crises = get_crisis_signals_cached(df_full)
    sport_signals = scan_sport_signals(df_full)
    cards: list[dict] = []

    dist_txt = " · ".join(f"{k} {v['pct']:.0%}" for k, v in sorted(dist.items(), key=lambda x: -x[1]["count"])[:3])
    score_txt = f" Score {m_score:+.2f}." if m_score is not None else ""
    sentiment_summary = f"{total:,} articles — {dom} dominant ({dom_pct:.0%}). {dist_txt}.{score_txt}"
    if neg >= 0.4:
        sentiment_summary += " Climat défiant, au-dessus du simple bruit médiatique."
    cards.append(
        _card(
            "sentiment_overview",
            "sentiment",
            f"Sentiment {label}",
            sentiment_summary,
            {"total": total, "dominant": dom, "dominant_pct": dom_pct, "mean_score": m_score, "distribution": dist},
        )
    )

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

    trend = _temporal_trend(df_theme)
    if trend:
        cards.append(
            _card(
                "temporal_trend",
                "trend",
                "Tendance temporelle",
                f"Sentiment en {trend['trend']} : récent {trend['score_recent']:+.2f} vs antérieur {trend['score_old']:+.2f}.",
                trend,
            )
        )

    wx = _weather_cross(df_full, df_theme)
    if wx:
        cards.append(
            _card(
                "weather_cross",
                "weather",
                "Météo & climat social",
                narrate_weather_cross(wx, crises, label, neg),
                wx,
            )
        )

    eco_df = filter_sources(df_full, _ECONOMIC_SOURCES)
    if len(eco_df) >= 5 and theme in ("financier", "politique"):
        eco_dist = sentiment_distribution(eco_df)
        eco_dom, eco_pct = _dominant(eco_dist)
        cards.append(
            _card(
                "economic_cross",
                "economy",
                "Signal économique",
                narrate_economy(len(eco_df), eco_dom, eco_pct, theme, neg if theme == "politique" else None),
                {"total": len(eco_df), "dominant": eco_dom, "dominant_pct": eco_pct},
            )
        )

    cards.append(
        _card(
            "sport_macro",
            "sport",
            "Sport & effet événement",
            narrate_sport(sport_signals, theme),
            {"signals": sport_signals[:5]},
        )
    )

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

    if crises:
        cards.append(
            _card(
                "crisis_signals",
                "crisis",
                "Signaux crise & santé",
                narrate_crisis(crises, label),
                {"signals": crises[:5]},
            )
        )

    cards.append(
        _card(
            "risk_score",
            "risk",
            "Score de risque",
            narrate_risk(risk, neg, label, crises),
            {"risk_score": risk, "neg_pct": neg},
        )
    )

    cards = _curate_cards(cards, theme, message, max_cards=6)

    if include_mistral:
        context = build_cross_context_block(
            df_full, df_theme, theme, label, cards, crises=crises, sport_signals=sport_signals
        )
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

    return InsightPack(reply=reply, insights=cards[:7], data_label=data_label)
