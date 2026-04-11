"""
Diagnostic qualité des prédictions en production.
À lancer après chaque run d'inférence.

Usage:
    python scripts/check_inference_quality.py
    python scripts/check_inference_quality.py --verbose
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = ROOT / "data" / "goldai" / "predictions"

# Seuils de décision
THRESHOLDS = {
    "confidence_mean_min":    0.60,   # confiance moyenne acceptable
    "confidence_low_max_pct": 0.20,   # max 20% d'articles sous 0.55
    "dominant_class_max_pct": 0.85,   # alerte si une classe > 85%
    "neutral_min_pct":        0.03,   # alerte si neutre < 3%
    "latency_p90_ms":         260,    # p90 latence cible
    "latency_p99_ms":         500,    # p99 latence cible
}


def find_latest() -> Path:
    files = list(PRED_DIR.rglob("predictions.parquet"))
    if not files:
        raise FileNotFoundError(f"Aucun predictions.parquet dans {PRED_DIR}")
    # Priorité au plus volumineux (run complet) parmi les runs du jour le plus récent
    # Évite de pointer sur un mini-run de test (10 articles) qui serait plus récent
    files_by_date: dict[str, list[Path]] = {}
    for f in files:
        date_dir = f.parent.parent.name  # date=YYYY-MM-DD
        files_by_date.setdefault(date_dir, []).append(f)
    latest_date = sorted(files_by_date.keys())[-1]
    candidates = files_by_date[latest_date]
    # Parmi les runs du jour le plus récent, prend le plus gros
    best = max(candidates, key=lambda f: f.stat().st_size)
    return best


def check_distribution(df: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Vérifie la distribution des sentiments prédits."""
    results = []
    total = len(df)
    dist = df["predicted_sentiment"].value_counts(normalize=True)

    for label, pct in dist.items():
        results.append(("Distribution", f"{label}", f"{pct:.1%}"))

    dominant_pct = dist.iloc[0] if len(dist) > 0 else 0
    dominant_label = dist.index[0] if len(dist) > 0 else "?"
    if dominant_pct > THRESHOLDS["dominant_class_max_pct"]:
        results.append(("⚠ ALERTE", f"Dominance {dominant_label} à {dominant_pct:.1%}",
                         "Biais corpus ou biais modèle → vérifier"))
    else:
        results.append(("✅ OK", "Distribution équilibrée", f"Dominance max = {dominant_pct:.1%}"))

    neutral_pct = dist.get("neutre", dist.get("neutral", 0))
    if neutral_pct < THRESHOLDS["neutral_min_pct"]:
        results.append(("⚠ ALERTE", f"Classe neutre sous-représentée ({neutral_pct:.1%})",
                         "Modèle mal calibré sur les articles neutres"))
    return results


def check_confidence(df: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Vérifie les scores de confiance."""
    results = []
    conf = df["confidence"].dropna()
    mean_conf = conf.mean()
    pct_low = (conf < 0.55).mean()
    pct_high = (conf > 0.75).mean()

    results.append(("Confiance", "Moyenne", f"{mean_conf:.3f}"))
    results.append(("Confiance", "% < 0.55 (hésitant)", f"{pct_low:.1%}"))
    results.append(("Confiance", "% > 0.75 (sûr)", f"{pct_high:.1%}"))

    if mean_conf < THRESHOLDS["confidence_mean_min"]:
        results.append(("⚠ ALERTE", f"Confiance moyenne trop basse ({mean_conf:.3f})",
                         f"Seuil cible >= {THRESHOLDS['confidence_mean_min']}"))
    else:
        results.append(("✅ OK", f"Confiance moyenne acceptable ({mean_conf:.3f})", ""))

    if pct_low > THRESHOLDS["confidence_low_max_pct"]:
        results.append(("⚠ ALERTE", f"{pct_low:.1%} d'articles sous 0.55",
                         "Trop d'articles ambigus → enrichir le dataset d'entraînement"))
    else:
        results.append(("✅ OK", f"Taux d'articles ambigus acceptable ({pct_low:.1%})", ""))

    return results


def check_latency(df: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Vérifie les performances de latence."""
    results = []
    if "inference_ms" not in df.columns:
        results.append(("⚠ INFO", "Colonne inference_ms absente", "Latence non mesurée"))
        return results

    lat = df["inference_ms"].dropna()
    p50 = lat.quantile(0.50)
    p90 = lat.quantile(0.90)
    p99 = lat.quantile(0.99)

    results.append(("Latence", "p50 (médiane)", f"{p50:.0f} ms"))
    results.append(("Latence", "p90", f"{p90:.0f} ms"))
    results.append(("Latence", "p99", f"{p99:.0f} ms"))
    results.append(("Latence", "% sous 300ms (SLA API)", f"{(lat <= 300).mean():.1%}"))

    if p90 > THRESHOLDS["latency_p90_ms"]:
        results.append(("⚠ ALERTE", f"p90 latence = {p90:.0f}ms > seuil {THRESHOLDS['latency_p90_ms']}ms",
                         "Modèle trop lent pour production API"))
    else:
        results.append(("✅ OK", f"Latence p90 dans les clous ({p90:.0f}ms)", ""))

    return results


def check_topic_coherence(df: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Croise sentiment prédit par topic — cohérence métier."""
    results = []
    if "topic_1" not in df.columns:
        results.append(("⚠ INFO", "Colonne topic_1 absente", "Jointure gold_app_input manquante"))
        return results

    top_topics = df["topic_1"].value_counts().head(5).index.tolist()
    for topic in top_topics:
        sub = df[df["topic_1"] == topic]
        dist = sub["predicted_sentiment"].value_counts(normalize=True)
        dominant = dist.index[0] if len(dist) > 0 else "?"
        dominant_pct = dist.iloc[0] if len(dist) > 0 else 0
        results.append(("Topic", f"{topic} (n={len(sub):,})",
                         f"→ {dominant} à {dominant_pct:.0%}"))
    return results


def verdict(checks: list[tuple[str, str, str]]) -> str:
    alerts = [c for c in checks if c[0].startswith("⚠ ALERTE")]
    if not alerts:
        return "✅ GO — Prédictions exploitables pour Mistral et le cockpit."
    if len(alerts) <= 2:
        return f"⚠ GO AVEC VIGILANCE — {len(alerts)} point(s) à surveiller."
    return f"❌ NO-GO — {len(alerts)} alertes. Ré-entraîner avant usage production."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Affiche toutes les lignes")
    args = parser.parse_args()

    latest = find_latest()
    print(f"\nDiagnostic inférence : {latest.parent.name} / {latest.parent.parent.name}")
    print("─" * 60)

    df = pd.read_parquet(latest)
    print(f"Articles analysés : {len(df):,}")
    print(f"Modèle            : {df['model_version'].iloc[0] if 'model_version' in df.columns else '?'}")
    print("─" * 60)

    all_checks: list[tuple[str, str, str]] = []
    all_checks += check_distribution(df)
    all_checks += check_confidence(df)
    all_checks += check_latency(df)
    all_checks += check_topic_coherence(df)

    # Affichage
    for category, label, value in all_checks:
        if args.verbose or category.startswith(("✅", "⚠")):
            print(f"  {category:<20} {label:<45} {value}")

    if not args.verbose:
        print("\n  (--verbose pour tout afficher)")

    print("\n" + "=" * 60)
    print(f"VERDICT : {verdict(all_checks)}")
    print("=" * 60)

    # Recommandation
    alerts = [c for c in all_checks if c[0].startswith("⚠ ALERTE")]
    if alerts:
        print("\nActions recommandées :")
        for _, label, value in alerts:
            print(f"  • {label} — {value}")
    print()


if __name__ == "__main__":
    main()
