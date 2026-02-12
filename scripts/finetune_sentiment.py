#!/usr/bin/env python3
"""
Fine-tuning CamemBERT/FlauBERT pour l'analyse de sentiment (3 classes).
Utilise la copie IA (train/val) préparée par create_ia_copy.py.
Usage: python scripts/finetune_sentiment.py [--model camembert|flaubert] [--epochs 3] [--batch-size 16]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from src.config import get_settings

# Modèles HuggingFace compatibles (sequence classification 3 classes)
HF_MODELS = {
    "camembert": "cmarkea/distilcamembert-base",  # Plus léger, rapide
    "flaubert": "flaubert/flaubert_base_uncased",  # FlauBERT français
}

LABEL2ID = {"négatif": 0, "neutre": 1, "positif": 2}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}


def load_ia_dataset(ia_dir: Path, split: str) -> pd.DataFrame:
    """Charge train, val ou test depuis data/goldai/ia/."""
    path = ia_dir / f"{split}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Copie IA introuvable: {path}. Lancez: python scripts/create_ia_copy.py")
    return pd.read_parquet(path)


def prepare_text(df: pd.DataFrame) -> tuple[list[str], list[int]]:
    """Prépare texts et labels depuis train/val. Retourne (texts, labels)."""
    title_col = "title" if "title" in df.columns else "headline"
    content_col = "content" if "content" in df.columns else "text"
    sent_col = "sentiment"

    if sent_col not in df.columns:
        raise ValueError(f"Colonne '{sent_col}' absente. Colonnes: {list(df.columns)}")

    texts = []
    labels = []
    for _, row in df.iterrows():
        title = str(row.get(title_col, "") or "")
        content = str(row.get(content_col, "") or "")
        text = f"{title} {content}".strip()[:512]
        if not text:
            continue
        sent = str(row[sent_col]).strip().lower()
        # Normaliser variations (negatif, négatif, etc.)
        if sent in ("negatif", "négatif", "negative"):
            sent = "négatif"
        elif sent in ("positif", "positive"):
            sent = "positif"
        else:
            sent = "neutre"
        if sent not in LABEL2ID:
            continue
        texts.append(text)
        labels.append(LABEL2ID[sent])

    return texts, labels


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fine-tuning CamemBERT/FlauBERT pour sentiment (positif/négatif/neutre)"
    )
    parser.add_argument(
        "--model",
        choices=["camembert", "flaubert"],
        default="camembert",
        help="Modèle de base (défaut: camembert)",
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

    train_texts, train_labels = prepare_text(train_df)
    val_texts, val_labels = prepare_text(val_df)

    if len(train_texts) < 100:
        print(
            f"ATTENTION: Peu d'exemples ({len(train_texts)}). "
            "Lancez Pipeline E1 + Fusion GoldAI + Créer copie IA pour enrichir."
        )

    print(f"  Train: {len(train_texts):,} exemples")
    print(f"  Val:   {len(val_texts):,} exemples")

    try:
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

    # Renommer pour Trainer (input_ids, attention_mask, label)
    train_ds.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    val_ds.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

    if args.eval_only:
        if not (output_path / "config.json").exists():
            print(f"Modèle fine-tuné introuvable dans {output_path}. Lancez sans --eval-only.")
            return 1
        # Évaluation avec pipeline
        import torch
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
        f1 = f1_score(val_labels[:n_eval], preds, average="weighted")
        print(f"Val accuracy ({n_eval} ex.): {acc:.2%} | F1 weighted: {f1:.4f}")
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
        metric_for_best_model="f1",
        greater_is_better=True,
        report_to="none",
    )

    def compute_metrics(eval_pred):
        preds, labels = eval_pred
        preds = preds.argmax(axis=-1)
        acc = accuracy_score(labels, preds)
        f1 = f1_score(labels, preds, average="weighted")
        return {"accuracy": acc, "f1": f1}

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer, padding=True)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print("\nDémarrage fine-tuning...")
    trainer.train()

    print("\nSauvegarde modèle...")
    trainer.save_model(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    # Métriques finales sur val
    eval_res = trainer.evaluate()
    print(f"\nRésultats validation: accuracy={eval_res.get('eval_accuracy', 0):.2%}, f1={eval_res.get('eval_f1', 0):.4f}")
    print(f"Modèle sauvegardé: {output_path.absolute()}")
    print("\nPour utiliser ce modèle: définir SENTIMENT_FINETUNED_MODEL_PATH dans .env")
    return 0


if __name__ == "__main__":
    sys.exit(main())
