"""Compare sentiment_fr vs fine-tuned sur phrases de demo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.e2.api.routes.ai import _resolve_sentiment_model
from src.ml.inference.local_hf_service import LocalHFService, compute_sentiment_output

TEXTS = [
    ("Financier negatif", "L'inflation inquiète les investisseurs et freine la croissance."),
    ("Financier positif", "Le marché boursier affiche une forte hausse cette semaine."),
    ("Politique", "Le gouvernement annonce de nouvelles mesures sociales controversées."),
]

MODELS = [
    ("sentiment_fr", _resolve_sentiment_model("sentiment_fr")),
    ("finetuned_local (env)", _resolve_sentiment_model("finetuned_local")),
]

_local = Path("models/sentiment_fr-sentiment-finetuned")
if (_local / "config.json").exists():
    MODELS.append(("finetuned_local (disk)", str(_local.resolve())))


def run_one(model_id: str, hf_path: str, text: str) -> dict:
    svc = LocalHFService(model_name=hf_path, task="text-classification")
    raw = svc.predict(text, return_all_scores=True)
    scores = raw[0] if raw and isinstance(raw[0], list) else raw
    out = compute_sentiment_output(scores)
    out["_raw_scores"] = scores
    out["_hf_path"] = hf_path
    return out


def main() -> None:
    print("=" * 72)
    for label, text in TEXTS:
        print(f"\n>>> {label}: {text[:60]}...")
        for choice, path in MODELS:
            out = run_one(choice, path, text)
            print(f"  [{choice}] path={path}")
            for s in out["_raw_scores"]:
                print(f"      raw: {s['label']!r} = {s['score']:.4f}")
            print(
                f"      => {out['label']}  score={out['sentiment_score']:+.3f}  "
                f"conf={out['confidence']:.3f}"
            )


if __name__ == "__main__":
    main()
