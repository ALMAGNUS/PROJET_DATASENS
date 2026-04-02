#!/usr/bin/env python3
"""
Publish the best local fine-tuned sentiment model to Hugging Face Hub.

Usage examples:
  python scripts/publish_best_model_to_hf.py --repo-id yourname/datasens-sentiment-fr
  python scripts/publish_best_model_to_hf.py --repo-id yourname/datasens-sentiment-fr --private
  python scripts/publish_best_model_to_hf.py --repo-id yourname/datasens-sentiment-fr --dry-run
  python scripts/publish_best_model_to_hf.py --repo-id yourname/datasens-sentiment-fr --revision-tag v1.1
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


@dataclass
class Candidate:
    model_name: str
    checkpoint_dir: Path
    eval_accuracy: float
    eval_f1_macro: float
    step: int


def _extract_last_eval(trainer_state_path: Path) -> dict | None:
    try:
        payload = json.loads(trainer_state_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    log = payload.get("log_history", [])
    eval_rows = [row for row in log if "eval_accuracy" in row]
    if not eval_rows:
        return None
    return eval_rows[-1]


def discover_candidates(models_dir: Path) -> list[Candidate]:
    candidates: list[Candidate] = []
    if not models_dir.exists():
        return candidates
    for model_dir in sorted(models_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        for state_path in model_dir.rglob("trainer_state.json"):
            eval_row = _extract_last_eval(state_path)
            if not eval_row:
                continue
            checkpoint_dir = state_path.parent
            candidates.append(
                Candidate(
                    model_name=model_dir.name,
                    checkpoint_dir=checkpoint_dir,
                    eval_accuracy=float(eval_row.get("eval_accuracy", 0.0) or 0.0),
                    eval_f1_macro=float(eval_row.get("eval_f1_macro", 0.0) or 0.0),
                    step=int(eval_row.get("step", 0) or 0),
                )
            )
    return candidates


def select_best(candidates: list[Candidate]) -> Candidate | None:
    if not candidates:
        return None
    return max(candidates, key=lambda c: (c.eval_accuracy, c.eval_f1_macro, c.step))


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish best fine-tuned model to Hugging Face Hub")
    parser.add_argument("--repo-id", required=True, help="Hugging Face repo id, e.g. username/datasens-sentiment-fr")
    parser.add_argument("--token-env", default="HF_TOKEN", help="Environment variable containing HF token")
    parser.add_argument("--private", action="store_true", help="Create private model repo")
    parser.add_argument("--dry-run", action="store_true", help="Only print best candidate, do not push")
    parser.add_argument(
        "--revision-tag",
        default="",
        help="Optional Hugging Face tag to create after push (ex: v1.0, v1.1).",
    )
    args = parser.parse_args()

    candidates = discover_candidates(MODELS_DIR)
    best = select_best(candidates)
    if not best:
        print("No fine-tuned checkpoint found in models/.")
        return 1

    print("Best local checkpoint detected:")
    print(f"  model_name     : {best.model_name}")
    print(f"  checkpoint_dir : {best.checkpoint_dir}")
    print(f"  eval_accuracy  : {best.eval_accuracy:.4f}")
    print(f"  eval_f1_macro  : {best.eval_f1_macro:.4f}")
    print(f"  step           : {best.step}")

    if args.dry_run:
        return 0

    token = (
        os.getenv(args.token_env, "").strip()
        or os.getenv("HUGGINGFACE_HUB_TOKEN", "").strip()
        or os.getenv("HUGGINGFACE_API_KEY", "").strip()
    )
    if not token:
        print(
            f"Missing token: set {args.token_env} (or HUGGINGFACE_HUB_TOKEN / HUGGINGFACE_API_KEY) in your environment."
        )
        return 1

    from huggingface_hub import HfApi, login
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    login(token=token)
    api = HfApi()
    api.create_repo(repo_id=args.repo_id, repo_type="model", private=args.private, exist_ok=True)

    model = AutoModelForSequenceClassification.from_pretrained(str(best.checkpoint_dir))
    tokenizer = AutoTokenizer.from_pretrained(str(best.checkpoint_dir))

    commit_msg = (
        f"Publish best DataSens checkpoint "
        f"(acc={best.eval_accuracy:.4f}, f1_macro={best.eval_f1_macro:.4f}, step={best.step})"
    )
    model.push_to_hub(args.repo_id, commit_message=commit_msg)
    tokenizer.push_to_hub(args.repo_id, commit_message=commit_msg)

    created_tag = ""
    if args.revision_tag.strip():
        created_tag = args.revision_tag.strip()
        try:
            api.create_tag(
                repo_id=args.repo_id,
                repo_type="model",
                tag=created_tag,
                tag_message=commit_msg,
            )
            print(f"Created HF revision tag: {created_tag}")
        except Exception as exc:
            print(f"Warning: unable to create tag '{created_tag}': {exc}")
            created_tag = ""

    summary = {
        "repo_id": args.repo_id,
        "model_name": best.model_name,
        "checkpoint_dir": str(best.checkpoint_dir),
        "eval_accuracy": best.eval_accuracy,
        "eval_f1_macro": best.eval_f1_macro,
        "step": best.step,
        "revision_tag": created_tag,
    }
    out = PROJECT_ROOT / "docs" / "e2" / "HF_MODEL_PUBLISH.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Pushed to Hugging Face: https://huggingface.co/{args.repo_id}")
    print(f"Publish summary saved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

