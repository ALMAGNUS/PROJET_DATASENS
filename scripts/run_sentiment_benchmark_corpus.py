"""Benchmark sentiment — corpus de test de référence (ac0hik + calibration)."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.ml.inference.local_hf_service import LocalHFService
from src.ml.inference.sentiment_postprocess import finalize_sentiment

CORPUS_PATH = ROOT / "data" / "tests" / "sentiment_benchmark_corpus.csv"
LABEL_MAP = {"positive": "POSITIVE", "negative": "NEGATIVE", "neutral": "NEUTRAL"}


def load_corpus(path: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append((row["id"], row["text"], row["label_expected"]))
    return rows


def _to_expected(label: str) -> str:
    return LABEL_MAP[label.lower()]


def _to_predicted_label(raw: str) -> str:
    u = raw.upper()
    if u.startswith("POS"):
        return "POSITIVE"
    if u.startswith("NEG") or u.startswith("NÉG"):
        return "NEGATIVE"
    return "NEUTRAL"


def main() -> None:
    corpus = load_corpus(CORPUS_PATH)
    svc = LocalHFService(model_name="ac0hik/Sentiment_Analysis_French", task="text-classification")
    rows: list[dict] = []
    for tid, text, expected in corpus:
        raw = svc.predict(text, return_all_scores=True)
        scores = raw[0] if raw and isinstance(raw[0], list) else raw
        out = finalize_sentiment(text, scores)
        pred = _to_predicted_label(out["label"])
        exp = _to_expected(expected)
        rows.append(
            {
                "id": tid,
                "text": text,
                "label_expected": expected,
                "label_predicted": pred.lower(),
                "confidence_score": out["confidence"],
                "sentiment_score": out.get("sentiment_score"),
                "is_correct": pred == exp,
                "refined": out.get("refined", ""),
            }
        )

    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / "sentiment_benchmark_corpus_results.csv"
    json_path = out_dir / "sentiment_benchmark_corpus_results.json"

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "text",
                "label_expected",
                "label_predicted",
                "confidence_score",
                "sentiment_score",
                "is_correct",
                "refined",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    total = len(rows)
    correct = sum(1 for r in rows if r["is_correct"])
    by_group: dict[str, dict[str, int]] = {}
    for r in rows:
        g = "NE" if r["id"].startswith("NE") else r["id"][0]
        by_group.setdefault(g, {"ok": 0, "n": 0})
        by_group[g]["n"] += 1
        if r["is_correct"]:
            by_group[g]["ok"] += 1

    summary = {
        "corpus": str(CORPUS_PATH.relative_to(ROOT)),
        "total": total,
        "correct": correct,
        "accuracy_pct": round(100 * correct / total, 1),
        "by_prefix": {
            k: {**v, "accuracy_pct": round(100 * v["ok"] / v["n"], 1)} for k, v in by_group.items()
        },
        "errors": [r for r in rows if not r["is_correct"]],
    }
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Accuracy: {correct}/{total} ({summary['accuracy_pct']}%)")
    for k, v in sorted(by_group.items()):
        print(f"  {k}: {v['ok']}/{v['n']} ({round(100*v['ok']/v['n'],1)}%)")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    if summary["errors"]:
        print("\nErreurs:")
        for r in summary["errors"]:
            print(
                f"  {r['id']}: attendu={r['label_expected']} pred={r['label_predicted']} conf={r['confidence_score']}"
            )


if __name__ == "__main__":
    main()
