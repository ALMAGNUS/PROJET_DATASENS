"""Interprétations métier pour cartes insight (météo, sport, crises, économie)."""

from __future__ import annotations

import re

import pandas as pd

from src.insights.goldai_data import mean_score, sentiment_distribution

_SPORT_PATTERNS: dict[str, list[str]] = {
    "Grands événements": [
        "coupe du monde",
        "euro 20",
        "champion du monde",
        "finale",
        "équipe de france",
        "equipe de france",
    ],
    "Football Paris / PSG": [
        "psg",
        "paris saint-germain",
        "champions league",
        "ligue des champions",
        "coupe d'europe",
        "ldc",
    ],
    "Sport & compétitions": [
        "football",
        "rugby",
        "tennis",
        "olympique",
        "stade",
        "victoire",
        "basket",
    ],
}


def scan_sport_signals(df: pd.DataFrame, limit_titles: int = 2) -> list[dict]:
    """Articles sport / grands événements (topic ou titres)."""
    if len(df) == 0:
        return []
    mask = pd.Series(False, index=df.index)
    if "topic_1" in df.columns:
        mask |= df["topic_1"].astype(str).str.lower().eq("sport")
    if "title" in df.columns:
        text = df["title"].astype(str).str.lower()
        for patterns in _SPORT_PATTERNS.values():
            for pat in patterns:
                mask |= text.str.contains(pat, na=False, regex=False)
    sport_df = df[mask]
    if len(sport_df) == 0:
        return []

    out: list[dict] = []
    if "title" in sport_df.columns:
        text = sport_df["title"].astype(str).str.lower()
        for label, patterns in _SPORT_PATTERNS.items():
            sub_mask = pd.Series(False, index=sport_df.index)
            for pat in patterns:
                sub_mask |= text.str.contains(pat, na=False, regex=False)
            sub = sport_df[sub_mask]
            if len(sub) == 0:
                continue
            titles = sub["title"].astype(str).head(limit_titles).tolist()
            dist = sentiment_distribution(sub)
            dom = max(dist.items(), key=lambda x: x[1]["count"])[0] if dist else "—"
            out.append(
                {
                    "theme": label,
                    "count": len(sub),
                    "dominant_sentiment": dom,
                    "mean_score": mean_score(sub),
                    "sample_titles": [t[:100] for t in titles if t.strip()],
                }
            )
    if not out:
        dist = sentiment_distribution(sport_df)
        dom = max(dist.items(), key=lambda x: x[1]["count"])[0] if dist else "—"
        titles = sport_df["title"].astype(str).head(limit_titles).tolist() if "title" in sport_df.columns else []
        out.append(
            {
                "theme": "Sport (topic)",
                "count": len(sport_df),
                "dominant_sentiment": dom,
                "mean_score": mean_score(sport_df),
                "sample_titles": [t[:100] for t in titles if t.strip()],
            }
        )
    return sorted(out, key=lambda x: -x["count"])


def parse_weather_conditions(titles: list[str]) -> dict:
    """Régime des bulletins : clément vs alerte."""
    temps: list[float] = []
    alert_mentions = 0
    mild = 0
    alert_kw = ("canicule", "alerte", "orange", "rouge", "orages", "crue", "inond")
    for raw in titles:
        t = raw.lower()
        m = re.search(r"([\d.]+)\s*c", t)
        if m:
            temps.append(float(m.group(1)))
        if any(k in t for k in alert_kw):
            alert_mentions += 1
        if re.search(r"ciel d[eé]gag[eé]|ensoleill|nuageux l[eé]ger|partiellement", t):
            mild += 1
    avg_temp = sum(temps) / len(temps) if temps else None
    return {
        "avg_temp": avg_temp,
        "alert_mentions": alert_mentions,
        "mild_regime": mild >= max(1, len(titles) // 2) and alert_mentions == 0,
        "sample": titles[0][:85] if titles else "",
    }


def narrate_weather_cross(
    wx: dict,
    crises: list[dict],
    theme_label: str,
    theme_neg_pct: float,
) -> str:
    cities = ", ".join(wx.get("cities") or []) or "France"
    cond = wx.get("conditions") or {}
    canicule = next((c for c in crises if "Canicule" in c.get("theme", "")), None)
    intemperies = next((c for c in crises if "Intempéries" in c.get("theme", "")), None)

    if cond.get("mild_regime"):
        head = f"Bulletins plutôt cléments ({cities}"
        if cond.get("avg_temp") is not None:
            head += f", ~{cond['avg_temp']:.0f}°C"
        head += ") : pas de canicule active dans les flux météo."
    else:
        head = f"{wx['weather_count']} bulletins météo ({cities})."

    if canicule and canicule["count"] >= 15:
        body = (
            f"{canicule['count']} articles canicule/sécheresse dans GoldAI — la chaleur extrême "
            f"est un facteur classique de crispation sociale et de ralentissement économique."
        )
    elif intemperies and intemperies["count"] >= 20:
        body = (
            f"{intemperies['count']} articles intempéries : risque de contagion sur le ressenti "
            f"{theme_label.lower()} et sur l'activité locale."
        )
    else:
        body = (
            f"Peu de choc climatique majeur ; le ton des titres météo ({wx['weather_dominant_pct']:.0%} "
            f"{wx['weather_dominant'].lower()}) reflète surtout des bulletins techniques, "
            f"pas une vague de chaleur ou des crues dominantes."
        )

    tail = ""
    if theme_neg_pct >= 0.4:
        tail = (
            f" Le négatif {theme_label.lower()} ({theme_neg_pct:.0%}) paraît endogène au débat politique "
            f"plutôt qu'imputable à la météo du moment."
        )
    return head + " " + body + tail


def narrate_sport(sport_signals: list[dict], theme: str) -> str:
    if not sport_signals:
        return (
            "Peu de couverture sport majeure dans la fenêtre GoldAI. Les grands événements "
            "(Coupe du monde, victoire du PSG en Ligue des champions) restent des leviers "
            "d'euphorie locale, de fréquentation et de consommation à croiser quand ils émergent."
        )
    total = sum(s["count"] for s in sport_signals)
    chunks = [
        f"{s['theme']} ({s['count']:,} art., {s['dominant_sentiment']})"
        for s in sport_signals[:3]
    ]
    lead = sport_signals[0]
    sample = lead["sample_titles"][0][:65] if lead.get("sample_titles") else ""
    text = (
        f"{total:,} articles sport — {' · '.join(chunks)}. "
        f"Le sport amplifie l'économie de l'événementiel (bars, transport, retail) "
        f"lors des victoires nationales ou parisiennes."
    )
    if sample:
        text += f" Fil : «{sample}…»."
    if theme == "politique":
        text += " Les personnalités politiques capitalisent ou subissent ces moments collectifs."
    return text


def narrate_crisis(crises: list[dict], theme_label: str) -> str:
    if not crises:
        return (
            f"Aucun signal crise dominant (canicule, épidémie, intempéries) dans les titres GoldAI "
            f"pour le périmètre {theme_label}."
        )

    top = crises[0]
    if "santé" in top["theme"].lower() or "épidém" in top["theme"].lower():
        intro = (
            f"La santé publique ({top['count']:,} art.) sature une partie du bruit médias "
            f"et peut masquer le signal {theme_label.lower()} pur. "
        )
    elif "Canicule" in top.get("theme", ""):
        intro = (
            f"Canicule/sécheresse ({top['count']:,} art.) : chaleur extrême, tension sur l'eau "
            f"et l'énergie, climat social plus irritable. "
        )
    elif "Intempéries" in top.get("theme", ""):
        intro = (
            f"Intempéries ({top['count']:,} art.) : perturbent transports, assurances "
            f"et continuité économique locale. "
        )
    elif "Sécurité" in top.get("theme", ""):
        intro = f"Sécurité/insécurité ({top['count']:,} art.) : alimente l'agenda politique et la défiance. "
    else:
        intro = ""

    parts: list[str] = []
    for c in crises[:4]:
        hint = ""
        if c.get("sample_titles"):
            hint = f" — «{c['sample_titles'][0][:50]}…»"
        parts.append(f"{c['theme']} ({c['count']:,}){hint}")
    return intro + "Autres signaux : " + " · ".join(parts)


def narrate_economy(
    eco_total: int,
    eco_dom: str,
    eco_pct: float,
    theme: str,
    politics_neg: float | None = None,
) -> str:
    text = (
        f"{eco_total:,} flux Yahoo/INSEE — tonalité {eco_dom} ({eco_pct:.0%}). "
        "Les gros volumes boursiers lissent le signal : peu de panique macro visible. "
    )
    if theme == "politique" and politics_neg is not None and politics_neg >= 0.4:
        text += (
            f"Découplage probable avec le politique ({politics_neg:.0%} négatif) : "
            "la méfiance citoyenne ne suit pas une crise économique ouverte dans GoldAI."
        )
    elif theme == "financier":
        text += "Isoler inflation, taux et emploi pour repérer les secteurs sous pression réelle."
    else:
        text += "À recouper avec le sport (événements) et la météo (canicule) pour le ressenti terrain."
    return text


def narrate_risk(risk: int, neg_pct: float, theme_label: str, crises: list[dict]) -> str:
    qual = "élevé" if risk >= 7 else ("modéré" if risk >= 5 else "contenu")
    extra = ""
    sec = next((c for c in crises if "Sécurité" in c.get("theme", "")), None)
    if sec and sec["count"] > 40:
        extra = f" Renforcé par {sec['count']:,} articles sécurité/insécurité."
    return f"Niveau {qual} ({risk}/10) — {neg_pct:.0%} de négatif sur {theme_label}.{extra}"
