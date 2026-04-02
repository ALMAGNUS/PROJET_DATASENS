#!/usr/bin/env python3
"""
Fine-tuning CamemBERT / FlauBERT / sentiment_fr pour l'analyse de sentiment (3 classes).
Utilise la copie IA (train/val) préparée par create_ia_copy.py.
Usage: python scripts/finetune_sentiment.py [--model camembert|flaubert|sentiment_fr] [--epochs 3] [--batch-size 16]

Classement benchmark pré-entraîné (données projet):
  1. sentiment_fr  (ac0hik/Sentiment_Analysis_French) — accuracy 57.5%, f1_macro 0.570 ← RECOMMANDÉ
  2. finetuned_local                                  — accuracy 54.2%, f1_macro 0.440 (mais f1_pos=0 sans class_weight)
  3. flaubert                                         — accuracy 42.5%, f1_macro 0.396
  4. camembert_distil                                 — accuracy 32.9%, f1_macro 0.235
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.utils.class_weight import compute_class_weight

from src.config import get_settings

# Modèles HuggingFace compatibles (sequence classification 3 classes)
HF_MODELS = {
    "sentiment_fr": "ac0hik/Sentiment_Analysis_French",  # MEILLEUR benchmark FR — recommandé
    "bert_multilingual": "nlptown/bert-base-multilingual-uncased-sentiment",  # BERT 5★, pas CamemBERT
    "camembert": "cmarkea/distilcamembert-base",         # Léger, rapide, bon sur CPU
    "flaubert": "flaubert/flaubert_base_uncased",       # FlauBERT français
}

LABEL2ID = {"négatif": 0, "neutre": 1, "positif": 2}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}


def normalize_sentiment_label(value: object) -> str | None:
    """Normalise les variantes de label vers négatif/neutre/positif."""
    s = str(value or "").strip().lower()

    negative = {"negatif", "négatif", "negative", "n�gatif"}
    positive = {"positif", "positive"}
    neutral = {"neutre", "neutral"}

    if s in negative:
        return "négatif"
    if s in positive:
        return "positif"
    if s in neutral:
        return "neutre"
    return None


def load_ia_dataset(ia_dir: Path, split: str) -> pd.DataFrame:
    """Charge train, val ou test depuis data/goldai/ia/."""
    path = ia_dir / f"{split}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Copie IA introuvable: {path}. Lancez: python scripts/create_ia_copy.py")
    return pd.read_parquet(path)


def _filter_by_topics(df: pd.DataFrame, topics: list[str]) -> pd.DataFrame:
    """Filtre les lignes où topic_1 ou topic_2 est dans la liste des topics autorisés."""
    if not topics or ("topic_1" not in df.columns and "topic_2" not in df.columns):
        return df
    allowed = {t.strip().lower() for t in topics if t.strip()}
    if not allowed:
        return df
    t1 = df.get("topic_1", pd.Series(dtype=object)).fillna("").astype(str).str.strip().str.lower()
    t2 = df.get("topic_2", pd.Series(dtype=object)).fillna("").astype(str).str.strip().str.lower()
    mask = t1.isin(allowed) | t2.isin(allowed)
    return df[mask].reset_index(drop=True)


def prepare_text(df: pd.DataFrame) -> tuple[list[str], list[int]]:
    """Prépare texts et labels depuis train/val. Retourne (texts, labels)."""
    title_col = "title" if "title" in df.columns else "headline"
    content_col = "content" if "content" in df.columns else "text"
    sent_col = "sentiment"

    if sent_col not in df.columns:
        raise ValueError(f"Colonne '{sent_col}' absente. Colonnes: {list(df.columns)}")

    texts = []
    labels = []
    skipped_unknown = 0
    for _, row in df.iterrows():
        title = str(row.get(title_col, "") or "")
        content = str(row.get(content_col, "") or "")
        text = f"{title} {content}".strip()[:512]
        if not text:
            continue
        sent = normalize_sentiment_label(row[sent_col])
        if sent is None:
            skipped_unknown += 1
            continue
        texts.append(text)
        labels.append(LABEL2ID[sent])

    if skipped_unknown:
        print(f"ATTENTION: {skipped_unknown} lignes ignorées (label sentiment inconnu).")

    return texts, labels


def rebalance_positive_class(
    texts: list[str],
    labels: list[int],
    *,
    target_pos_ratio: float,
    max_multiplier: float,
    seed: int = 42,
) -> tuple[list[str], list[int], dict]:
    """Oversample positive class to a target ratio for training stability."""
    if target_pos_ratio <= 0 or target_pos_ratio >= 1:
        return texts, labels, {"applied": False, "reason": "target_disabled"}
    if max_multiplier <= 1.0:
        return texts, labels, {"applied": False, "reason": "max_multiplier<=1"}

    pairs = pd.DataFrame({"text": texts, "label": labels})
    if pairs.empty:
        return texts, labels, {"applied": False, "reason": "empty_dataset"}

    pos_id = LABEL2ID["positif"]
    n_total = int(len(pairs))
    n_pos = int((pairs["label"] == pos_id).sum())
    if n_pos == 0:
        return texts, labels, {"applied": False, "reason": "no_positive_examples"}

    # x = (r*N - P) / (1-r), where only positives are added.
    desired_extra = int(np.ceil(((target_pos_ratio * n_total) - n_pos) / max(1e-9, (1 - target_pos_ratio))))
    if desired_extra <= 0:
        return texts, labels, {"applied": False, "reason": "already_above_target", "before_ratio": n_pos / n_total}

    max_extra = int(np.floor((max_multiplier - 1.0) * n_pos))
    extra = min(desired_extra, max_extra)
    if extra <= 0:
        return texts, labels, {"applied": False, "reason": "capped_to_zero", "before_ratio": n_pos / n_total}

    pos_rows = pairs[pairs["label"] == pos_id]
    extra_rows = pos_rows.sample(n=extra, replace=True, random_state=seed)
    out = pd.concat([pairs, extra_rows], ignore_index=True)
    out = out.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    n_total_after = int(len(out))
    n_pos_after = int((out["label"] == pos_id).sum())
    return (
        out["text"].tolist(),
        out["label"].tolist(),
        {
            "applied": True,
            "before_ratio": n_pos / n_total,
            "after_ratio": n_pos_after / n_total_after,
            "added_positive_rows": extra,
            "before_total": n_total,
            "after_total": n_total_after,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fine-tuning CamemBERT/FlauBERT pour sentiment (positif/négatif/neutre)"
    )
    parser.add_argument(
        "--model",
        choices=["sentiment_fr", "bert_multilingual", "camembert", "flaubert"],
        default="sentiment_fr",
        help="Backbone à fine-tuner: sentiment_fr (RECOMMANDÉ — meilleur benchmark 57.5%), camembert (léger/CPU), flaubert (FR)",
    )
    parser.add_argument("--epochs", type=int, default=3, help="Nombre d'epochs (défaut: 3)")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size (défaut: 16)")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate (défaut: 2e-5)")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Répertoire de sortie (défaut: models/{model}-sentiment-finetuned)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=256,
        help="Longueur max tokens (défaut: 256)",
    )
    parser.add_argument(
        "--eval-only",
        action="store_true",
        help="Évaluer uniquement un modèle existant (sans entraînement)",
    )
    parser.add_argument(
        "--max-train-samples",
        type=int,
        default=0,
        help="Limiter le nombre d'exemples train (0 = tous).",
    )
    parser.add_argument(
        "--max-val-samples",
        type=int,
        default=0,
        help="Limiter le nombre d'exemples validation (0 = tous).",
    )
    parser.add_argument(
        "--topics",
        type=str,
        default="",
        help="Filtrer par topics (ex: finance,politique). Vide = toutes. Améliore restitution veille.",
    )
    parser.add_argument(
        "--target-pos-ratio",
        type=float,
        default=0.0,
        help="Ratio cible de la classe positif dans TRAIN via sur-échantillonnage (0=off, ex: 0.25).",
    )
    parser.add_argument(
        "--pos-oversample-max-multiplier",
        type=float,
        default=3.0,
        help="Multiplicateur max d'exemples positifs (sécurité anti-sur-apprentissage).",
    )
    args = parser.parse_args()

    settings = get_settings()
    goldai_base = Path(settings.goldai_base_path)
    if not goldai_base.is_absolute():
        goldai_base = project_root / goldai_base
    ia_dir = goldai_base / "ia"

    # Charger train et val
    if not args.eval_only:
        print(
            "ATTENTION CPU: Le fine-tuning sur CPU est lent (10-60 min selon données). "
            "Préférez inférence seule (modèle pré-entraîné) ou GPU si disponible."
        )
    print("Chargement copie IA (train/val)...")
    train_df = load_ia_dataset(ia_dir, "train")
    val_df = load_ia_dataset(ia_dir, "val")

    # Filtre par topics (finance, politique) pour veille ciblée
    if args.topics:
        topics_list = [t.strip() for t in args.topics.split(",") if t.strip()]
        if topics_list:
            n_train_before, n_val_before = len(train_df), len(val_df)
            train_df = _filter_by_topics(train_df, topics_list)
            val_df = _filter_by_topics(val_df, topics_list)
            print(f"  Filtre topics [{', '.join(topics_list)}]: train {n_train_before:,}→{len(train_df):,}, val {n_val_before:,}→{len(val_df):,}")

    train_texts, train_labels = prepare_text(train_df)
    val_texts, val_labels = prepare_text(val_df)

    if args.max_train_samples and args.max_train_samples > 0 and len(train_texts) > args.max_train_samples:
        train_pairs = list(zip(train_texts, train_labels))
        train_pairs = pd.DataFrame(train_pairs, columns=["text", "label"]).sample(
            n=args.max_train_samples, random_state=42
        )
        train_texts = train_pairs["text"].tolist()
        train_labels = train_pairs["label"].tolist()

    if args.max_val_samples and args.max_val_samples > 0 and len(val_texts) > args.max_val_samples:
        val_pairs = list(zip(val_texts, val_labels))
        val_pairs = pd.DataFrame(val_pairs, columns=["text", "label"]).sample(
            n=args.max_val_samples, random_state=42
        )
        val_texts = val_pairs["text"].tolist()
        val_labels = val_pairs["label"].tolist()

    train_texts, train_labels, rebalance_info = rebalance_positive_class(
        train_texts,
        train_labels,
        target_pos_ratio=args.target_pos_ratio,
        max_multiplier=args.pos_oversample_max_multiplier,
        seed=42,
    )
    if rebalance_info.get("applied"):
        print(
            "Recalibrage positif appliqué: "
            f"{rebalance_info.get('before_ratio', 0):.2%} -> {rebalance_info.get('after_ratio', 0):.2%} "
            f"(+{rebalance_info.get('added_positive_rows', 0)} lignes)"
        )
    else:
        print(f"Recalibrage positif: non appliqué ({rebalance_info.get('reason', 'n/a')}).")

    if len(train_texts) < 100:
        print(
            f"ATTENTION: Peu d'exemples ({len(train_texts)}). "
            "Lancez Pipeline E1 + Fusion GoldAI + Créer copie IA pour enrichir."
        )

    print(f"  Train: {len(train_texts):,} exemples")
    print(f"  Val:   {len(val_texts):,} exemples")

    try:
        import torch
        from datasets import Dataset
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            DataCollatorWithPadding,
            Trainer,
            TrainingArguments,
        )
    except ImportError as e:
        print(f"ERREUR: Dépendances manquantes. pip install transformers datasets - {e}")
        return 1

    # --- Calcul des class weights (correctif déséquilibre: positif=13%) ---
    label_array = np.array(train_labels)
    classes = np.array([0, 1, 2])
    raw_weights = compute_class_weight("balanced", classes=classes, y=label_array)
    class_weights_np = raw_weights
    dist = {ID2LABEL[c]: int((label_array == c).sum()) for c in classes}
    print(f"\nDistribution classes (train): {dist}")
    print(f"Class weights auto: {[f'{ID2LABEL[i]}={w:.2f}' for i, w in enumerate(class_weights_np)]}")

    model_name = HF_MODELS[args.model]
    output_dir = args.output_dir or f"models/{args.model}-sentiment-finetuned"
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = project_root / output_path
    output_path.mkdir(parents=True, exist_ok=True)

    # Tokenizer et modèle
    print(f"\nChargement {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=3,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,  # Nécessaire pour sentiment_fr (head remplacé)
    )

    def tokenize_fn(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=args.max_length,
            padding="max_length",
        )

    # Datasets HuggingFace
    train_ds = Dataset.from_dict({"text": train_texts, "label": train_labels})
    val_ds = Dataset.from_dict({"text": val_texts, "label": val_labels})

    train_ds = train_ds.map(
        tokenize_fn,
        batched=True,
        remove_columns=["text"],
        desc="Tokenize train",
    )
    val_ds = val_ds.map(
        tokenize_fn,
        batched=True,
        remove_columns=["text"],
        desc="Tokenize val",
    )

    train_ds.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    val_ds.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

    if args.eval_only:
        # Pour eval-only : priorité config > output_path par défaut
        eval_path = output_path
        if settings.sentiment_finetuned_model_path:
            p = Path(settings.sentiment_finetuned_model_path)
            if not p.is_absolute():
                p = project_root / p
            if (p / "config.json").exists():
                eval_path = p
        if not (eval_path / "config.json").exists():
            for fallback in ["sentiment_fr-sentiment-finetuned", "camembert-sentiment-finetuned"]:
                fb = project_root / "models" / fallback
                if (fb / "config.json").exists():
                    eval_path = fb
                    break
        if not (eval_path / "config.json").exists():
            print(f"Modèle fine-tuné introuvable. Vérifiez SENTIMENT_FINETUNED_MODEL_PATH ou lancez le fine-tuning.")
            return 1
        output_path = eval_path
        from transformers import pipeline
        device = 0 if torch.cuda.is_available() else -1
        pipe = pipeline(
            "text-classification",
            model=str(output_path),
            tokenizer=str(output_path),
            device=device,
        )
        preds = []
        for t in val_texts[:500]:
            out = pipe(t[:256], truncation=True, max_length=args.max_length)
            lbl = out[0]["label"].lower().replace("positive", "positif").replace("negative", "négatif")
            preds.append(LABEL2ID.get(lbl, 1))
        n_eval = min(500, len(val_labels))
        acc = accuracy_score(val_labels[:n_eval], preds)
        f1_w = f1_score(val_labels[:n_eval], preds, average="weighted")
        f1_m = f1_score(val_labels[:n_eval], preds, average="macro")
        f1_pc = f1_score(val_labels[:n_eval], preds, average=None, labels=[0, 1, 2])
        print(f"Val accuracy ({n_eval} ex.): {acc:.2%} | F1 weighted: {f1_w:.4f} | F1 macro: {f1_m:.4f}")
        print(f"F1 per class: négatif={f1_pc[0]:.3f}, neutre={f1_pc[1]:.3f}, positif={f1_pc[2]:.3f}")
        return 0

    training_args = TrainingArguments(
        output_dir=str(output_path),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        learning_rate=args.lr,
        weight_decay=0.01,
        warmup_ratio=0.1,
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        report_to="none",
        dataloader_pin_memory=torch.cuda.is_available(),
    )

    def compute_metrics(eval_pred):
        preds, labels = eval_pred
        preds = preds.argmax(axis=-1)
        acc = accuracy_score(labels, preds)
        f1_w = f1_score(labels, preds, average="weighted")
        f1_m = f1_score(labels, preds, average="macro")
        f1_pc = f1_score(labels, preds, average=None, labels=[0, 1, 2])
        return {
            "accuracy": acc,
            "f1": f1_w,
            "f1_macro": f1_m,
            "f1_neg": float(f1_pc[0]),
            "f1_neu": float(f1_pc[1]),
            "f1_pos": float(f1_pc[2]),
        }

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer, padding=True)

    # Trainer avec class weights pour corriger le déséquilibre (positif sous-représenté)
    class_weights_tensor = torch.tensor(class_weights_np, dtype=torch.float)

    class WeightedTrainer(Trainer):
        """Trainer avec CrossEntropyLoss pondérée par classe."""
        def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
            labels = inputs.get("labels")
            outputs = model(**inputs)
            logits = outputs.get("logits")
            weight = class_weights_tensor.to(logits.device)
            loss_fn = torch.nn.CrossEntropyLoss(weight=weight)
            loss = loss_fn(logits.view(-1, model.config.num_labels), labels.view(-1))
            return (loss, outputs) if return_outputs else loss

    trainer = WeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print(f"\nDémarrage fine-tuning ({args.model} | {args.epochs} epochs | class weights actifs)...")
    trainer.train()

    print("\nSauvegarde modèle...")
    trainer.save_model(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    # Métriques finales sur val
    eval_res = trainer.evaluate()
    acc = eval_res.get("eval_accuracy", 0)
    f1m = eval_res.get("eval_f1_macro", 0)
    f1w = eval_res.get("eval_f1", 0)
    f1p = eval_res.get("eval_f1_pos", 0)
    print(f"\nRésultats val: accuracy={acc:.2%} | F1 macro={f1m:.4f} | F1 weighted={f1w:.4f} | F1 positif={f1p:.4f}")
    print(f"Modèle sauvegardé: {output_path.absolute()}")

    # Écriture TRAINING_RESULTS.json pour plot_e2_results.py (quick ou full)
    mode = "quick" if args.max_train_samples and args.max_train_samples > 0 else "full"
    state = trainer.state
    log_hist = getattr(state, "log_history", []) or []
    train_loss_final = 0.0
    for e in reversed(log_hist):
        if "loss" in e and "eval_loss" not in e:
            train_loss_final = float(e.get("loss", 0))
            break
    eval_loss = float(eval_res.get("eval_loss", 0))
    train_runtime = float(getattr(state, "train_runtime", 0) or 0)
    train_sps = float(getattr(state, "train_samples_per_second", 0) or 0)
    train_stps = float(getattr(state, "train_steps_per_second", 0) or 0)
    from datetime import datetime
    results_json = {
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "mode": mode,
        "model": args.model,
        "train_samples": len(train_texts),
        "val_samples": len(val_texts),
        "epochs": args.epochs,
        "train_loss_final": train_loss_final,
        "eval_loss": eval_loss,
        "eval_accuracy": float(acc),
        "eval_f1_weighted": float(f1w),
        "eval_f1_macro": float(f1m),
        "train_runtime_seconds": train_runtime,
        "train_samples_per_second": train_sps,
        "train_steps_per_second": train_stps,
        "target_pos_ratio": float(args.target_pos_ratio),
        "pos_oversample_max_multiplier": float(args.pos_oversample_max_multiplier),
        "positive_rebalance": rebalance_info,
    }
    results_path = project_root / "docs" / "e2" / "TRAINING_RESULTS.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8") as f:
        json.dump(results_json, f, indent=2, ensure_ascii=False)
    print(f"Résultats training écrits: {results_path}")

    # MLflow explicitement désactivé sur ce projet (trop lourd pour le run quotidien).
    print("MLflow: désactivé (versioning local via fichiers JSON + artefacts modèles).")

    print(f"\nPour utiliser ce modèle, ajoutez dans .env :")
    print(f"  SENTIMENT_FINETUNED_MODEL_PATH=models/{args.model}-sentiment-finetuned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
