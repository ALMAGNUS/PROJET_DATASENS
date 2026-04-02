"""
DataSens Streamlit — helpers de calcul pur (sans streamlit).

Ce module centralise les fonctions de data-wrangling et de scan de fichiers
extraites de app.py. Le code d'affichage (st.xxx) reste dans app.py.

Plan de migration M6 :
  Phase 1 (fait) : fmt_size, scan_stage
  Phase 2 (fait) : stage_time_range, chrono_data, ia_metrics_from_parquet,
                   enrich_profile, build_enrichment_table
  Phase 3 (fait) : load_benchmark_results, sentiment_benchmark_diagnosis,
                   go_no_go_snapshot, scan_trained_models
  Phase 4 : découper app.py en sous-modules src/streamlit/pages/*.py
"""

from __future__ import annotations

import csv
import datetime
import json
import re
import time
from pathlib import Path

import pandas as pd


def fmt_size(num: int) -> str:
    """Formatte un nombre d'octets en unité lisible (KB / MB / GB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} PB"


def scan_stage(path: Path, patterns: list[str]) -> dict:
    """
    Scanne un répertoire de données (RAW / SILVER / GOLD / GoldAI) et retourne
    les métriques de volume : nb fichiers, taille totale, dernière modif, delta 24h.
    """
    if not path.exists():
        return {
            "exists": False,
            "count": 0,
            "latest": None,
            "size": 0,
            "latest_mtime": None,
            "changed_24h_count": 0,
            "changed_24h_size": 0,
        }
    files: list[Path] = []
    for pattern in patterns:
        files.extend(path.rglob(pattern))
    files = [p.resolve() for p in files if p.is_file()]
    files = list(dict.fromkeys(files))
    if not files:
        return {
            "exists": True,
            "count": 0,
            "latest": None,
            "size": 0,
            "latest_mtime": None,
            "changed_24h_count": 0,
            "changed_24h_size": 0,
        }
    file_stats = [(p, p.stat().st_size, p.stat().st_mtime) for p in files]
    latest, _latest_size, latest_mtime = max(file_stats, key=lambda x: x[2])
    total_size = sum(size for _p, size, _mt in file_stats)
    cutoff = time.time() - 24 * 3600
    changed_24h = [(p, size) for p, size, mt in file_stats if mt >= cutoff]
    changed_24h_size = sum(size for _p, size in changed_24h)
    return {
        "exists": True,
        "count": len(files),
        "latest": latest,
        "size": total_size,
        "latest_mtime": latest_mtime,
        "changed_24h_count": len(changed_24h),
        "changed_24h_size": changed_24h_size,
    }


# ---------------------------------------------------------------------------
# Phase 2 — ajoutées depuis app.py
# ---------------------------------------------------------------------------


def stage_time_range(stage_path: Path, stage_key: str) -> tuple[str, str]:
    """Retourne la période couverte (min, max) selon le format de partition."""
    if not stage_path.exists():
        return ("—", "—")
    dates: list[str] = []
    if stage_key == "raw":
        for d in stage_path.iterdir():
            if d.is_dir() and d.name.startswith("sources_"):
                dates.append(d.name.replace("sources_", ""))
    elif stage_key in {"silver", "gold"}:
        for d in stage_path.iterdir():
            if not d.is_dir():
                continue
            if d.name.startswith("date="):
                dates.append(d.name.replace("date=", ""))
            elif stage_key == "silver" and d.name.startswith("v_"):
                dates.append(d.name.replace("v_", ""))
    elif stage_key == "goldai":
        meta_path = stage_path / "metadata.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                dates = [str(x) for x in (meta.get("dates_included") or [])]
            except Exception:
                dates = []
        if not dates:
            for d in stage_path.iterdir():
                if d.is_dir() and d.name.startswith("date="):
                    dates.append(d.name.replace("date=", ""))
    elif stage_key == "ia":
        files = [f for f in stage_path.rglob("*.parquet") if f.is_file()]
        if files:
            ts = sorted([f.stat().st_mtime for f in files])
            return (
                pd.to_datetime(ts[0], unit="s").strftime("%Y-%m-%d"),
                pd.to_datetime(ts[-1], unit="s").strftime("%Y-%m-%d"),
            )
    dates = sorted([d for d in dates if re.match(r"^\d{4}-\d{2}-\d{2}$", d)])
    if not dates:
        return ("—", "—")
    return (dates[0], dates[-1])


def chrono_data(root: Path) -> pd.DataFrame:
    """Construit un DataFrame date -> stage -> nb fichiers, taille pour les graphes."""
    rows: list[dict] = []
    date_re = re.compile(r"^date=(\d{4}-\d{2}-\d{2})$")
    silver_re = re.compile(r"^v_(\d{4}-\d{2}-\d{2})$")

    def _scan_stage_dir(stage_dir: Path, stage_name: str, pattern: re.Pattern) -> None:
        if not stage_dir.exists():
            return
        for d in stage_dir.iterdir():
            if not d.is_dir():
                continue
            m = pattern.match(d.name)
            if not m:
                continue
            dt = m.group(1)
            files = [f for f in d.rglob("*.parquet") if f.is_file()]
            size = sum(f.stat().st_size for f in files)
            rows.append({"date": dt, "stage": stage_name, "count": len(files), "size": size})

    _scan_stage_dir(root / "data" / "gold", "GOLD", date_re)
    _scan_stage_dir(root / "data" / "silver", "SILVER", silver_re)
    _scan_stage_dir(root / "data" / "goldai", "GoldAI", date_re)

    if not rows:
        return pd.DataFrame(columns=["date", "stage", "count", "size"])
    return pd.DataFrame(rows)


def _canon_sentiment(value: object) -> str:
    """Normalise une valeur de sentiment brute vers une des 3 classes canoniques."""
    s = str(value or "").strip().lower()
    if s in {"positif", "positive", "pos", "4", "5"}:
        return "positif"
    if s in {"négatif", "negatif", "negative", "neg", "1", "2"}:
        return "négatif"
    if s in {"neutre", "neutral", "neu", "3"}:
        return "neutre"
    return "inconnu"


def ia_metrics_from_parquet(root: Path) -> dict | None:
    """Calcule les métriques IA depuis les Parquet GOLD/GoldAI (pour pilotage du modèle)."""
    goldai_merged = root / "data" / "goldai" / "merged_all_dates.parquet"
    gold_dir = root / "data" / "gold"
    df = None
    source_label = ""
    if goldai_merged.exists():
        try:
            df = pd.read_parquet(goldai_merged)
            source_label = "GoldAI (fusion)"
        except Exception:
            pass
    if df is None and gold_dir.exists():
        date_dirs = sorted(
            [d for d in gold_dir.iterdir() if d.is_dir() and d.name.startswith("date=")],
            reverse=True,
        )
        for d in date_dirs[:1]:
            files = list(d.rglob("*.parquet"))
            if files:
                try:
                    df = pd.read_parquet(files[0])
                    source_label = f"GOLD ({d.name})"
                    break
                except Exception:
                    continue
    if df is None or len(df) == 0:
        return None
    total = len(df)
    out: dict = {"total_articles": total, "source": source_label}
    if "sentiment" in df.columns:
        raw_sent = df["sentiment"].fillna("inconnu").astype(str).str.strip()
        canon_sent = raw_sent.map(_canon_sentiment)

        sent_norm = canon_sent.value_counts()
        sent_raw = raw_sent.value_counts()
        out["sentiment_distribution"] = sent_norm.to_dict()
        out["sentiment_pct"] = (sent_norm / total * 100).round(1).to_dict()
        out["sentiment_distribution_raw"] = sent_raw.head(12).to_dict()
        out["sentiment_alias_rows"] = int((raw_sent.str.lower() != canon_sent.str.lower()).sum())

        mapping_df = (
            pd.DataFrame({"label_brut": raw_sent, "label_canonique": canon_sent})
            .groupby(["label_brut", "label_canonique"])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        out["sentiment_mapping_table"] = mapping_df.head(20).to_dict(orient="records")

        if "label_source" in df.columns:
            src_counts = df["label_source"].fillna("lexical").value_counts()
            out["label_source_breakdown"] = {
                "lexical": int(src_counts.get("lexical", 0)),
                "ml_model": int(src_counts.get("ml_model", 0)),
                "total": total,
            }
        else:
            out["label_source_breakdown"] = {"lexical": total, "ml_model": 0, "total": total}
    if "topic_1" in df.columns:
        top = df["topic_1"].value_counts().head(15)
        out["topic_distribution"] = top.to_dict()
    if "sentiment_score" in df.columns:
        out["sentiment_score_mean"] = float(df["sentiment_score"].mean())
        out["sentiment_score_std"] = float(df["sentiment_score"].std())
    if "topic_1_confidence" in df.columns:
        out["topic_confidence_mean"] = float(df["topic_1_confidence"].mean())
    if "source" in df.columns:
        out["top_sources"] = df["source"].value_counts().head(10).to_dict()
    if "id" in df.columns:
        stable_id = (
            df["id"]
            .astype("string")
            .str.strip()
            .fillna("")
            .replace({"<NA>": "", "nan": "", "None": ""})
        )
        out["id_missing"] = int((stable_id == "").sum())
        out["id_duplicates"] = int(stable_id[stable_id != ""].duplicated().sum())
    ia_dir = root / "data" / "goldai" / "ia"
    merged_annot = ia_dir / "merged_all_dates_annotated.parquet"
    train_p = ia_dir / "train.parquet"
    val_p = ia_dir / "val.parquet"
    test_p = ia_dir / "test.parquet"
    out["mistral_dataset_reco"] = (
        "Utiliser `data/goldai/app/gold_app_input.parquet` + le dernier "
        "`data/goldai/predictions/date=*/run=*/predictions.parquet` pour les insights Mistral. "
        "Conserver `train/val/test` uniquement pour l'entraînement/évaluation."
        if (root / "data" / "goldai" / "app" / "gold_app_input.parquet").exists()
        else "Créer d'abord les branches IA (`build_gold_branches.py`) puis un run de prédiction "
        "(`run_inference_pipeline.py`) avant l'usage Mistral."
    )
    if train_p.exists() and val_p.exists() and test_p.exists():
        out["ia_splits"] = {
            "train": int(len(pd.read_parquet(train_p))),
            "val": int(len(pd.read_parquet(val_p))),
            "test": int(len(pd.read_parquet(test_p))),
        }
    else:
        out["ia_splits"] = {}
    # merged_annot référencé pour usage futur (ex. : stats annotées)
    _ = merged_annot
    return out


def enrich_profile(df: pd.DataFrame, stage: str) -> dict:
    """Profil d'enrichissement d'un DataFrame pour une étape."""
    profile: dict = {"stage": stage, "lignes": len(df), "colonnes": len(df.columns)}
    col_set = set(df.columns)
    profile["has_sentiment"] = "sentiment" in col_set
    profile["has_topic"] = "topic_1" in col_set
    profile["has_score"] = "sentiment_score" in col_set
    profile["sentiment_coverage"] = (
        float(df["sentiment"].notna().mean()) if "sentiment" in col_set else 0.0
    )
    profile["topic_coverage"] = (
        float(df["topic_1"].notna().mean()) if "topic_1" in col_set else 0.0
    )
    profile["cols_list"] = sorted(col_set)
    return profile


def _try_load(paths: list[Path]) -> pd.DataFrame | None:
    """Tente de charger le premier fichier valide (parquet ou csv) depuis une liste de chemins."""
    for p in paths:
        if not p.exists():
            continue
        try:
            if p.suffix == ".parquet":
                return pd.read_parquet(p)
            if p.suffix == ".csv":
                return pd.read_csv(p, encoding="utf-8", on_bad_lines="skip")
        except Exception:
            pass
    return None


def build_enrichment_table(root: Path) -> list[dict]:
    """Construit le tableau d'enrichissement RAW -> SILVER -> GOLD -> GoldAI -> Copie IA."""
    rows: list[dict] = []

    raw_dir = root / "data" / "raw"
    silver_dir = root / "data" / "silver"
    gold_dir = root / "data" / "gold"
    goldai_dir = root / "data" / "goldai"
    ia_dir = goldai_dir / "ia"

    raw_candidates: list[Path] = []
    if raw_dir.exists():
        for d in sorted(raw_dir.iterdir(), reverse=True):
            if d.is_dir() and "sources" in d.name:
                for f in [d / "raw_articles.csv"]:
                    if f.exists():
                        raw_candidates.append(f)
                if raw_candidates:
                    break
    df_raw = _try_load(raw_candidates)
    if df_raw is not None:
        rows.append(enrich_profile(df_raw, "1. RAW"))

    silver_candidates: list[Path] = []
    if silver_dir.exists():
        for d in sorted(silver_dir.iterdir(), reverse=True):
            if d.is_dir():
                for f in d.rglob("*.parquet"):
                    silver_candidates.append(f)
                    break
            if silver_candidates:
                break
    df_silver = _try_load(silver_candidates)
    if df_silver is not None:
        rows.append(enrich_profile(df_silver, "2. SILVER"))

    gold_candidates: list[Path] = []
    if gold_dir.exists():
        for d in sorted(
            [x for x in gold_dir.iterdir() if x.is_dir() and x.name.startswith("date=")],
            reverse=True,
        ):
            p = d / "articles.parquet"
            if p.exists():
                gold_candidates.append(p)
                break
    df_gold = _try_load(gold_candidates)
    if df_gold is not None:
        rows.append(enrich_profile(df_gold, "3. GOLD"))

    df_goldai = _try_load([goldai_dir / "merged_all_dates.parquet"])
    if df_goldai is not None:
        rows.append(enrich_profile(df_goldai, "4. GoldAI"))

    df_ia = _try_load([ia_dir / "train.parquet"])
    if df_ia is not None:
        rows.append(enrich_profile(df_ia, "5. Copie IA (train)"))

    return rows


# ---------------------------------------------------------------------------
# Phase 3 — ajoutées depuis app.py
# ---------------------------------------------------------------------------


def load_benchmark_results(root: Path) -> dict | None:
    """Charge les résultats du dernier benchmark depuis AI_BENCHMARK_RESULTS.json."""
    p = root / "docs" / "e2" / "AI_BENCHMARK_RESULTS.json"
    if not p.exists():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        normalized: dict = {}
        for key, value in raw.items():
            canon = "xlm_roberta_twitter" if key == "flaubert_multilingual" else key
            normalized[canon] = value
        return normalized
    except Exception:
        return None


_MODEL_META: dict[str, dict] = {
    "sentiment_fr": {
        "display": "Sentiment_FR (backbone fine-tuné par toi)",
        "backbone": "ac0hik/Sentiment_Analysis_French",
        "family": "FR spécialisé",
        "type": "Base",
    },
    "finetuned_local": {
        "display": "Sentiment_FR local fine-tuné (projet)",
        "backbone": "models/sentiment_fr-sentiment-finetuned",
        "family": "FR spécialisé",
        "type": "Fine-tuné local",
    },
    "bert_multilingual": {
        "display": "BERT multilingue",
        "backbone": "nlptown/bert-base-multilingual-uncased-sentiment",
        "family": "BERT",
        "type": "Base",
    },
    "xlm_roberta_twitter": {
        "display": "XLM-RoBERTa Twitter (multilingue)",
        "backbone": "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
        "family": "XLM-RoBERTa",
        "type": "Base",
    },
}


def sentiment_benchmark_diagnosis(root: Path) -> pd.DataFrame:
    """Build a concise diagnosis table from AI_BENCHMARK_RESULTS.json."""
    payload = load_benchmark_results(root)
    if not payload:
        return pd.DataFrame()
    rows = []
    for model, m in payload.items():
        if not isinstance(m, dict) or "error" in m:
            continue
        per = m.get("per_class", {}) or {}
        f1_neg = float((per.get("neg") or {}).get("f1", 0.0))
        f1_neu = float((per.get("neu") or {}).get("f1", 0.0))
        f1_pos = float((per.get("pos") or {}).get("f1", 0.0))
        rows.append(
            {
                "model_key": model,
                "model": _MODEL_META.get(model, {}).get("display", model),
                "backbone": _MODEL_META.get(model, {}).get("backbone", str(m.get("model_name", ""))),
                "family": _MODEL_META.get(model, {}).get("family", "n/a"),
                "type": _MODEL_META.get(model, {}).get("type", "n/a"),
                "accuracy": float(m.get("accuracy", 0.0)),
                "f1_macro": float(m.get("f1_macro", 0.0)),
                "latency_ms": float(m.get("avg_latency_ms", 0.0)),
                "f1_neg": f1_neg,
                "f1_neu": f1_neu,
                "f1_pos": f1_pos,
                "f1_gap_max": max(f1_neg, f1_neu, f1_pos) - min(f1_neg, f1_neu, f1_pos),
            }
        )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).sort_values(["f1_macro", "accuracy"], ascending=False)
    ordered_cols = [
        "model", "family", "type", "backbone",
        "accuracy", "f1_macro", "latency_ms",
        "f1_neg", "f1_neu", "f1_pos", "f1_gap_max", "model_key",
    ]
    return df[[c for c in ordered_cols if c in df.columns]]


def _active_inference_benchmark_key(active_model: str | None, bench_results: dict | None) -> str | None:
    """Résout la clé benchmark correspondant au modèle d'inférence actif."""
    if not bench_results:
        return None
    if active_model:
        if active_model == "camembert_pretrained":
            return None
        if "finetuned_local" in bench_results:
            return "finetuned_local"
    if "sentiment_fr" in bench_results:
        return "sentiment_fr"
    return next(iter(bench_results.keys()), None)


def go_no_go_snapshot(
    active_model: str | None,
    bench_results: dict | None,
    trained_models: list[dict],
) -> dict:
    """Compute explicit production gate from training (validation) and inference (benchmark)."""
    trained_ranked = sorted(
        trained_models,
        key=lambda m: (m.get("eval_f1_macro") or m.get("eval_f1") or 0, m.get("eval_accuracy") or 0),
        reverse=True,
    )
    best_trained = trained_ranked[0] if trained_ranked else None

    inf_key = _active_inference_benchmark_key(active_model, bench_results)
    inf = (bench_results or {}).get(inf_key, {}) if inf_key else {}
    per = inf.get("per_class", {}) if isinstance(inf, dict) else {}

    train_f1_macro = (best_trained or {}).get("eval_f1_macro")
    if train_f1_macro is None and best_trained:
        train_f1_macro = best_trained.get("eval_f1")
    train_acc = (best_trained or {}).get("eval_accuracy")
    train_f1_pos = (best_trained or {}).get("eval_f1_pos")

    inf_f1_macro = inf.get("f1_macro") if isinstance(inf, dict) else None
    inf_acc = inf.get("accuracy") if isinstance(inf, dict) else None
    inf_f1_pos = (per.get("pos") or {}).get("f1") if isinstance(per, dict) else None
    inf_latency = inf.get("avg_latency_ms") if isinstance(inf, dict) else None

    checks = [
        ("Train F1 macro >= 0.75", train_f1_macro is not None and float(train_f1_macro) >= 0.75),
        ("Train accuracy >= 0.75", train_acc is not None and float(train_acc) >= 0.75),
        ("Inference F1 macro >= 0.70", inf_f1_macro is not None and float(inf_f1_macro) >= 0.70),
        ("Inference F1 positif >= 0.65", inf_f1_pos is not None and float(inf_f1_pos) >= 0.65),
        ("Inference latence <= 260 ms", inf_latency is not None and float(inf_latency) <= 260.0),
    ]
    passed = sum(1 for _, ok in checks if ok)

    if passed == len(checks):
        status = "GO"
    elif passed >= 3:
        status = "GO avec vigilance"
    else:
        status = "NO-GO"

    return {
        "status": status,
        "checks": checks,
        "train_model_name": (best_trained or {}).get("name"),
        "train_accuracy": train_acc,
        "train_f1_macro": train_f1_macro,
        "train_f1_pos": train_f1_pos,
        "inference_model_key": inf_key,
        "inference_accuracy": inf_acc,
        "inference_f1_macro": inf_f1_macro,
        "inference_f1_pos": inf_f1_pos,
        "inference_latency_ms": inf_latency,
    }


def scan_trained_models(root: Path) -> list[dict]:
    """Scanne models/ et retourne la liste des modèles fine-tunés avec leurs métriques."""
    models_dir = root / "models"
    results = []
    if not models_dir.exists():
        return results
    for model_dir in sorted(models_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        config_file = model_dir / "config.json"
        if not config_file.exists():
            continue
        entry: dict = {"name": model_dir.name, "path": str(model_dir.relative_to(root))}
        state_file = None
        for candidate in [
            model_dir / "trainer_state.json",
            *sorted(model_dir.glob("checkpoint-*/trainer_state.json"), reverse=True),
        ]:
            if candidate.exists():
                state_file = candidate
                break
        if state_file:
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                entry["best_metric"] = state.get("best_metric")
                entry["epochs"] = state.get("epoch")
                log = state.get("log_history", [])
                last_eval = next(
                    (e for e in reversed(log) if "eval_accuracy" in e), None
                )
                if last_eval:
                    entry["eval_accuracy"] = last_eval.get("eval_accuracy")
                    entry["eval_f1"] = last_eval.get("eval_f1")
                    entry["eval_f1_macro"] = last_eval.get("eval_f1_macro")
                    entry["eval_f1_pos"] = last_eval.get("eval_f1_pos")
                    entry["eval_f1_neg"] = last_eval.get("eval_f1_neg")
                    entry["eval_f1_neu"] = last_eval.get("eval_f1_neu")
                    entry["eval_loss"] = last_eval.get("eval_loss")
                entry["log_history"] = [e for e in log if "loss" in e or "eval_loss" in e]
            except Exception:
                pass
        try:
            mtime = config_file.stat().st_mtime
            entry["trained_at"] = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass
        results.append(entry)
    return results
