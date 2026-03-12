"""
Benchmark IA (C7) - benchmark de modèles de sentiment avec scores.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from datetime import datetime
from pathlib import Path


BASE_MODELS = {
    # BERT multilingue 5★ (1-2→neg, 3→neu, 4-5→pos) — PyTorch, pas CamemBERT
    "bert_multilingual": "nlptown/bert-base-multilingual-uncased-sentiment",
    # XLM-RoBERTa Twitter multilingue
    "flaubert_multilingual": "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
    # Modèle FR dédié presse/opinion (ac0hik)
    "sentiment_fr": "ac0hik/Sentiment_Analysis_French",
}


def _label_to_polarity(label: str) -> str:
    lbl = str(label).lower()
    if any(x in lbl for x in ["positive", "pos", "positif", "5", "very_pos", "4"]):
        return "pos"
    if any(x in lbl for x in ["negative", "neg", "négatif", "1", "very_neg", "2"]):
        return "neg"
    return "neu"


def compute_sentiment(scores: list[dict]) -> tuple[str, float]:
    p_pos = p_neu = p_neg = 0.0
    for item in scores:
        pol = _label_to_polarity(item.get("label", ""))
        sc = float(item.get("score", 0))
        if pol == "pos":
            p_pos += sc
        elif pol == "neg":
            p_neg += sc
        else:
            p_neu += sc
    total = p_pos + p_neu + p_neg
    if total > 0:
        p_pos, p_neu, p_neg = p_pos / total, p_neu / total, p_neg / total
    probs = [("pos", p_pos), ("neu", p_neu), ("neg", p_neg)]
    pred, conf = max(probs, key=lambda x: x[1])
    return pred, conf


def load_dataset(path: Path) -> list[dict]:
    def norm_label(raw: str) -> str | None:
        lbl = str(raw).strip().lower()
        if lbl in {"pos", "positive", "positif", "5", "4"}:
            return "pos"
        if lbl in {"neg", "negative", "négatif", "negatif", "1", "2"}:
            return "neg"
        if lbl in {"neu", "neutral", "neutre", "neutre."}:
            return "neu"
        return None

    def load_csv_dataset(csv_path: Path) -> list[dict]:
        rows: list[dict] = []
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                label = norm_label(row.get("label", ""))
                text = str(row.get("text", "")).strip()
                if label and text:
                    rows.append({"label": label, "text": text})
        return rows

    def load_parquet_dataset(parquet_path: Path) -> list[dict]:
        try:
            import pandas as pd
        except Exception as e:
            raise RuntimeError("Lecture parquet impossible: pandas non disponible dans cet environnement.") from e

        df = pd.read_parquet(parquet_path)
        possible_text_cols = ["content", "text", "cleaned", "title"]
        possible_label_cols = ["sentiment", "label"]

        text_col = next((c for c in possible_text_cols if c in df.columns), None)
        label_col = next((c for c in possible_label_cols if c in df.columns), None)
        if not text_col or not label_col:
            raise RuntimeError(f"Colonnes manquantes dans {parquet_path}. Colonnes disponibles: {list(df.columns)}")

        rows: list[dict] = []
        for _, row in df.iterrows():
            label = norm_label(str(row.get(label_col, "")))
            text = str(row.get(text_col, "")).strip()
            if label and text and text.lower() not in {"nan", "none"}:
                rows.append({"label": label, "text": text})
        return rows

    if path.suffix.lower() == ".parquet":
        return load_parquet_dataset(path)

    rows: list[dict] = []
    rows.extend(load_csv_dataset(path))
    return rows


def balanced_sample(dataset: list[dict], per_class: int, seed: int = 42) -> list[dict]:
    if per_class <= 0:
        return dataset
    buckets = {"neg": [], "neu": [], "pos": []}
    for row in dataset:
        lbl = row.get("label")
        if lbl in buckets:
            buckets[lbl].append(row)

    rnd = random.Random(seed)
    sampled: list[dict] = []
    for lbl in ("neg", "neu", "pos"):
        bucket = buckets[lbl]
        rnd.shuffle(bucket)
        sampled.extend(bucket[: min(per_class, len(bucket))])
    rnd.shuffle(sampled)
    return sampled


def evaluate_model(model_name: str, dataset: list[dict], max_length: int) -> dict:
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except Exception as e:
        raise RuntimeError(
            "Impossible d'importer transformers/torch dans cet environnement. "
            "Créer un venv propre et installer requirements.txt, "
            "ou corriger numpy/scipy/sklearn."
        ) from e

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()
    id2label = getattr(model.config, "id2label", {}) or {}

    def infer_scores(text: str) -> list[dict]:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
        with torch.no_grad():
            logits = model(**inputs).logits[0]
        probs = torch.softmax(logits, dim=-1).tolist()
        scores = []
        for i, p in enumerate(probs):
            label = str(id2label.get(i, f"LABEL_{i}"))
            scores.append({"label": label, "score": float(p)})
        return scores

    y_true: list[str] = []
    y_pred: list[str] = []
    confidences: list[float] = []
    latencies_ms: list[float] = []

    for sample in dataset:
        t0 = time.perf_counter()
        scores = infer_scores(sample["text"])
        dt = (time.perf_counter() - t0) * 1000.0
        pred, conf = compute_sentiment(scores)
        y_true.append(sample["label"])
        y_pred.append(pred)
        confidences.append(conf)
        latencies_ms.append(dt)

    labels = ["neg", "neu", "pos"]
    total = len(y_true)
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    acc = correct / total if total else 0.0

    per_class = {}
    f1_sum = 0.0
    f1_weighted_sum = 0.0
    for lbl in labels:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == lbl and yp == lbl)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != lbl and yp == lbl)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == lbl and yp != lbl)
        support = sum(1 for yt in y_true if yt == lbl)

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[lbl] = {
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1": round(float(f1), 4),
            "support": int(support),
        }
        f1_sum += f1
        f1_weighted_sum += f1 * support

    f1_macro = f1_sum / len(labels) if labels else 0.0
    f1_weighted = f1_weighted_sum / total if total else 0.0

    return {
        "accuracy": round(float(acc), 4),
        "f1_macro": round(float(f1_macro), 4),
        "f1_weighted": round(float(f1_weighted), 4),
        "avg_confidence": round(sum(confidences) / max(len(confidences), 1), 4),
        "avg_latency_ms": round(sum(latencies_ms) / max(len(latencies_ms), 1), 2),
        "per_class": per_class,
        "samples": len(dataset),
    }


def write_report(docs_dir: Path, results: dict, dataset_path: Path, class_counts: dict[str, int]) -> None:
    bench_path = docs_dir / "AI_BENCHMARK.md"
    reqs_path = docs_dir / "AI_REQUIREMENTS.md"
    raw_json_path = docs_dir / "AI_BENCHMARK_RESULTS.json"

    ranked = sorted(results.items(), key=lambda x: (x[1].get("f1_macro", 0), x[1].get("accuracy", 0)), reverse=True)
    winner = ranked[0][0] if ranked else "n/a"

    bench = [
        "# Benchmark IA - DataSens E2",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Méthode",
        f"Dataset de référence: `{dataset_path.as_posix()}`",
        "Métriques: Accuracy, F1 macro, F1 pondéré, confiance moyenne, latence moyenne (ms).",
        f"Répartition des classes évaluées: neg={class_counts.get('neg', 0)}, neu={class_counts.get('neu', 0)}, pos={class_counts.get('pos', 0)}.",
        "",
        "## Résultats comparatifs",
        "",
        "| Modèle | Accuracy | F1 macro | F1 pondéré | Confiance moy. | Latence moy. (ms) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, met in ranked:
        bench.append(
            f"| `{key}` | {met['accuracy']:.4f} | {met['f1_macro']:.4f} | {met['f1_weighted']:.4f} | {met['avg_confidence']:.4f} | {met['avg_latency_ms']:.2f} |"
        )

    bench.extend(
        [
            "",
            "## Recommandation",
            f"Le modèle recommandé est `{winner}` car il obtient le meilleur compromis entre F1 macro et accuracy sur le dataset de référence.",
            "Les résultats détaillés (par classe) sont conservés dans `docs/e2/AI_BENCHMARK_RESULTS.json`.",
        ]
    )

    reqs = [
        "# Exigences IA - DataSens E2",
        "",
        "## Problématique",
        "Comparer objectivement plusieurs modèles de sentiment pour sélectionner un moteur principal mesuré.",
        "",
        "## Contraintes",
        "- Données sensibles: privilégier le traitement local",
        "- Exécution CPU",
        "- Latence compatible API",
        "- Qualité mesurable (scores reproductibles)",
        "",
        "## Critères de décision",
        "- Priorité 1: F1 macro (équilibre classes)",
        "- Priorité 2: Accuracy",
        "- Priorité 3: Latence moyenne",
        "",
        f"## Recommandation actuelle\n`{winner}` sur la base du benchmark daté.",
    ]

    bench_path.write_text("\n".join(bench), encoding="utf-8")
    reqs_path.write_text("\n".join(reqs), encoding="utf-8")
    raw_json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK Benchmark: {bench_path}")
    print(f"OK Exigences: {reqs_path}")
    print(f"OK Résultats bruts: {raw_json_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark sentiment models for E2.")
    parser.add_argument(
        "--dataset",
        default="data/goldai/ia/test.parquet",
        help="Chemin vers dataset CSV ou Parquet.",
    )
    parser.add_argument("--max-samples", type=int, default=0, help="Limiter le nombre d'échantillons (0 = tous).")
    parser.add_argument("--max-length", type=int, default=256, help="Longueur max tokenization.")
    parser.add_argument("--per-class", type=int, default=120, help="Nombre max d'échantillons par classe (0 = pas d'équilibrage).")
    parser.add_argument(
        "--models",
        nargs="*",
        default=[],
        help="Clés de modèles à évaluer. Vide = tous les modèles disponibles.",
    )
    return parser.parse_args()


def get_available_models(project_root: Path) -> dict[str, str]:
    models = dict(BASE_MODELS)
    # Priorité : config .env > sentiment_fr (meilleur bench) > camembert
    try:
        from src.config import get_settings
        cfg = get_settings()
        if cfg.sentiment_finetuned_model_path:
            p = Path(cfg.sentiment_finetuned_model_path)
            if not p.is_absolute():
                p = project_root / p
            if (p / "config.json").exists():
                models["finetuned_local"] = str(p.resolve())
                return models
    except Exception:
        pass
    for preferred in ["sentiment_fr-sentiment-finetuned", "camembert-sentiment-finetuned"]:
        local_ft = project_root / "models" / preferred
        if (local_ft / "config.json").exists():
            models["finetuned_local"] = str(local_ft)
            break
    return models


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs" / "e2"
    docs_dir.mkdir(parents=True, exist_ok=True)
    available_models = get_available_models(project_root)

    dataset_path = project_root / args.dataset
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset introuvable: {dataset_path}")
    dataset = load_dataset(dataset_path)
    if not dataset:
        raise RuntimeError("Dataset vide ou invalide.")
    if args.per_class and args.per_class > 0:
        dataset = balanced_sample(dataset, per_class=args.per_class)
    if args.max_samples and args.max_samples > 0:
        dataset = dataset[: args.max_samples]
    class_counts = {"neg": 0, "neu": 0, "pos": 0}
    for row in dataset:
        class_counts[row["label"]] = class_counts.get(row["label"], 0) + 1

    if args.models:
        selected_models = {k: v for k, v in available_models.items() if k in set(args.models)}
    else:
        selected_models = available_models
    if not selected_models:
        raise RuntimeError(
            f"Aucun modèle valide sélectionné. Choix possibles: {', '.join(available_models.keys())}"
        )

    results: dict = {}
    for key, model_name in selected_models.items():
        print(f"Running benchmark for {key} ({model_name})...")
        try:
            results[key] = evaluate_model(model_name, dataset, max_length=args.max_length)
            results[key]["model_name"] = model_name
        except Exception as e:
            results[key] = {"error": str(e), "model_name": model_name}

    valid_results = {k: v for k, v in results.items() if "error" not in v}
    if not valid_results:
        raise RuntimeError("Tous les benchmarks ont échoué. Vérifier connexion/modèles.")
    write_report(docs_dir, valid_results, dataset_path, class_counts)


if __name__ == "__main__":
    main()
