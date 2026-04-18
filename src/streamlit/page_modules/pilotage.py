"""
Page cockpit : onglet pilotage.
Extrait depuis src/streamlit/app.py (phase C, audit 2026-04).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
    activate_model as _activate_model,
    csv_row_count_cached as _csv_row_count_cached,
    get_active_model as _get_active_model,
    ia_history as _ia_history,
    inject_css as _inject_css,
    inject_demo_css as _inject_demo_css,
    inject_readability_css as _inject_readability_css,
    launch_api_in_new_window as _launch_api_in_new_window,
    mongo_status as _mongo_status,
    parquet_row_count_cached as _parquet_row_count_cached,
    read_parquet_cached as _read_parquet_cached,
    render_last_report as _render_last_report,
    run_command as _run_command,
)
from src.streamlit.auth_plug import (
    can_admin,
    can_write,
    get_token,
    init_session_auth,
    is_logged_in,
    render_login_form,
    render_user_and_logout,
)
from src.streamlit.metrics import (
    build_enrichment_table as _build_enrichment_table,
    chrono_data as _chrono_data,
    enrich_profile as _enrich_profile,
    go_no_go_snapshot as _go_no_go_snapshot,
    ia_metrics_from_parquet as _ia_metrics_from_parquet,
    load_benchmark_results as _load_benchmark_results,
    scan_stage as _scan_stage,
    scan_trained_models as _scan_trained_models,
    stage_time_range as _stage_time_range,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def render(ctx: PageContext) -> None:
    project_root = ctx.project_root
    PROJECT_ROOT = ctx.project_root
    settings = ctx.settings
    api_base = ctx.api_base
    backend_ok = ctx.backend_ok
    ux_mode = ctx.ux_mode
    show_advanced = ctx.show_advanced
    history_mode = ctx.history_mode
    raw_dir = ctx.raw_dir
    silver_dir = ctx.silver_dir
    gold_dir = ctx.gold_dir
    goldai_dir = ctx.goldai_dir
    ia_dir = ctx.ia_dir

    if show_advanced:
        st.caption(
            "Mode **Expert** actif (sélecteur *Ergonomie cockpit* dans la barre latérale) : "
            "les blocs techniques avancés sont affichés."
        )
    else:
        st.caption(
            "Mode **Focus** (par défaut). Passez sur *Ergonomie cockpit → Expert* "
            "dans la barre latérale pour afficher les blocs techniques avancés."
        )

    def _resolve_db_path() -> str:
        db = os.getenv("DB_PATH")
        if db and Path(db).exists():
            return db
        default = str(Path.home() / "datasens_project" / "datasens.db")
        if Path(default).exists():
            return default
        return (
            str(PROJECT_ROOT / "datasens.db")
            if (PROJECT_ROOT / "datasens.db").exists()
            else default
        )

    db_path = _resolve_db_path()

    st.info(
        "**Centre d'actions du cockpit.** Les chiffres de volumétrie sont dans "
        "**Vue d'ensemble** ; la qualité et l'historique sont dans **Monitoring**. "
        "Ici, on **lance** le pipeline, la fusion, la copie IA, l'API et les backups."
    )
    # ── RBAC : seul un role writer/deleter/admin peut executer les pipelines ─
    may_run = can_write()
    may_admin = can_admin()
    if not may_run:
        st.warning(
            "Role `reader` : les actions d'execution sont verrouillees. "
            "Seuls les roles `writer`, `deleter` ou `admin` peuvent lancer les pipelines, backups et copies IA."
        )
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button(
            "Pipeline E1", type="primary", use_container_width=True, disabled=not may_run
        ):
            env = {"FORCE_ZZDB_REIMPORT": "false"}
            _run_command("pipeline", [sys.executable, "main.py"], extra_env=env)
    with b2:
        if st.button(
            "Fusion GoldAI", type="primary", use_container_width=True, disabled=not may_run
        ):
            _run_command("goldai", [sys.executable, "scripts/merge_parquet_goldai.py"])
    with b3:
        copie_ia_topics = st.checkbox(
            "Copie IA (experimental): filtrer finance+politique+météo (peut biaiser l'entrainement)",
            value=False,
            key="copie_ia_topics",
        )
        if copie_ia_topics:
            st.warning(
                "Mode slice metier active: utile pour test rapide, mais a eviter pour le modele principal. "
                "Bonne pratique: entrainer global, puis filtrer au niveau des insights."
            )
        if st.button(
            "Copie IA", type="primary", use_container_width=True, disabled=not may_run
        ):
            cmd = [sys.executable, "scripts/create_ia_copy.py"]
            if copie_ia_topics:
                cmd += ["--topics", "finance,politique,meteo"]
            _run_command("copie IA", cmd)

    # Rapport d'exécution (affiché juste après les boutons principaux)
    _render_last_report("pilotage")

    b4, b5, _ = st.columns(3)
    with b4:
        if st.button(
            "Lancer API E2",
            use_container_width=True,
            disabled=not may_admin,
            help=("Role admin requis." if not may_admin else None),
        ):
            _launch_api_in_new_window()
    with b5:
        if st.button(
            "Backup MongoDB",
            use_container_width=True,
            disabled=not may_admin,
            help=(
                "Role admin requis."
                if not may_admin
                else "Parquet vers MongoDB GridFS. Lancer start_mongo.bat avant (Docker)."
            ),
        ):
            _run_command(
                "backup",
                [sys.executable, "scripts/backup_parquet_to_mongo.py"],
                extra_env={"MONGO_STORE_PARQUET": "true"},
            )

    with st.expander("Injecter un CSV (à la demande)", expanded=False):
        st.caption(
            "Le CSV parcourt le pipeline E1 complet (RAW → SILVER → GOLD). "
            "Colonnes: title, content (obligatoires), url, published_at (optionnels)"
        )
        csv_file = st.file_uploader("Fichier CSV", type=["csv"], key="inject_csv")
        source_name = st.text_input("Nom de la source", value="csv_inject", key="inject_source")
        if st.button(
            "Injecter dans le pipeline E1",
            disabled=not may_run,
            help=("Role writer/admin requis." if not may_run else None),
        ):
            if csv_file:
                import tempfile
                with tempfile.NamedTemporaryFile(
                    suffix=".csv", delete=False, mode="wb"
                ) as tmp:
                    tmp.write(csv_file.getvalue())
                    tmp_path = tmp.name
                try:
                    _run_command(
                        "inject CSV (pipeline complet)",
                        [
                            sys.executable,
                            "main.py",
                            "--inject-csv",
                            tmp_path,
                            "--source-name",
                            source_name or "csv_inject",
                        ],
                    )
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
            else:
                st.warning("Déposez un fichier CSV.")

    st.caption("Fine-tuning : améliore le modèle IA avec les données GoldAI")

    # Auto-suggestion du meilleur backbone basée sur le benchmark
    _bench_for_ft = _load_benchmark_results(PROJECT_ROOT)
    _best_backbone_suggestion = "sentiment_fr"
    if _bench_for_ft:
        _pretrained_only = {
            k: v for k, v in _bench_for_ft.items()
            if k != "finetuned_local" and "error" not in v
        }
        _backbone_map = {
            "bert_multilingual": "bert_multilingual",
            "sentiment_fr": "sentiment_fr",
            "xlm_roberta_twitter": "flaubert",
            "flaubert_multilingual": "flaubert",
        }
        if _pretrained_only:
            _best_bench_key = max(_pretrained_only, key=lambda k: _pretrained_only[k].get("accuracy", 0))
            _best_backbone_suggestion = _backbone_map.get(_best_bench_key, "sentiment_fr")
            _best_acc = _pretrained_only[_best_bench_key].get("accuracy", 0)
            f1_best = _pretrained_only[_best_bench_key].get("f1_macro", 0)
            st.info(
                f"**Recommandation** : fine-tuner **{_best_bench_key}** "
                f"(F1 macro {f1_best:.1%}). Évitez CamemBERT distil (le plus faible). "
                f"Un bon pré-entraîné donne un meilleur fine-tuné."
            )

    ft_col1, ft_col2, ft_col3 = st.columns(3)
    with ft_col1:
        _backbone_choices = ["sentiment_fr", "bert_multilingual", "camembert", "flaubert"]
        _default_idx = _backbone_choices.index(_best_backbone_suggestion) if _best_backbone_suggestion in _backbone_choices else 0
        ft_backbone = st.selectbox(
            "Backbone à entraîner",
            _backbone_choices,
            index=_default_idx,
            format_func=lambda x: {
                "camembert": "CamemBERT distil (léger, CPU rapide)",
                "bert_multilingual": "BERT multilingue 5★ (nlptown) — pas CamemBERT",
                "sentiment_fr": "sentiment_fr (RECOMMANDÉ — meilleur bench) ★",
                "flaubert": "FlauBERT base uncased (FR)",
            }.get(x, x),
            key="ft_backbone",
            help="sentiment_fr est le meilleur pré-entraîné sur le benchmark. Fine-tuner le meilleur backbone donne le meilleur résultat final.",
        )
    with ft_col2:
        ft_mode = st.selectbox(
            "Mode",
            ["quick", "full"],
            format_func=lambda x: "Quick (1 epoch, ~3000 ex.)" if x == "quick" else "Full (3 epochs, toutes données)",
            key="ft_mode",
        )
    with ft_col3:
        ft_epochs = 1 if ft_mode == "quick" else 3
        ft_max_train = 3000 if ft_mode == "quick" else None
        ft_max_val = 800 if ft_mode == "quick" else None
        st.caption(f"Epochs: {ft_epochs}")
        if ft_max_train:
            st.caption(f"Max train: {ft_max_train} · Max val: {ft_max_val}")

    ft_topics = st.checkbox(
        "Filtrer finance + politique + météo uniquement",
        value=False,
        key="ft_topics_filter",
        help="Entraîne sur les articles avec topic_1 ou topic_2 = finance/politique/meteo. Meilleure restitution veille.",
    )
    ft_pos_ratio = st.slider(
        "Recalibrage classe positif (train)",
        min_value=0.0,
        max_value=0.40,
        value=0.25,
        step=0.01,
        help="0 = off. Augmente la part de la classe positif dans le train via sur-échantillonnage contrôlé.",
        key="ft_target_pos_ratio",
    )
    ft_pos_mult = st.slider(
        "Limite sur-échantillonnage positif (x)",
        min_value=1.0,
        max_value=6.0,
        value=3.0,
        step=0.5,
        help="Garde-fou pour éviter de dupliquer excessivement la classe positif.",
        key="ft_pos_oversample_multiplier",
    )

    b6, b7, _ = st.columns(3)
    with b6:
        if st.button(
            "Lancer le fine-tuning",
            type="primary",
            use_container_width=True,
            disabled=not may_admin,
            help=(
                "Role admin requis."
                if not may_admin
                else "Entraîne le backbone choisi sur train.parquet (Copie IA)."
            ),
        ):
            cmd = [
                sys.executable,
                "scripts/finetune_sentiment.py",
                "--model", ft_backbone,
                "--epochs", str(ft_epochs),
            ]
            if ft_max_train:
                cmd += ["--max-train-samples", str(ft_max_train)]
            if ft_max_val:
                cmd += ["--max-val-samples", str(ft_max_val)]
            if ft_topics:
                cmd += ["--topics", "finance,politique,meteo"]
            if ft_pos_ratio > 0:
                cmd += ["--target-pos-ratio", str(ft_pos_ratio)]
                cmd += ["--pos-oversample-max-multiplier", str(ft_pos_mult)]
            _run_command("finetune", cmd)
    with b7:
        if st.button(
            "Évaluer modèle fine-tuné",
            use_container_width=True,
            disabled=not may_run,
            help="Calcule accuracy/F1 sur val.parquet (modèle fine-tuné)",
        ):
            _run_command(
                "eval", [sys.executable, "scripts/finetune_sentiment.py", "--eval-only"]
            )
    finetuned_path = getattr(settings, "sentiment_finetuned_model_path", None)
    if finetuned_path:
        st.caption(f"Modèle fine-tuné actif : `{finetuned_path}`")
    else:
        _expected_path = f"models/{ft_backbone}-sentiment-finetuned" if "ft_backbone" in dir() else "models/sentiment_fr-sentiment-finetuned"
        st.caption(
            f"Après fine-tuning, activez le modèle dans **Modèles & Sélection** "
            f"ou ajoutez dans `.env` : `SENTIMENT_FINETUNED_MODEL_PATH={_expected_path}`"
        )

    with st.expander("Paramètres & détails", expanded=False):
        force_reimport = st.checkbox("FORCE_ZZDB_REIMPORT (zzdb_csv)", value=False)
        env = {"FORCE_ZZDB_REIMPORT": "true" if force_reimport else "false"}
        if st.button("Pipeline E1 (avec params)", disabled=not may_run):
            _run_command("pipeline", [sys.executable, "main.py"], extra_env=env)
        st.caption(f"Base : {db_path}")
        if Path(db_path).exists():
            try:
                import sqlite3

                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = []
                for r in cur.fetchall():
                    if r[0] != "sqlite_sequence":
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM [{r[0]}]")
                            tables.append((r[0], cur.fetchone()[0]))
                        except Exception:
                            pass
                conn.close()
                st.caption("Tables : " + ", ".join(f"{t}={c}" for t, c in tables[:8]))
            except Exception:
                pass
        if st.button("Veille IA", disabled=not may_run):
            _run_command("veille", [sys.executable, "scripts/veille_digest.py"])
        if st.button("Benchmark IA (rapide 200 ex.)", disabled=not may_run):
            _run_command("benchmark", [sys.executable, "scripts/ai_benchmark.py", "--max-samples", "200"])
        if st.button("Benchmark IA (complet)", disabled=not may_run):
            _run_command("benchmark", [sys.executable, "scripts/ai_benchmark.py"])
        if st.button("Lister Parquet MongoDB", disabled=not may_run):
            _run_command("mongo", [sys.executable, "scripts/list_mongo_parquet.py"])
        st.divider()
        st.caption("Après fine-tuning, le chemin du modèle :")
        st.code("SENTIMENT_FINETUNED_MODEL_PATH=models/sentiment_fr-sentiment-finetuned")
