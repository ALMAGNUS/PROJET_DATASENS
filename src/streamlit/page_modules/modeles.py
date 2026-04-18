"""
Page cockpit : onglet modeles.
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

from src.observability.lineage_service import LineageService
from src.streamlit._cockpit_helpers import (
    PageContext,
    activate_model as _activate_model,
    csv_row_count_cached as _csv_row_count_cached,
    get_active_model as _get_active_model,
    ia_history as _ia_history,
    inject_css as _inject_css,
    inject_demo_css as _inject_demo_css,
    inject_readability_css as _inject_readability_css,
    latest_db_state_reports as _latest_db_state_reports,
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
    fmt_size as _fmt_size,
    go_no_go_snapshot as _go_no_go_snapshot,
    ia_metrics_from_parquet as _ia_metrics_from_parquet,
    load_benchmark_results as _load_benchmark_results,
    scan_stage as _scan_stage,
    scan_trained_models as _scan_trained_models,
    sentiment_benchmark_diagnosis as _sentiment_benchmark_diagnosis,
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

    st.markdown("### Modèles IA — Benchmark, Fine-tuning & Sélection")
    st.caption(
        "Ici vous comparez tous les modèles (pré-entraînés et fine-tunés sur vos données), "
        "choisissez le meilleur, et l'activez pour la production (API sentiment + Mistral)."
    )

    active_model = _get_active_model(PROJECT_ROOT)
    if active_model:
        st.success(f"Modèle actif en production : `{active_model}`")
    else:
        st.warning(
            "Aucun modèle fine-tuné activé. Le modèle par défaut (`sentiment_fr`) est utilisé. "
            "Activez un modèle fine-tuné ci-dessous pour améliorer la précision sur vos données."
        )

    # Vision claire pour l'utilisateur: entraînement (validation) vs inférence (production)
    bench_results_modeles = _load_benchmark_results(PROJECT_ROOT)
    trained_models_modeles = _scan_trained_models(PROJECT_ROOT)
    gate = _go_no_go_snapshot(active_model, bench_results_modeles, trained_models_modeles)

    st.divider()
    st.subheader("Lecture métier : entraînement vs inférence")
    st.caption(
        "Entraînement = qualité d'apprentissage interne (train/validation). "
        "Inférence = qualité réelle en production (benchmark/test + latence)."
    )
    explain_rows = [
        {
            "Étape": "Entraînement (offline)",
            "Objectif": "Apprendre le modèle",
            "Mesures clés": "eval_accuracy, eval_f1_macro, eval_f1_pos, eval_loss",
            "Source": "trainer_state.json / runs fine-tuning",
        },
        {
            "Étape": "Inférence (online)",
            "Objectif": "Prédire vite et bien pour l'utilisateur",
            "Mesures clés": "accuracy, f1_macro, f1_pos, latency_ms",
            "Source": "AI_BENCHMARK_RESULTS.json + API /ai/predict",
        },
    ]
    st.dataframe(pd.DataFrame(explain_rows), use_container_width=True, hide_index=True)

    c_train, c_inf, c_gate = st.columns(3)
    with c_train:
        st.markdown("**Entraînement (validation)**")
        st.metric("Modèle entraîné de référence", gate.get("train_model_name") or "n/a")
        tr_acc = gate.get("train_accuracy")
        tr_f1 = gate.get("train_f1_macro")
        tr_pos = gate.get("train_f1_pos")
        st.caption(
            f"Acc={float(tr_acc):.3f} | F1_macro={float(tr_f1):.3f} | F1_pos={float(tr_pos):.3f}"
            if tr_acc is not None and tr_f1 is not None and tr_pos is not None
            else "Métriques entraînement incomplètes."
        )
    with c_inf:
        st.markdown("**Inférence (production/test)**")
        st.metric("Modèle évalué en inférence", gate.get("inference_model_key") or "n/a")
        inf_acc = gate.get("inference_accuracy")
        inf_f1 = gate.get("inference_f1_macro")
        inf_pos = gate.get("inference_f1_pos")
        inf_lat = gate.get("inference_latency_ms")
        st.caption(
            f"Acc={float(inf_acc):.3f} | F1_macro={float(inf_f1):.3f} | "
            f"F1_pos={float(inf_pos):.3f} | Lat={float(inf_lat):.1f} ms"
            if inf_acc is not None and inf_f1 is not None and inf_pos is not None and inf_lat is not None
            else "Métriques inférence incomplètes."
        )
    with c_gate:
        st.markdown("**Décision Go/No-Go prod**")
        gate_status = str(gate.get("status", "NO-GO"))
        if gate_status == "GO":
            st.success("GO")
        elif gate_status == "GO avec vigilance":
            st.warning("GO avec vigilance")
        else:
            st.error("NO-GO")

    with st.expander("Règles de décision (explicites)", expanded=False):
        checks = gate.get("checks", [])
        for label, ok in checks:
            st.markdown(f"- {'✅' if ok else '❌'} {label}")

    # ── Section 0 : Évolution des datasets ─────────────────────────────────────
    st.divider()
    st.subheader("0. Évolution du volume de données")
    st.caption(
        "Plus vous collectez, plus le modèle s'améliore. "
        "Cette courbe montre la croissance cumulative des articles labellisés dans GoldAI."
    )

    df_hist = _ia_history(PROJECT_ROOT)
    if not df_hist.empty:
        col_h1, col_h2, col_h3 = st.columns(3)
        ia_dir_path = PROJECT_ROOT / "data" / "goldai" / "ia"
        n_train = len(pd.read_parquet(ia_dir_path / "train.parquet")) if (ia_dir_path / "train.parquet").exists() else 0
        n_val = len(pd.read_parquet(ia_dir_path / "val.parquet")) if (ia_dir_path / "val.parquet").exists() else 0
        n_test = len(pd.read_parquet(ia_dir_path / "test.parquet")) if (ia_dir_path / "test.parquet").exists() else 0
        col_h1.metric("Train", f"{n_train:,}")
        col_h2.metric("Validation", f"{n_val:,}")
        col_h3.metric("Test", f"{n_test:,}")
        st.line_chart(df_hist.set_index("date")["lignes_cumulées"], use_container_width=True)
        st.caption("Données collectées par date → plus de données = meilleur fine-tuning.")
    else:
        st.info("Aucun historique disponible. Lancez le pipeline et la fusion GoldAI.")

    # Évolution des runs d'entraînement (si plusieurs modèles fine-tunés)
    trained_models_hist = _scan_trained_models(PROJECT_ROOT)
    if len(trained_models_hist) >= 1:
        st.caption("**Historique des runs de fine-tuning**")
        run_rows = []
        for m in trained_models_hist:
            if m.get("eval_accuracy"):
                run_rows.append({
                    "Run": m["name"],
                    "Date": m.get("trained_at", "—"),
                    "Accuracy": round(m["eval_accuracy"], 4),
                    "F1": round(m.get("eval_f1") or 0, 4),
                    "Epochs": m.get("epochs", "—"),
                })
        if run_rows:
            df_runs = pd.DataFrame(run_rows)
            st.dataframe(df_runs, use_container_width=True, hide_index=True)
            if len(run_rows) > 1:
                st.line_chart(df_runs.set_index("Run")[["Accuracy", "F1"]], use_container_width=True)

    # ── Section 1 : Benchmark ───────────────────────────────────────────────────
    st.divider()
    st.subheader("1. Benchmark — Modèles pré-entraînés")
    st.caption(
        "Compare les modèles HuggingFace sur votre dataset de test (data/goldai/ia/test.parquet). "
        "**Relancez le benchmark après chaque grosse collecte** car les métriques évoluent avec les données."
    )

    bench_results = _load_benchmark_results(PROJECT_ROOT)
    _backbone_from_bench_key = {
        "bert_multilingual": "bert_multilingual",
        "sentiment_fr": "sentiment_fr",
        "xlm_roberta_twitter": "flaubert",
        "flaubert_multilingual": "flaubert",
    }
    _best_pretrained_backbone = "sentiment_fr"
    if bench_results:
        rows_b = []
        for key, r in bench_results.items():
            if "error" in r:
                continue
            pc = r.get("per_class", {})
            f1_pos_val = pc.get("pos", {}).get("f1", pc.get("positif", {}).get("f1", 0))
            rows_b.append({
                "Modèle": key,
                "Accuracy": f"{r.get('accuracy', 0):.1%}",
                "F1 macro": f"{r.get('f1_macro', 0):.3f}",
                "F1 positif": f"{f1_pos_val:.3f}",
                "F1 négatif": f"{pc.get('neg', {}).get('f1', 0):.3f}",
                "Latence (ms)": f"{r.get('avg_latency_ms', 0):.0f}",
            })
        if rows_b:
            # Trier par accuracy décroissante
            rows_b_sorted = sorted(
                rows_b,
                key=lambda x: bench_results.get(x["Modèle"], {}).get("accuracy", 0),
                reverse=True,
            )
            # Ajouter médaille
            for i, row in enumerate(rows_b_sorted):
                row["Rang"] = ["🥇", "🥈", "🥉", "4"][min(i, 3)]
            df_bench = pd.DataFrame(rows_b_sorted)[["Rang", "Modèle", "Accuracy", "F1 macro", "F1 positif", "F1 négatif", "Latence (ms)"]]
            st.dataframe(df_bench, use_container_width=True, hide_index=True)

            best_key = rows_b_sorted[0]["Modèle"]
            best_acc = bench_results.get(best_key, {}).get("accuracy", 0)

            # Exclure finetuned_local pour suggérer un backbone pré-entraîné
            pretrained_sorted = [r for r in rows_b_sorted if r["Modèle"] != "finetuned_local"]
            if pretrained_sorted:
                _best_pretrained_backbone = _backbone_from_bench_key.get(
                    pretrained_sorted[0]["Modèle"], "sentiment_fr"
                )
                best_pt_key = pretrained_sorted[0]["Modèle"]
                best_pt_acc = bench_results.get(best_pt_key, {}).get("accuracy", 0)

                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.success(
                        f"**Meilleur pré-entraîné : {best_pt_key}** ({best_pt_acc:.1%} accuracy) "
                        f"→ Recommandé comme backbone pour le fine-tuning."
                    )
                with col_btn:
                    _may_admin = can_admin()
                    if st.button(
                        f"Fine-tuner {_best_pretrained_backbone} maintenant",
                        use_container_width=True,
                        type="primary",
                        disabled=not _may_admin,
                        help=(
                            "Role admin requis."
                            if not _may_admin
                            else f"Lance le fine-tuning du meilleur backbone ({best_pt_key}) avec class weights"
                        ),
                    ):
                        _run_command(
                            "finetune",
                            [sys.executable, "scripts/finetune_sentiment.py",
                             "--model", _best_pretrained_backbone, "--epochs", "3",
                             "--target-pos-ratio", "0.25",
                             "--pos-oversample-max-multiplier", "3.0"],
                        )
                        st.info("Fine-tuning lancé. Suivez la progression dans **Pilotage**.")
    else:
        st.info(
            "Aucun résultat de benchmark disponible. "
            "Lancez le benchmark ci-dessous pour comparer les modèles et obtenir une recommandation automatique."
        )

    _may_run = can_write()
    if not _may_run:
        st.info(
            "Role `reader` : les benchmarks et l'activation de modele sont en lecture seule. "
            "Seuls `writer` ou `admin` peuvent declencher un run."
        )
    col_bench1, col_bench2 = st.columns(2)
    with col_bench1:
        if st.button(
            "Lancer Benchmark (rapide 200 ex.)",
            use_container_width=True,
            disabled=not _may_run,
            help="Compare tous les modèles sur 200 exemples (~5 min)",
        ):
            _run_command(
                "benchmark",
                [sys.executable, "scripts/ai_benchmark.py", "--max-samples", "200"],
            )
    with col_bench2:
        if st.button(
            "Lancer Benchmark (complet)",
            use_container_width=True,
            disabled=not _may_run,
            help="Compare sur toutes les données — résultats définitifs",
        ):
            _run_command("benchmark", [sys.executable, "scripts/ai_benchmark.py"])

    _render_last_report("monitoring")

    # ── Section 2 : Modèles fine-tunés ─────────────────────────────────────────
    st.divider()
    st.subheader("2. Modèles fine-tunés — Entraînés sur vos données")
    st.caption(
        "Chaque fine-tuning produit un modèle adapté à vos articles (politique / économie FR). "
        "Plus il y a de données collectées, plus le modèle sera précis."
    )

    trained_models = _scan_trained_models(PROJECT_ROOT)
    if trained_models:
        rows_t: list[dict] = []
        for m in trained_models:
            # Certains anciens runs peuvent avoir eval_f1_macro=None mais eval_f1 défini.
            raw_f1_macro = m.get("eval_f1_macro")
            fallback_f1 = m.get("eval_f1")
            f1_macro_display_val = raw_f1_macro if raw_f1_macro is not None else fallback_f1
            f1_pos_ft = m.get("eval_f1_pos")
            rows_t.append(
                {
                    "Modèle": m["name"],
                    "Accuracy val.": f"{m['eval_accuracy']:.1%}" if m.get("eval_accuracy") else "—",
                    "F1 macro": f"{f1_macro_display_val:.3f}" if f1_macro_display_val is not None else "—",
                    "F1 positif": f"{f1_pos_ft:.3f}" if f1_pos_ft is not None else "⚠ non calculé",
                    "Epochs": f"{m.get('epochs', '—')}",
                    "Entraîné le": m.get("trained_at", "—"),
                    "Chemin": m["path"],
                }
            )
        df_trained = pd.DataFrame(rows_t)
        st.dataframe(df_trained.drop(columns=["Chemin"]), use_container_width=True, hide_index=True)
        if any(r.get("F1 positif", "").startswith("⚠") for r in rows_t):
            st.warning(
                "**F1 positif non calculé** pour certains modèles → anciens runs sans class weights. "
                "Re-lancez le fine-tuning avec le nouveau script pour corriger (class weights automatiques activés)."
            )

        # Courbe de loss pour le modèle sélectionné
        selected_model_name = st.selectbox(
            "Voir la courbe d'apprentissage",
            [m["name"] for m in trained_models],
            key="sel_loss_curve",
        )
        selected_model = next((m for m in trained_models if m["name"] == selected_model_name), None)
        if selected_model and selected_model.get("log_history"):
            log = selected_model["log_history"]
            train_steps = [e["step"] for e in log if "loss" in e]
            train_loss = [e["loss"] for e in log if "loss" in e]
            eval_entries = [e for e in log if "eval_loss" in e]
            if train_steps:
                df_loss = pd.DataFrame({"step": train_steps, "Train Loss": train_loss})
                df_loss = df_loss.set_index("step")
                if eval_entries:
                    for ev in eval_entries:
                        step = ev.get("step", train_steps[-1])
                        df_loss.loc[step, "Val Loss"] = ev["eval_loss"]
                st.line_chart(df_loss, use_container_width=True)
    else:
        st.info(
            "Aucun modèle fine-tuné trouvé dans `models/`. "
            "Allez dans **Pilotage** → choisissez un backbone → **Lancer le fine-tuning**."
        )

    # ── Section 3 : Sélection & Activation ─────────────────────────────────────
    st.divider()
    st.subheader("3. Sélection & Activation pour la production")
    st.caption(
        "Activez le meilleur modèle ici. Il sera utilisé automatiquement par l'API `/ai/predict` "
        "et pour les analyses Mistral (insights clients politique / économie)."
    )

    all_model_options: dict[str, str] = {
        "sentiment_fr (pré-entraîné — défaut)": "",
        "camembert (pré-entraîné — DistilCamemBERT)": "camembert_pretrained",
    }
    for m in trained_models:
        label = (
            f"{m['name']} — Accuracy {m['eval_accuracy']:.1%}" if m.get("eval_accuracy")
            else m["name"]
        )
        all_model_options[label] = m["path"]

    current_label = next(
        (lbl for lbl, path in all_model_options.items() if path == (active_model or "")),
        list(all_model_options.keys())[0],
    )
    chosen_label = st.selectbox(
        "Modèle à activer pour la production",
        list(all_model_options.keys()),
        index=list(all_model_options.keys()).index(current_label),
        key="activate_model_select",
    )
    chosen_path = all_model_options[chosen_label]

    _may_admin_activate = can_admin()
    col_act1, col_act2 = st.columns(2)
    with col_act1:
        if st.button(
            "Activer ce modèle",
            type="primary",
            use_container_width=True,
            disabled=not _may_admin_activate,
            help=("Role admin requis (ecriture de .env)." if not _may_admin_activate else None),
        ):
            if chosen_path:
                ok = _activate_model(PROJECT_ROOT, chosen_path)
                if ok:
                    st.success(
                        f"Modèle activé : `{chosen_path}`\n\n"
                        "Redémarrez l'API E2 pour prendre en compte le changement."
                    )
                    st.rerun()
                else:
                    st.error("Impossible d'écrire dans .env — vérifiez les permissions.")
            else:
                ok = _activate_model(PROJECT_ROOT, "")
                if ok:
                    st.success("Modèle par défaut (`sentiment_fr`) restauré.")
                    st.rerun()
    with col_act2:
        if trained_models and st.button(
            "Activer le meilleur automatiquement",
            use_container_width=True,
            disabled=not _may_admin_activate,
            help=(
                "Role admin requis."
                if not _may_admin_activate
                else "Active le modèle fine-tuné avec la meilleure accuracy"
            ),
        ):
            best = max(trained_models, key=lambda m: m.get("eval_accuracy") or 0)
            if best.get("eval_accuracy"):
                ok = _activate_model(PROJECT_ROOT, best["path"])
                if ok:
                    st.success(f"Meilleur modèle activé : `{best['name']}` ({best['eval_accuracy']:.1%})")
                    st.rerun()

    # ── Section 4 : Dataset IA prêt pour Mistral ───────────────────────────────
    st.divider()
    st.subheader("4. Dataset IA — Prêt pour Mistral")
    st.caption(
        "Ce dataset (labellisé sentiment + topics) est ce que vous vendez à vos clients : "
        "il alimente l'assistant Mistral pour les analyses politique / économie."
    )

    ia_dir = PROJECT_ROOT / "data" / "goldai" / "ia"
    splits_info = []
    for split in ["train", "val", "test"]:
        p = ia_dir / f"{split}.parquet"
        if p.exists():
            try:
                n = len(pd.read_parquet(p))
                splits_info.append({"Split": split, "Lignes": n, "Chemin": str(p.relative_to(PROJECT_ROOT))})
            except Exception:
                splits_info.append({"Split": split, "Lignes": "?", "Chemin": str(p.relative_to(PROJECT_ROOT))})

    if splits_info:
        df_splits = pd.DataFrame(splits_info)
        total = sum(r["Lignes"] for r in splits_info if isinstance(r["Lignes"], int))
        c1, c2, c3 = st.columns(3)
        c1.metric("Total exemples étiquetés", f"{total:,}")
        c2.metric("Modèle actif (inférence)", active_model.split("/")[-1] if active_model else "sentiment_fr")
        c3.metric("Splits disponibles", len(splits_info))
        st.dataframe(df_splits, use_container_width=True, hide_index=True)
        st.caption(
            "Pour Mistral : le dataset `data/goldai/ia/` contient `sentiment` (positif/négatif/neutre) "
            "+ `topic_1/topic_2` pour chaque article. L'assistant peut s'en servir pour les insights clients."
        )
    else:
        st.info(
            "Dataset IA absent. Lancez : **Pilotage** → Copie IA → Fine-tuning → revenir ici."
        )
