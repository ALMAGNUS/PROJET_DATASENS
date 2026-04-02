"""
Export du dataset de prédictions vers Mistral pour génération d'insights.

Étape 1 : Prépare mistral_input.json depuis le dernier run d'inférence.
Étape 2 : Appelle l'API Mistral et écrit les insights dans mistral_insights.json.

Usage :
    # Préparer le fichier seulement (sans appel API)
    python scripts/export_mistral_dataset.py --export-only

    # Préparer + appeler Mistral
    python scripts/export_mistral_dataset.py

    # Filtrer sur un sujet
    python scripts/export_mistral_dataset.py --topic politique
    python scripts/export_mistral_dataset.py --topic finance
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = ROOT / "data" / "goldai" / "predictions"
OUT_DIR  = ROOT / "data" / "goldai"


# ─────────────────────────────────────────────────────────────────────────────
def find_latest_predictions() -> Path:
    files = sorted(PRED_DIR.rglob("predictions.parquet"), key=lambda f: f.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"Aucun predictions.parquet dans {PRED_DIR}\n"
                                "Lance d'abord : python scripts/run_inference_pipeline.py")
    latest = files[-1]
    print(f"[OK] Dernier run d'inférence : {latest.parent.name} ({latest.parent.parent.name})")
    return latest


def load_and_filter(path: Path, min_confidence: float, topic: str | None) -> pd.DataFrame:
    df_pred = pd.read_parquet(path)
    total_pred = len(df_pred)

    # Jointure avec gold_app_input pour récupérer le contenu complet (source, date, texte, topics)
    app_input = ROOT / "data" / "goldai" / "app" / "gold_app_input.parquet"
    if app_input.exists():
        df_app = pd.read_parquet(app_input)
        # Normalise la colonne id pour la jointure
        id_col_pred = "id" if "id" in df_pred.columns else None
        id_col_app  = "id" if "id" in df_app.columns else None
        if id_col_pred and id_col_app:
            df_pred["id"] = df_pred["id"].astype(str).str.strip()
            df_app["id"]  = df_app["id"].astype(str).str.strip()
            # Garde les colonnes de gold_app_input qui n'existent pas déjà dans predictions
            extra_cols = [c for c in df_app.columns if c not in df_pred.columns]
            df = df_pred.merge(df_app[["id"] + extra_cols], on="id", how="left")
            print(f"[OK] Jointure predictions ({total_pred}) + gold_app_input ({len(df_app)}) → {len(df)} lignes")
        else:
            df = df_pred
            print("[WARN] Jointure impossible (colonne id manquante), utilisation de predictions seul")
    else:
        df = df_pred
        print("[WARN] gold_app_input.parquet absent — run build_gold_branches.py d'abord")

    df = df[df["confidence"] >= min_confidence].copy()
    print(f"[OK] {len(df):,} / {total_pred:,} articles avec confiance >= {min_confidence}")

    if topic and "topic_1" in df.columns:
        df = df[df["topic_1"].str.lower().str.contains(topic.lower(), na=False)]
        print(f"[OK] {len(df):,} articles après filtre topic='{topic}'")

    return df


def build_mistral_input(df: pd.DataFrame, out_path: Path) -> list[dict]:
    keep = [c for c in ["title", "content", "predicted_sentiment", "confidence",
                         "p_pos", "p_neu", "p_neg", "topic_1", "source", "published_at"] if c in df.columns]
    records = df[keep].to_dict(orient="records")
    out_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(records):,} articles exportés → {out_path.relative_to(ROOT)}")
    return records


# ─────────────────────────────────────────────────────────────────────────────
def build_prompt(records: list[dict], topic: str | None) -> str:
    sujet = f"sur le thème **{topic}**" if topic else "toutes thématiques confondues"
    lines = []
    for r in records[:80]:  # max 80 articles pour rester dans la fenêtre de contexte
        sent  = r.get("predicted_sentiment", "?")
        conf  = r.get("confidence", 0)
        title = str(r.get("title", "")).strip()[:120]
        lines.append(f"- [{sent} {conf:.0%}] {title}")
    context = "\n".join(lines)

    dist = {}
    for r in records:
        s = r.get("predicted_sentiment", "?")
        dist[s] = dist.get(s, 0) + 1
    dist_str = " | ".join(f"{k}: {v}" for k, v in sorted(dist.items(), key=lambda x: -x[1]))

    return f"""Tu es un analyste politique et financier senior.

Voici {len(records)} articles de presse français analysés par le modèle DataSens ({sujet}).
Distribution des sentiments : {dist_str}

Articles (format [sentiment confiance] titre) :
{context}

Génère une analyse structurée en 3 parties :

## 1. Tendances majeures
Liste les 3 tendances dominantes de la période avec leur sentiment caractéristique.

## 2. Signaux d'alerte
Identifie les 3 signaux négatifs ou risques à surveiller.

## 3. Score de risque global
Donne un score de risque de 1 (calme) à 10 (crise) avec une justification en 2-3 lignes.
"""


def call_mistral(prompt: str, api_key: str) -> str:
    from mistralai import Mistral  # type: ignore
    client = Mistral(api_key=api_key)
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def save_insights(insights: str, out_path: Path, meta: dict) -> None:
    result = {
        "generated_at": datetime.now().isoformat(),
        "articles_used": meta.get("count", 0),
        "topic_filter": meta.get("topic"),
        "model": "mistral-large-latest",
        "insights": insights,
    }
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Insights sauvegardés → {out_path.relative_to(ROOT)}")
    print("\n" + "─" * 60)
    print(insights)


# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Export prédictions + insights Mistral")
    parser.add_argument("--export-only", action="store_true",
                        help="Prépare mistral_input.json sans appeler l'API Mistral")
    parser.add_argument("--topic", default=None,
                        help="Filtrer sur un topic (ex: politique, finance)")
    parser.add_argument("--min-confidence", type=float, default=0.6,
                        help="Seuil de confiance minimum (défaut: 0.6)")
    args = parser.parse_args()

    # Étape 1 — Préparer le fichier d'entrée
    latest = find_latest_predictions()
    df = load_and_filter(latest, args.min_confidence, args.topic)

    if df.empty:
        print("[WARN] Aucun article après filtrage. Baisse --min-confidence ou change --topic.")
        return

    suffix = f"_{args.topic}" if args.topic else ""
    input_path = OUT_DIR / f"mistral_input{suffix}.json"
    records = build_mistral_input(df, input_path)

    if args.export_only:
        print("\nFichier prêt. Pour appeler Mistral, relance sans --export-only.")
        print(f"  Ajoute MISTRAL_API_KEY dans ton .env puis : python scripts/export_mistral_dataset.py")
        return

    # Étape 2 — Appeler Mistral
    env_file = ROOT / ".env"
    api_key = None
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("MISTRAL_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

    if not api_key:
        print("[WARN] MISTRAL_API_KEY absent dans .env")
        print("  Ajoute : MISTRAL_API_KEY=ta_clé dans .env")
        print(f"  Le fichier {input_path.name} est prêt, tu peux l'utiliser manuellement.")
        return

    try:
        import mistralai  # noqa: F401
    except ImportError:
        print("[WARN] Package mistralai non installé.")
        print("  Lance : pip install mistralai")
        return

    prompt = build_prompt(records, args.topic)
    print(f"[...] Appel Mistral API ({len(records)} articles)...")
    insights = call_mistral(prompt, api_key)

    out_path = OUT_DIR / f"mistral_insights{suffix}.json"
    save_insights(insights, out_path, {"count": len(records), "topic": args.topic})


if __name__ == "__main__":
    main()
