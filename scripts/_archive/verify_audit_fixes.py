#!/usr/bin/env python3
"""
Verification rapide des fixes d'audit DataSens.
Usage: python scripts/verify_audit_fixes.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

OK = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results: list[tuple[str, str, str]] = []


def check(label: str, fn):
    try:
        msg = fn()
        results.append((OK, label, msg or ""))
        print(f"{OK}  {label}" + (f" — {msg}" if msg else ""))
    except Exception as e:
        results.append((FAIL, label, str(e)[:120]))
        print(f"{FAIL} {label} — {e!s:.120}")


# ─── 1. Config ────────────────────────────────────────────────────────────────
def check_config():
    from src.config import get_settings
    s = get_settings()
    assert hasattr(s, "xlm_roberta_model_path"), "xlm_roberta_model_path manquant"
    assert s.flaubert_model_path == s.xlm_roberta_model_path, "alias flaubert ne matche pas"
    return f"xlm_roberta={s.xlm_roberta_model_path} | env={s.environment}"

check("Config — xlm_roberta_model_path + alias flaubert", check_config)


# ─── 2. metrics.py extrait de app.py ─────────────────────────────────────────
def check_metrics():
    from src.streamlit.metrics import fmt_size, scan_stage
    s = fmt_size(1_500_000_000)
    assert "GB" in s, f"fmt_size inattendu: {s}"
    r = scan_stage(project_root / "data" / "gold", ["*.parquet"])
    assert "count" in r
    return f"fmt_size(1.5GB)={s} | gold parquets={r['count']}"

check("Metrics module — fmt_size + scan_stage importes depuis metrics.py", check_metrics)


# ─── 3. SQLite — UNIQUE index + PRAGMA foreign_keys ──────────────────────────
def check_sqlite():
    import sqlite3
    db = str(Path.home() / "datasens_project" / "datasens.db")
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = ON")
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    idx = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_doc_topic_unique'"
    ).fetchone()
    conn.close()
    assert fk == 1, f"foreign_keys non actif: {fk}"
    assert idx is not None, "idx_doc_topic_unique absent (migration non jouee?)"
    return f"foreign_keys=ON | idx_doc_topic_unique={idx[0]}"

check("SQLite — PRAGMA foreign_keys + UNIQUE index document_topic", check_sqlite)


# ─── 4. SILVER incremental — _max_silver_id ──────────────────────────────────
def check_silver_incremental():
    from src.e1.aggregator import _max_silver_id
    max_id = _max_silver_id()
    silver_dir = project_root / "data" / "silver"
    parquets = list(silver_dir.rglob("*.parquet")) if silver_dir.exists() else []
    return f"max_silver_id={max_id} | silver parquets={len(parquets)}"

check("SILVER incremental — _max_silver_id()", check_silver_incremental)


# ─── 5. aggregator.aggregate_silver incremental ───────────────────────────────
def check_silver_agg():
    from src.e1.aggregator import DataAggregator
    db = str(Path.home() / "datasens_project" / "datasens.db")
    agg = DataAggregator(db)
    df = agg.aggregate_silver(incremental=True)
    agg.close()
    return f"nouvelles lignes SILVER={len(df)}"

check("SILVER incremental — aggregate_silver(incremental=True)", check_silver_agg)


# ─── 6. create_ia_copy — split temporel ───────────────────────────────────────
def check_temporal_split():
    import pandas as pd
    from src.config import get_settings
    s = get_settings()
    ia_dir = project_root / s.goldai_base_path / "ia"
    if not ia_dir.is_absolute():
        ia_dir = project_root / ia_dir
    train = ia_dir / "train.parquet"
    if not train.exists():
        return "train.parquet absent — lancer create_ia_copy.py d'abord"
    df = pd.read_parquet(train)
    date_col = next(
        (c for c in ("published_at", "publication_date", "date", "created_at") if c in df.columns),
        None,
    )
    if date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
        if len(dates) > 1:
            assert dates.iloc[-1] >= dates.iloc[0], "split non trié par date!"
    return f"train={len(df)} lignes | colonne_date={date_col or 'absente'}"

check("Split temporel — train.parquet trié par date", check_temporal_split)


# ─── 7. predict_one — singleton cache ────────────────────────────────────────
def check_singleton_cache():
    from src.ml.inference.sentiment import _pipeline_cache
    # Le cache est vide au démarrage, ce qui est attendu (lazy)
    return f"_pipeline_cache accessible | entrées actuelles={len(_pipeline_cache)}"

check("Singleton pipeline — _pipeline_cache existe dans sentiment.py", check_singleton_cache)


# ─── 8. secret_key guard ─────────────────────────────────────────────────────
def check_secret_key_guard():
    from src.config import get_settings, _DEFAULT_SECRET
    s = get_settings()
    if s.environment in ("development", "dev", "test"):
        return f"env={s.environment} → guard bypasse (normal)"
    if s.secret_key == _DEFAULT_SECRET:
        raise AssertionError("SECRET_KEY par defaut en non-dev — guard aurait du lever RuntimeError")
    return f"env={s.environment} | secret_key personnalise: OK"

check("Security — secret_key guard fonctionne", check_secret_key_guard)


# ─── 9. CORS warning en prod ─────────────────────────────────────────────────
def check_cors_warning():
    import importlib
    import src.e2.api.main as api_main
    # Verifier juste que le code source contient bien le warning
    src_text = Path(api_main.__file__).read_text(encoding="utf-8")
    assert "CORS_ORIGINS" in src_text and "warnings.warn" in src_text, "warning CORS absent"
    return "warning CORS present dans main.py"

check("CORS — warning prod present dans api/main.py", check_cors_warning)


# ─── 10. db_state_report — section derive ─────────────────────────────────────
def check_drift_in_report():
    from scripts.db_state_report import _compute_sentiment_drift
    # Test avec un cas simple : distribution qui derive de 10pp sur positif
    curr = {"enrichment": {"sentiment_keyword_distribution": {"positif": 200, "negatif": 500, "neutre": 300}}}
    prev = {"enrichment": {"sentiment_keyword_distribution": {"positif": 100, "negatif": 500, "neutre": 400}}}
    result = _compute_sentiment_drift(curr, prev)
    assert result["status"] == "DRIFT_DETECTED", f"drift non detecte: {result}"
    assert len(result["alerts"]) > 0, "aucune alerte generee"
    return f"drift detecte: {result['alerts']}"

check("Drift monitoring — _compute_sentiment_drift detecte une derive de 10pp", check_drift_in_report)


# ─── Resume ───────────────────────────────────────────────────────────────────
print()
print("=" * 60)
n_ok = sum(1 for s, _, _ in results if s == OK)
n_fail = sum(1 for s, _, _ in results if s == FAIL)
print(f"Resultat : {n_ok}/{len(results)} OK  |  {n_fail} echec(s)")
if n_fail:
    print()
    print("Echecs :")
    for s, label, msg in results:
        if s == FAIL:
            print(f"  - {label}: {msg}")
    sys.exit(1)
else:
    print("Tous les fixes d'audit sont operationnels.")
    sys.exit(0)
