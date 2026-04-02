"""
Génère les figures E2 d'inférence — résultats du modèle ALMAGNUS sur les données réelles.
Usage: python scripts/plot_inference_results.py

Figures produites dans docs/e2/figures/ :
  - e2_inference_sentiment_distribution.png  Distribution des sentiments prédits
  - e2_inference_confidence_by_class.png     Confiance par classe (boîtes à moustaches)
  - e2_inference_probability_profiles.png    Profils de probabilité p_pos / p_neu / p_neg
  - e2_inference_latency.png                 Distribution de la latence + percentiles
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = ROOT / "data" / "goldai" / "predictions"
FIG_DIR = ROOT / "docs" / "e2" / "figures"

CLASS_COLORS = {
    "positif":  "#22c55e",
    "négatif":  "#ef4444",
    "neutre":   "#64748b",
    "POSITIVE": "#22c55e",
    "NEGATIVE": "#ef4444",
    "NEUTRAL":  "#64748b",
}
STYLE = {"dpi": 180, "facecolor": "white"}

_LABEL_MAP = {"POSITIVE": "positif", "NEGATIVE": "négatif", "NEUTRAL": "neutre"}


def _load_predictions() -> pd.DataFrame:
    files = list(PRED_DIR.rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"Aucun fichier predictions.parquet dans {PRED_DIR}")
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    # Normalise vers labels FR minuscules
    if "predicted_sentiment" in df.columns:
        df["sentiment_label"] = df["predicted_sentiment"].map(lambda x: _LABEL_MAP.get(str(x), str(x)))
    elif "label_3c" in df.columns:
        df["sentiment_label"] = df["label_3c"].map(lambda x: _LABEL_MAP.get(str(x), str(x)))
    else:
        raise ValueError("Colonnes predicted_sentiment / label_3c absentes")
    return df


# ─────────────────────────────────────────────────────────────────────────────
def _plot_sentiment_distribution(df: pd.DataFrame) -> None:
    """Bar chart + donut : distribution des sentiments prédits."""
    order = ["positif", "négatif", "neutre"]
    counts = df["sentiment_label"].value_counts()
    counts = counts.reindex(order, fill_value=0)
    total = counts.sum()
    pcts = (counts / total * 100).round(1)
    colors = [CLASS_COLORS[c] for c in order]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(
        f"E2 Inférence — Distribution des sentiments prédits\n"
        f"Modèle : ALMAGNUS/datasens-sentiment-fr · {total:,} articles",
        fontsize=12, fontweight="bold",
    )

    # Gauche : bar chart
    ax0 = axes[0]
    bars = ax0.bar(order, counts.values, color=colors, alpha=0.88, edgecolor="black", linewidth=0.5, width=0.5)
    for bar, cnt, pct in zip(bars, counts.values, pcts.values):
        ax0.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + total * 0.005,
            f"{cnt:,}\n({pct}%)", ha="center", fontsize=10, fontweight="bold",
        )
    ax0.set_ylabel("Nombre d'articles")
    ax0.set_title("Décompte par classe", fontsize=11)
    ax0.grid(axis="y", alpha=0.25)
    ax0.set_ylim(0, counts.max() * 1.18)

    # Droite : donut
    ax1 = axes[1]
    wedges, texts, autotexts = ax1.pie(
        counts.values, labels=order, colors=colors,
        autopct="%1.1f%%", startangle=90, pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for t in autotexts:
        t.set_fontsize(10)
        t.set_fontweight("bold")
    # Donut hole
    centre = plt.Circle((0, 0), 0.45, fc="white")
    ax1.add_patch(centre)
    ax1.text(0, 0, f"{total:,}\narticles", ha="center", va="center", fontsize=9, fontweight="bold", color="#374151")
    ax1.set_title("Répartition proportionnelle", fontsize=11)

    # Annotation si forte dominance
    dominant_class = counts.idxmax()
    dominant_pct = pcts[dominant_class]
    if dominant_pct > 60:
        ax0.annotate(
            f"Dominance {dominant_class} ({dominant_pct}%)\n→ vérifier biais corpus ou modèle",
            xy=(order.index(dominant_class), counts[dominant_class]),
            xytext=(0.65, 0.85), xycoords=("data", "axes fraction"),
            textcoords="axes fraction",
            fontsize=8, color="#7c3aed", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f3e8ff", edgecolor="#7c3aed", alpha=0.9),
        )

    fig.tight_layout()
    fig.savefig(FIG_DIR / "e2_inference_sentiment_distribution.png", **STYLE)
    plt.close(fig)
    print("  OK e2_inference_sentiment_distribution.png")


# ─────────────────────────────────────────────────────────────────────────────
def _plot_confidence_by_class(df: pd.DataFrame) -> None:
    """Boîte à moustaches + distribution de confiance par classe prédite."""
    order = ["positif", "négatif", "neutre"]
    order = [c for c in order if c in df["sentiment_label"].values]
    colors = [CLASS_COLORS[c] for c in order]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(
        "E2 Inférence — Score de confiance par classe prédite\n"
        "(confiance = max des probabilités : max(p_pos, p_neu, p_neg))",
        fontsize=12, fontweight="bold",
    )

    # Gauche : boxplot
    ax0 = axes[0]
    data_by_class = [df[df["sentiment_label"] == c]["confidence"].dropna().values for c in order]
    bp = ax0.boxplot(
        data_by_class, tick_labels=order, patch_artist=True,
        medianprops={"color": "black", "linewidth": 2},
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    for mean_val, x_pos, c in zip([d.mean() for d in data_by_class], range(1, len(order) + 1), order):
        ax0.scatter(x_pos, mean_val, color="black", zorder=5, s=60, marker="D")
        ax0.text(x_pos + 0.07, mean_val, f"moy={mean_val:.3f}", fontsize=8, va="center")
    ax0.set_ylabel("Score de confiance (0 → 1)")
    ax0.set_title("Distribution de confiance", fontsize=11)
    ax0.axhline(0.5, color="#dc2626", linestyle="--", linewidth=1, alpha=0.7)
    ax0.text(0.7, 0.515, "Seuil 0.5", fontsize=8, color="#7f1d1d", transform=ax0.get_yaxis_transform())
    ax0.grid(axis="y", alpha=0.25)

    # Droite : histogramme superposé
    ax1 = axes[1]
    bins = np.linspace(0, 1, 30)
    for c, color in zip(order, colors):
        subset = df[df["sentiment_label"] == c]["confidence"].dropna()
        ax1.hist(subset, bins=bins, alpha=0.55, color=color, label=f"{c} (n={len(subset):,})", edgecolor="none")
    ax1.set_xlabel("Score de confiance")
    ax1.set_ylabel("Fréquence")
    ax1.set_title("Histogramme par classe", fontsize=11)
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.2)
    ax1.axvline(df["confidence"].mean(), color="#7c3aed", linewidth=1.5, linestyle="--",
                label=f"Moy. globale = {df['confidence'].mean():.3f}")

    fig.tight_layout()
    fig.savefig(FIG_DIR / "e2_inference_confidence_by_class.png", **STYLE)
    plt.close(fig)
    print("  OK e2_inference_confidence_by_class.png")


# ─────────────────────────────────────────────────────────────────────────────
def _plot_probability_profiles(df: pd.DataFrame) -> None:
    """Scatter p_pos vs p_neg coloré par classe — montre les frontières de décision."""
    if not {"p_pos", "p_neg", "p_neu"}.issubset(df.columns):
        print("  ⚠ Colonnes p_pos/p_neg/p_neu absentes, figure ignorée.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(
        "E2 Inférence — Profils de probabilité par classe\n"
        "(frontières de décision du modèle ALMAGNUS/datasens-sentiment-fr)",
        fontsize=12, fontweight="bold",
    )

    # Échantillon pour le scatter (max 3000 points pour lisibilité)
    sample = df.sample(min(3000, len(df)), random_state=42)
    order = ["positif", "négatif", "neutre"]
    order = [c for c in order if c in sample["sentiment_label"].values]

    ax0 = axes[0]
    for c in order:
        sub = sample[sample["sentiment_label"] == c]
        ax0.scatter(sub["p_pos"], sub["p_neg"], s=8, alpha=0.35,
                    color=CLASS_COLORS[c], label=f"{c} (n={len(sub):,})")
    ax0.set_xlabel("p(positif)")
    ax0.set_ylabel("p(négatif)")
    ax0.set_title("Espace de décision p_pos vs p_neg", fontsize=11)
    ax0.legend(fontsize=9, markerscale=3)
    ax0.grid(alpha=0.2)
    # Diagonale équiprobable
    ax0.plot([0, 1], [1, 0], color="#94a3b8", linestyle=":", linewidth=1, alpha=0.7)
    ax0.text(0.5, 0.52, "p_pos = p_neg", fontsize=7, color="#94a3b8", rotation=-45)

    # Droite : distributions marginales des 3 probabilités
    ax1 = axes[1]
    bins = np.linspace(0, 1, 35)
    for col, label, color in [
        ("p_pos", "p(positif)", CLASS_COLORS["positif"]),
        ("p_neg", "p(négatif)", CLASS_COLORS["négatif"]),
        ("p_neu", "p(neutre)",  CLASS_COLORS["neutre"]),
    ]:
        ax1.hist(df[col].dropna(), bins=bins, alpha=0.45, color=color, label=label, edgecolor="none")
    ax1.set_xlabel("Probabilité")
    ax1.set_ylabel("Fréquence")
    ax1.set_title("Distribution marginale des 3 probabilités", fontsize=11)
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "e2_inference_probability_profiles.png", **STYLE)
    plt.close(fig)
    print("  OK e2_inference_probability_profiles.png")


# ─────────────────────────────────────────────────────────────────────────────
def _plot_latency(df: pd.DataFrame) -> None:
    """Distribution de la latence d'inférence + percentiles."""
    if "inference_ms" not in df.columns:
        print("  ⚠ Colonne inference_ms absente, figure ignorée.")
        return

    lat = df["inference_ms"].dropna()
    p50, p90, p99 = lat.quantile([0.5, 0.9, 0.99]).values

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(
        f"E2 Inférence — Latence d'inférence par article\n"
        f"Modèle : ALMAGNUS/datasens-sentiment-fr · {len(lat):,} prédictions",
        fontsize=12, fontweight="bold",
    )

    # Gauche : histogramme
    ax0 = axes[0]
    ax0.hist(lat, bins=50, color="#60a5fa", alpha=0.80, edgecolor="white", linewidth=0.4)
    ax0.axvline(p50, color="#16a34a",  linewidth=2, linestyle="-",  label=f"p50 = {p50:.0f} ms")
    ax0.axvline(p90, color="#ea580c",  linewidth=2, linestyle="--", label=f"p90 = {p90:.0f} ms")
    ax0.axvline(p99, color="#dc2626",  linewidth=2, linestyle=":",  label=f"p99 = {p99:.0f} ms")
    ax0.axvline(300, color="#7c3aed",  linewidth=1.5, linestyle="--", alpha=0.7, label="Seuil API 300 ms")
    ax0.set_xlabel("Latence (ms)")
    ax0.set_ylabel("Fréquence")
    ax0.set_title("Distribution de la latence", fontsize=11)
    ax0.legend(fontsize=9)
    ax0.grid(alpha=0.2)

    # Droite : tableau de synthèse
    ax1 = axes[1]
    ax1.axis("off")
    stats = [
        ["Métrique",          "Valeur"],
        ["Prédictions totales", f"{len(lat):,}"],
        ["Latence moyenne",   f"{lat.mean():.1f} ms"],
        ["Latence médiane",   f"{p50:.1f} ms"],
        ["p90",               f"{p90:.1f} ms"],
        ["p99",               f"{p99:.1f} ms"],
        ["Latence max",       f"{lat.max():.1f} ms"],
        ["Seuil API cible",   "300 ms"],
        ["% sous seuil",      f"{(lat <= 300).mean() * 100:.1f}%"],
        ["Modèle",            "ALMAGNUS/datasens-sentiment-fr"],
    ]
    tbl = ax1.table(cellText=stats[1:], colLabels=stats[0],
                    cellLoc="center", loc="center", bbox=[0.05, 0.0, 0.9, 1.0])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9.5)
    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_facecolor("#1e3a5f")
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f0f4f8")
        cell.set_edgecolor("#cbd5e1")
    ax1.set_title("Synthèse performance production", fontsize=11)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "e2_inference_latency.png", **STYLE)
    plt.close(fig)
    print("  OK e2_inference_latency.png")


# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    print("Génération des figures d'inférence E2...")
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = _load_predictions()
    print(f"  {len(df):,} prédictions chargées depuis {PRED_DIR}")

    total = len(df)
    dist = df["sentiment_label"].value_counts()
    for label, cnt in dist.items():
        print(f"    {label}: {cnt:,} ({cnt / total * 100:.1f}%)")
    print(f"  Confiance moyenne : {df['confidence'].mean():.3f}")

    _plot_sentiment_distribution(df)
    _plot_confidence_by_class(df)
    _plot_probability_profiles(df)
    _plot_latency(df)

    print(f"\nFigures générées dans : {FIG_DIR}")
    print("\nFigures produites :")
    for f in sorted(FIG_DIR.glob("e2_inference_*.png")):
        print(f"  • {f.name}")


if __name__ == "__main__":
    main()
