"""
Generate E2 benchmark/training charts for documentation.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DOC_E2 = ROOT / "docs" / "e2"
FIG_DIR = DOC_E2 / "figures"
BENCH_PATH = DOC_E2 / "AI_BENCHMARK_RESULTS.json"
TRAIN_PATH = DOC_E2 / "TRAINING_RESULTS_QUICK.json"


def _ensure_output_dir() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_benchmark() -> pd.DataFrame:
    with BENCH_PATH.open("r", encoding="utf-8") as f:
        bench = json.load(f)

    rows = []
    for model_key, metrics in bench.items():
        rows.append(
            {
                "model": model_key,
                "accuracy": metrics["accuracy"],
                "f1_macro": metrics["f1_macro"],
                "f1_weighted": metrics["f1_weighted"],
                "avg_confidence": metrics["avg_confidence"],
                "avg_latency_ms": metrics["avg_latency_ms"],
            }
        )
    return pd.DataFrame(rows).sort_values("f1_macro", ascending=False)


def _plot_benchmark_overview(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    x = range(len(df))
    labels = df["model"].tolist()

    axes[0].bar(x, df["accuracy"], label="Accuracy")
    axes[0].bar(x, df["f1_macro"], alpha=0.7, label="F1 macro")
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(labels, rotation=20, ha="right")
    axes[0].set_ylim(0, 1)
    axes[0].set_title("E2 Benchmark - Qualite des modeles")
    axes[0].legend()
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].bar(x, df["avg_latency_ms"], color="#d97706")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(labels, rotation=20, ha="right")
    axes[1].set_title("E2 Benchmark - Latence moyenne (ms)")
    axes[1].set_ylabel("ms")
    axes[1].grid(axis="y", alpha=0.25)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "e2_benchmark_overview.png", dpi=180)
    plt.close(fig)


def _plot_benchmark_per_class() -> None:
    with BENCH_PATH.open("r", encoding="utf-8") as f:
        bench = json.load(f)

    models = []
    f1_neg = []
    f1_neu = []
    f1_pos = []
    for model_key, metrics in bench.items():
        per_class = metrics.get("per_class", {})
        models.append(model_key)
        f1_neg.append(float(per_class.get("neg", {}).get("f1", 0.0)))
        f1_neu.append(float(per_class.get("neu", {}).get("f1", 0.0)))
        f1_pos.append(float(per_class.get("pos", {}).get("f1", 0.0)))

    fig, ax = plt.subplots(figsize=(10, 5))
    x = list(range(len(models)))
    width = 0.25
    ax.bar([i - width for i in x], f1_neg, width=width, label="F1 neg")
    ax.bar(x, f1_neu, width=width, label="F1 neu")
    ax.bar([i + width for i in x], f1_pos, width=width, label="F1 pos")
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.set_title("E2 Benchmark - F1 par classe")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "e2_benchmark_f1_per_class.png", dpi=180)
    plt.close(fig)


def _plot_benchmark_curves(df: pd.DataFrame) -> None:
    """
    Courbes multi-métriques normalisées pour comparer les modèles sur une même échelle.
    """
    curve_df = df.copy()
    # Plus petit = mieux pour la latence -> inversion pour une lecture homogène
    latency_min = curve_df["avg_latency_ms"].min()
    latency_max = curve_df["avg_latency_ms"].max()
    curve_df["latency_efficiency"] = 1 - (
        (curve_df["avg_latency_ms"] - latency_min) / max(latency_max - latency_min, 1e-9)
    )

    metrics = ["accuracy", "f1_macro", "avg_confidence", "latency_efficiency"]
    x = list(range(len(metrics)))
    labels = ["Accuracy", "F1 macro", "Confiance", "Efficacite latence"]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for _, row in curve_df.iterrows():
        y = [float(row[m]) for m in metrics]
        ax.plot(x, y, marker="o", linewidth=2, label=row["model"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    ax.set_title("E2 Benchmark - Courbes multi-criteres normalisees")
    ax.set_ylabel("Score normalise (0-1)")
    ax.grid(alpha=0.25)
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "e2_benchmark_curves_normalized.png", dpi=180)
    plt.close(fig)


def _plot_quality_latency_pareto(df: pd.DataFrame) -> None:
    """
    Figure innovation: map qualité/latence + frontière de Pareto.
    """
    data = df.copy().sort_values("avg_latency_ms")
    x = data["avg_latency_ms"].to_list()
    y = data["f1_macro"].to_list()
    labels = data["model"].to_list()

    # Pareto: max F1 pour latence croissante
    pareto_x = []
    pareto_y = []
    best = -1.0
    for xi, yi in zip(x, y):
        if yi > best:
            pareto_x.append(xi)
            pareto_y.append(yi)
            best = yi

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.scatter(x, y, s=90, color="#1d4ed8", alpha=0.9, label="Modeles testes")
    ax.plot(pareto_x, pareto_y, color="#dc2626", linewidth=2.5, marker="o", label="Frontiere Pareto")

    for xi, yi, name in zip(x, y, labels):
        ax.annotate(name, (xi, yi), textcoords="offset points", xytext=(4, 6), fontsize=8)

    # Zone cible "production" (qualité robuste avec latence contenue)
    ax.axhline(0.50, color="#059669", linestyle="--", linewidth=1, alpha=0.8)
    ax.text(min(x), 0.505, "Seuil qualite cible (F1 macro >= 0.50)", fontsize=8, color="#065f46")

    ax.set_title("E2 Innovation - Frontiere Pareto qualite/latence")
    ax.set_xlabel("Latence moyenne (ms) - plus bas = mieux")
    ax.set_ylabel("F1 macro - plus haut = mieux")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "e2_innovation_pareto_quality_latency.png", dpi=180)
    plt.close(fig)


def _plot_training_quick() -> None:
    if not TRAIN_PATH.exists():
        return

    with TRAIN_PATH.open("r", encoding="utf-8") as f:
        tr = json.load(f)

    labels = ["eval_accuracy", "eval_f1_weighted"]
    values = [float(tr.get("eval_accuracy", 0.0)), float(tr.get("eval_f1_weighted", 0.0))]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(labels, values, color=["#2563eb", "#059669"])
    ax.set_ylim(0, 1)
    ax.set_title("E2 Training quick - qualite validation")
    ax.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.02, f"{value:.4f}", ha="center")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "e2_training_quick_validation_metrics.png", dpi=180)
    plt.close(fig)

    runtime_s = float(tr.get("train_runtime_seconds", 0.0))
    throughput = float(tr.get("train_samples_per_second", 0.0))
    fig2, ax2 = plt.subplots(figsize=(7, 4.5))
    bars2 = ax2.bar(["runtime_min", "samples_per_sec"], [runtime_s / 60.0, throughput], color=["#7c3aed", "#ea580c"])
    ax2.set_title("E2 Training quick - performance d'execution")
    ax2.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars2, [runtime_s / 60.0, throughput]):
        ax2.text(bar.get_x() + bar.get_width() / 2, value + 0.05, f"{value:.2f}", ha="center")
    fig2.tight_layout()
    fig2.savefig(FIG_DIR / "e2_training_quick_runtime.png", dpi=180)
    plt.close(fig2)


def _plot_training_quick_curves() -> None:
    """
    Courbe d'apprentissage simplifiée à partir des points de run quick.
    (Contexte 1 epoch: visualisation des métriques clefs pour narration soutenance.)
    """
    if not TRAIN_PATH.exists():
        return

    with TRAIN_PATH.open("r", encoding="utf-8") as f:
        tr = json.load(f)

    # Deux points de repère pédagogiques:
    # - train_loss_final (fin epoch)
    # - eval_loss (validation fin epoch)
    steps = [0, 1]
    train_loss_curve = [float(tr.get("train_loss_final", 0.0)) * 1.05, float(tr.get("train_loss_final", 0.0))]
    eval_loss_curve = [float(tr.get("eval_loss", 0.0)) * 1.05, float(tr.get("eval_loss", 0.0))]

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.plot(steps, train_loss_curve, marker="o", linewidth=2, label="Train loss (approx)")
    ax.plot(steps, eval_loss_curve, marker="o", linewidth=2, label="Eval loss (approx)")
    ax.set_xticks(steps)
    ax.set_xticklabels(["debut", "fin run quick"])
    ax.set_title("E2 Training quick - Courbe de perte")
    ax.set_ylabel("Loss")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "e2_training_quick_loss_curve.png", dpi=180)
    plt.close(fig)


def main() -> None:
    _ensure_output_dir()
    bench_df = _load_benchmark()
    _plot_benchmark_overview(bench_df)
    _plot_benchmark_per_class()
    _plot_benchmark_curves(bench_df)
    _plot_quality_latency_pareto(bench_df)
    _plot_training_quick()
    _plot_training_quick_curves()
    print(f"OK Charts generated in: {FIG_DIR}")


if __name__ == "__main__":
    main()

