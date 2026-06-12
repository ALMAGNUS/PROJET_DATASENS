#!/usr/bin/env python3
"""
Évaluation complète des métriques de classification (3 classes : négatif/neutre/positif).

Métriques couvertes :
  - Accuracy
  - Precision & Recall (par classe + macro)
  - F1 score (par classe + macro)
  - Specificity & False Positive Rate (par classe + macro, one-vs-rest)
  - ROC-AUC (one-vs-rest, par classe + macro)
  - Courbes ROC TPR vs FPR (par classe)
  - Matrice de confusion (3x3, brute + normalisée)

Le problème est multiclasse : specificity, FPR, ROC-AUC et la courbe ROC sont
calculés en one-vs-rest (chaque classe contre le reste) puis moyennés (macro).

Usage:
    python scripts/eval_classification_metrics.py
    python scripts/eval_classification_metrics.py --models finetuned_local sentiment_fr --per-class 200

Sorties:
    docs/e2/EVAL_CLASSIFICATION_METRICS.json   (toutes les métriques, tous modèles)
    docs/e2/EVAL_CLASSIFICATION_METRICS.md     (tableaux lisibles)
    docs/e2/figures/e2_eval_confusion_{model}.png
    docs/e2/figures/e2_eval_roc_{model}.png
    docs/e2/figures/e2_eval_metrics_table_{model}.png
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ai_benchmark  # réutilise load_dataset / balanced_sample / get_available_models / _label_to_polarity

LABELS = ["neg", "neu", "pos"]
DISPLAY = {"neg": "négatif", "neu": "neutre", "pos": "positif"}
LABEL2IDX = {"neg": 0, "neu": 1, "pos": 2}
CLASS_COLORS = {"neg": "#ef4444", "neu": "#64748b", "pos": "#22c55e"}
STYLE = {"dpi": 180, "facecolor": "white"}

DOC_E2 = PROJECT_ROOT / "docs" / "e2"
FIG_DIR = DOC_E2 / "figures"


def _probs_3c(scores: list[dict]) -> list[float]:
    """Agrège les scores du modèle vers [p_neg, p_neu, p_pos] normalisés."""
    acc = {"neg": 0.0, "neu": 0.0, "pos": 0.0}
    for item in scores:
        pol = ai_benchmark._label_to_polarity(item.get("label", ""))
        acc[pol] += float(item.get("score", 0.0))
    total = sum(acc.values())
    if total > 0:
        for k in acc:
            acc[k] /= total
    return [acc["neg"], acc["neu"], acc["pos"]]


def _infer_probabilities(
    model_name: str, dataset: list[dict], max_length: int
) -> tuple[np.ndarray, np.ndarray]:
    """Retourne (y_true_idx [n], proba [n,3]) ordre [neg, neu, pos]."""
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "transformers/torch indisponibles. Activez le venv projet et installez requirements.txt."
        ) from e

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()
    id2label = getattr(model.config, "id2label", {}) or {}

    y_true: list[int] = []
    probs: list[list[float]] = []
    for i, sample in enumerate(dataset, 1):
        inputs = tokenizer(
            sample["text"], return_tensors="pt", truncation=True, max_length=max_length
        )
        with torch.no_grad():
            logits = model(**inputs).logits[0]
        soft = torch.softmax(logits, dim=-1).tolist()
        scores = [
            {"label": str(id2label.get(j, f"LABEL_{j}")), "score": float(p)}
            for j, p in enumerate(soft)
        ]
        probs.append(_probs_3c(scores))
        y_true.append(LABEL2IDX[sample["label"]])
        if i % 100 == 0:
            print(f"    {i}/{len(dataset)} inférences...")

    return np.array(y_true, dtype=int), np.array(probs, dtype=float)


def _compute_metrics(y_true: np.ndarray, proba: np.ndarray) -> dict:
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
        roc_curve,
    )
    from sklearn.preprocessing import label_binarize

    y_pred = proba.argmax(axis=1)
    idx = [0, 1, 2]

    cm = confusion_matrix(y_true, y_pred, labels=idx)
    total = int(cm.sum())

    precision = precision_score(y_true, y_pred, labels=idx, average=None, zero_division=0)
    recall = recall_score(y_true, y_pred, labels=idx, average=None, zero_division=0)
    f1 = f1_score(y_true, y_pred, labels=idx, average=None, zero_division=0)

    # Specificity & FPR one-vs-rest depuis la matrice de confusion
    specificity, fpr_rate = [], []
    for c in idx:
        tp = cm[c, c]
        fn = cm[c, :].sum() - tp
        fp = cm[:, c].sum() - tp
        tn = total - tp - fn - fp
        spec = tn / (tn + fp) if (tn + fp) else 0.0
        specificity.append(float(spec))
        fpr_rate.append(float(1.0 - spec))

    # ROC-AUC one-vs-rest (nécessite les probabilités, pas seulement les labels)
    y_bin = label_binarize(y_true, classes=idx)
    roc_auc_per_class, roc_curves = {}, {}
    for c in idx:
        key = LABELS[c]
        # garde-fou : une classe absente du y_true casserait l'AUC
        if y_bin[:, c].sum() == 0 or y_bin[:, c].sum() == len(y_true):
            roc_auc_per_class[key] = None
            roc_curves[key] = {"fpr": [0.0, 1.0], "tpr": [0.0, 1.0]}
            continue
        roc_auc_per_class[key] = float(roc_auc_score(y_bin[:, c], proba[:, c]))
        fpr_c, tpr_c, _ = roc_curve(y_bin[:, c], proba[:, c])
        roc_curves[key] = {"fpr": fpr_c.tolist(), "tpr": tpr_c.tolist()}

    valid_auc = [v for v in roc_auc_per_class.values() if v is not None]
    roc_auc_macro = float(np.mean(valid_auc)) if valid_auc else None

    per_class = {}
    for c in idx:
        key = LABELS[c]
        per_class[key] = {
            "precision": round(float(precision[c]), 4),
            "recall": round(float(recall[c]), 4),
            "f1": round(float(f1[c]), 4),
            "specificity": round(float(specificity[c]), 4),
            "fpr": round(float(fpr_rate[c]), 4),
            "roc_auc": (
                round(roc_auc_per_class[key], 4) if roc_auc_per_class[key] is not None else None
            ),
            "support": int(cm[c, :].sum()),
        }

    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_macro": round(float(precision.mean()), 4),
        "recall_macro": round(float(recall.mean()), 4),
        "f1_macro": round(float(f1.mean()), 4),
        "specificity_macro": round(float(np.mean(specificity)), 4),
        "fpr_macro": round(float(np.mean(fpr_rate)), 4),
        "roc_auc_macro": (round(roc_auc_macro, 4) if roc_auc_macro is not None else None),
        "per_class": per_class,
        "confusion_matrix": cm.astype(int).tolist(),
        "_roc_curves": roc_curves,
        "samples": total,
    }


# ── Figures ───────────────────────────────────────────────────────────────────
def _plot_confusion(model_key: str, metrics: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cm = np.array(metrics["confusion_matrix"], dtype=float)
    cm_norm = cm / np.clip(cm.sum(axis=1, keepdims=True), 1e-9, None)
    names = [DISPLAY[c] for c in LABELS]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(
        f"E2 Évaluation — Matrice de confusion · {model_key}\n({metrics['samples']:,} exemples test étiquetés)",
        fontsize=12,
        fontweight="bold",
    )

    for ax, mat, title, fmt in (
        (axes[0], cm, "Effectifs bruts", "{:.0f}"),
        (axes[1], cm_norm, "Normalisée par ligne (recall)", "{:.2f}"),
    ):
        im = ax.imshow(
            mat, cmap="Blues", vmin=0, vmax=(mat.max() if title == "Effectifs bruts" else 1.0)
        )
        ax.set_xticks(range(3))
        ax.set_xticklabels(names)
        ax.set_yticks(range(3))
        ax.set_yticklabels(names)
        ax.set_xlabel("Prédit")
        ax.set_ylabel("Réel")
        ax.set_title(title, fontsize=11)
        thresh = mat.max() / 2.0 if mat.max() else 0.5
        for r in range(3):
            for cc in range(3):
                ax.text(
                    cc,
                    r,
                    fmt.format(mat[r, cc]),
                    ha="center",
                    va="center",
                    color="white" if mat[r, cc] > thresh else "#1e293b",
                    fontsize=11,
                    fontweight="bold",
                )
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.tight_layout()
    out = FIG_DIR / f"e2_eval_confusion_{model_key}.png"
    fig.savefig(out, **STYLE)
    plt.close(fig)
    print(f"  OK {out.name}")


def _plot_roc(model_key: str, metrics: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 7))
    fig.suptitle(
        f"E2 Évaluation — Courbes ROC (TPR vs FPR) · {model_key}\none-vs-rest par classe",
        fontsize=12,
        fontweight="bold",
    )

    for c in LABELS:
        curve = metrics["_roc_curves"][c]
        auc = metrics["per_class"][c]["roc_auc"]
        auc_txt = f"AUC={auc:.3f}" if auc is not None else "AUC=n/a"
        ax.plot(
            curve["fpr"],
            curve["tpr"],
            linewidth=2.2,
            color=CLASS_COLORS[c],
            label=f"{DISPLAY[c]} ({auc_txt})",
        )

    ax.plot(
        [0, 1], [0, 1], color="#94a3b8", linestyle="--", linewidth=1.2, label="Aléatoire (AUC=0.5)"
    )
    macro = metrics.get("roc_auc_macro")
    macro_txt = f"{macro:.3f}" if macro is not None else "n/a"
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Taux de faux positifs (FPR = 1 − specificity)", fontsize=10)
    ax.set_ylabel("Taux de vrais positifs (TPR = recall)", fontsize=10)
    ax.set_title(f"ROC-AUC macro = {macro_txt}", fontsize=10, style="italic")
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", fontsize=9)

    fig.tight_layout()
    out = FIG_DIR / f"e2_eval_roc_{model_key}.png"
    fig.savefig(out, **STYLE)
    plt.close(fig)
    print(f"  OK {out.name}")


def _plot_metrics_table(model_key: str, metrics: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cols = ["Classe", "Precision", "Recall", "F1", "Specificity", "FPR", "ROC-AUC", "Support"]
    rows = []
    for c in LABELS:
        m = metrics["per_class"][c]
        auc = f"{m['roc_auc']:.3f}" if m["roc_auc"] is not None else "n/a"
        rows.append(
            [
                DISPLAY[c],
                f"{m['precision']:.3f}",
                f"{m['recall']:.3f}",
                f"{m['f1']:.3f}",
                f"{m['specificity']:.3f}",
                f"{m['fpr']:.3f}",
                auc,
                f"{m['support']:,}",
            ]
        )
    macro_auc = f"{metrics['roc_auc_macro']:.3f}" if metrics["roc_auc_macro"] is not None else "n/a"
    rows.append(
        [
            "MACRO",
            f"{metrics['precision_macro']:.3f}",
            f"{metrics['recall_macro']:.3f}",
            f"{metrics['f1_macro']:.3f}",
            f"{metrics['specificity_macro']:.3f}",
            f"{metrics['fpr_macro']:.3f}",
            macro_auc,
            f"{metrics['samples']:,}",
        ]
    )

    fig, ax = plt.subplots(figsize=(12, 4.2))
    fig.suptitle(
        f"E2 Évaluation — Synthèse métriques · {model_key}\nAccuracy = {metrics['accuracy']:.3f} "
        f"({metrics['accuracy']:.1%}) · {metrics['samples']:,} exemples",
        fontsize=12,
        fontweight="bold",
    )
    ax.axis("off")
    tbl = ax.table(
        cellText=rows, colLabels=cols, cellLoc="center", loc="center", bbox=[0.0, 0.0, 1.0, 0.9]
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    for (r, _c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor("#1e3a5f")
            cell.set_text_props(color="white", fontweight="bold")
        elif r == len(rows):  # ligne MACRO
            cell.set_facecolor("#fef3c7")
            cell.set_text_props(fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#f0f4f8")
        cell.set_edgecolor("#cbd5e1")

    fig.tight_layout()
    out = FIG_DIR / f"e2_eval_metrics_table_{model_key}.png"
    fig.savefig(out, **STYLE)
    plt.close(fig)
    print(f"  OK {out.name}")


def _write_markdown(results: dict, dataset_path: Path) -> None:
    lines = [
        "# Évaluation classification — DataSens E2",
        f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"Dataset de test : `{ai_benchmark.display_path(dataset_path)}`",
        "",
        "Problème **multiclasse** (négatif / neutre / positif). Specificity, FPR, ROC-AUC et "
        "courbes ROC calculés en **one-vs-rest** puis moyennés (macro). ROC-AUC utilise les "
        "probabilités prédites (softmax).",
        "",
    ]
    for model_key, m in results.items():
        macro_auc = f"{m['roc_auc_macro']:.4f}" if m["roc_auc_macro"] is not None else "n/a"
        lines += [
            f"## {model_key}",
            "",
            f"- Accuracy : **{m['accuracy']:.4f}** ({m['accuracy']:.1%})",
            f"- Precision macro : {m['precision_macro']:.4f} · Recall macro : {m['recall_macro']:.4f} · F1 macro : {m['f1_macro']:.4f}",
            f"- Specificity macro : {m['specificity_macro']:.4f} · FPR macro : {m['fpr_macro']:.4f} · ROC-AUC macro : **{macro_auc}**",
            "",
            "| Classe | Precision | Recall | F1 | Specificity | FPR | ROC-AUC | Support |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for c in LABELS:
            pc = m["per_class"][c]
            auc = f"{pc['roc_auc']:.4f}" if pc["roc_auc"] is not None else "n/a"
            lines.append(
                f"| {DISPLAY[c]} | {pc['precision']:.4f} | {pc['recall']:.4f} | {pc['f1']:.4f} "
                f"| {pc['specificity']:.4f} | {pc['fpr']:.4f} | {auc} | {pc['support']:,} |"
            )
        lines += [
            "",
            f"Figures : `e2_eval_confusion_{model_key}.png`, `e2_eval_roc_{model_key}.png`, "
            f"`e2_eval_metrics_table_{model_key}.png`",
            "",
        ]
    out = DOC_E2 / "EVAL_CLASSIFICATION_METRICS.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK Rapport : {out}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Évaluation complète des métriques de classification (E2)."
    )
    p.add_argument(
        "--dataset", default="data/goldai/ia/test.parquet", help="Dataset de test étiqueté."
    )
    p.add_argument(
        "--models",
        nargs="*",
        default=["finetuned_local", "sentiment_fr"],
        help="Modèles à évaluer (clés get_available_models).",
    )
    p.add_argument(
        "--per-class",
        type=int,
        default=200,
        help="Échantillons max par classe (équilibrage). 0 = tout le test set.",
    )
    p.add_argument("--max-length", type=int, default=256, help="Longueur max tokenization.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    dataset_path = PROJECT_ROOT / args.dataset
    if not dataset_path.exists():
        print(f"ERREUR: dataset introuvable: {dataset_path}")
        return 1

    dataset = ai_benchmark.load_dataset(dataset_path)
    if not dataset:
        print("ERREUR: dataset vide ou invalide.")
        return 1
    if args.per_class and args.per_class > 0:
        dataset = ai_benchmark.balanced_sample(dataset, per_class=args.per_class)

    counts = {c: sum(1 for r in dataset if r["label"] == c) for c in LABELS}
    print(
        f"Dataset éval : {len(dataset):,} exemples (neg={counts['neg']}, neu={counts['neu']}, pos={counts['pos']})"
    )

    available = ai_benchmark.get_available_models(PROJECT_ROOT)
    results: dict = {}
    for key in args.models:
        if key not in available:
            print(f"  ⚠ modèle '{key}' indisponible (choix: {', '.join(available)}). Ignoré.")
            continue
        model_name = available[key]
        print(f"\n=== {key} ({model_name}) ===")
        y_true, proba = _infer_probabilities(model_name, dataset, args.max_length)
        metrics = _compute_metrics(y_true, proba)
        macro_auc = (
            f"{metrics['roc_auc_macro']:.4f}" if metrics["roc_auc_macro"] is not None else "n/a"
        )
        print(
            f"  accuracy={metrics['accuracy']:.4f} | F1 macro={metrics['f1_macro']:.4f} | "
            f"ROC-AUC macro={macro_auc} | specificity macro={metrics['specificity_macro']:.4f}"
        )
        _plot_confusion(key, metrics)
        _plot_roc(key, metrics)
        _plot_metrics_table(key, metrics)
        metrics_public = {k: v for k, v in metrics.items() if k != "_roc_curves"}
        metrics_public["model_name"] = ai_benchmark.display_model_ref(model_name)
        results[key] = metrics_public

    if not results:
        print("ERREUR: aucun modèle évalué.")
        return 1

    json_out = DOC_E2 / "EVAL_CLASSIFICATION_METRICS.json"
    json_out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nOK Résultats : {json_out}")
    _write_markdown(results, dataset_path)
    print(f"OK Figures dans : {FIG_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
