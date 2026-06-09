"""
Page cockpit : onglet modeles.
Refonte 2026-06 : carte « modèle en production » + 1 tableau comparatif unifié,
outillage MLOps (benchmark, fine-tuning, activation, drift) replié dans des expanders.
Noms de modèles unifiés (datasens-sentiment-fr partout).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import SENTIMENT_MODEL_DISPLAY_NAME, canonical_sentiment_label
from src.streamlit._cockpit_helpers import (
    PageContext,
)
from src.streamlit._cockpit_helpers import (
    activate_model as _activate_model,
)
from src.streamlit._cockpit_helpers import (
    get_active_model as _get_active_model,
)
from src.streamlit._cockpit_helpers import (
    render_last_report as _render_last_report,
)
from src.streamlit._cockpit_helpers import (
    run_command as _run_command,
)
from src.streamlit.auth_plug import (
    can_admin,
    can_write,
    get_token,
)
from src.streamlit.metrics import (
    go_no_go_snapshot as _go_no_go_snapshot,
)
from src.streamlit.metrics import (
    load_benchmark_results as _load_benchmark_results,
)
from src.streamlit.metrics import (
    scan_trained_models as _scan_trained_models,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# ── Noms d'affichage unifiés ────────────────────────────────────────────────
# Une seule source de vérité : notre fine-tune = datasens-sentiment-fr partout,
# les modèles de base gardent un nom lisible (et non leur clé technique).
_DISPLAY_NAMES: dict[str, str] = {
    "finetuned_local": SENTIMENT_MODEL_DISPLAY_NAME,
    "sentiment_fr": "ac0hik Sentiment FR",
    "bert_multilingual": "BERT multilingue (nlptown)",
    "xlm_roberta_twitter": "XLM-RoBERTa Twitter",
    "flaubert_multilingual": "XLM-RoBERTa Twitter",
    "camembert_pretrained": "CamemBERT (DistilCamemBERT)",
}


def _bench_display_name(key: str) -> str:
    return _DISPLAY_NAMES.get(key, key)


def _load_eval_metrics(root: Path) -> dict:
    """Métriques d'inférence complètes (precision/recall/specificity/FPR/ROC-AUC)."""
    p = root / "docs" / "e2" / "EVAL_CLASSIFICATION_METRICS.json"
    if not p.exists():
        return {}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _render_finetune_controls(ctx: PageContext) -> None:
    """Lancement fine-tuning / eval — regroupé ici, plus dans Pilotage."""
    PROJECT_ROOT = ctx.project_root
    settings = ctx.settings
    may_run = can_write()
    may_admin = can_admin()

    st.caption("Backbone + hyperparamètres. Lancez d'abord **Copie IA** (Pilotage) si train.parquet est absent.")

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
            _best_bench_key = max(
                _pretrained_only, key=lambda k: _pretrained_only[k].get("accuracy", 0)
            )
            _best_backbone_suggestion = _backbone_map.get(_best_bench_key, "sentiment_fr")
            f1_best = _pretrained_only[_best_bench_key].get("f1_macro", 0)
            st.info(
                f"**Recommandation** : fine-tuner **{_bench_display_name(_best_bench_key)}** "
                f"(F1 macro {f1_best:.1%})."
            )

    ft_col1, ft_col2, ft_col3 = st.columns(3)
    with ft_col1:
        _backbone_choices = ["sentiment_fr", "bert_multilingual", "camembert", "flaubert"]
        _default_idx = (
            _backbone_choices.index(_best_backbone_suggestion)
            if _best_backbone_suggestion in _backbone_choices
            else 0
        )
        ft_backbone = st.selectbox(
            "Backbone à entraîner",
            _backbone_choices,
            index=_default_idx,
            format_func=lambda x: {
                "camembert": "CamemBERT distil (léger, CPU rapide)",
                "bert_multilingual": "BERT multilingue 5★ (nlptown)",
                "sentiment_fr": "sentiment_fr (RECOMMANDÉ) ★",
                "flaubert": "FlauBERT base uncased (FR)",
            }.get(x, x),
            key="ft_backbone_models",
        )
    with ft_col2:
        ft_mode = st.selectbox(
            "Mode",
            ["quick", "full"],
            format_func=lambda x: "Quick (1 epoch, ~3000 ex.)" if x == "quick" else "Full (3 epochs)",
            key="ft_mode_models",
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
        key="ft_topics_filter_models",
    )
    ft_pos_ratio = st.slider(
        "Recalibrage classe positif (train)",
        min_value=0.0,
        max_value=0.40,
        value=0.25,
        step=0.01,
        key="ft_target_pos_ratio_models",
    )
    ft_pos_mult = st.slider(
        "Limite sur-échantillonnage positif (x)",
        min_value=1.0,
        max_value=6.0,
        value=3.0,
        step=0.5,
        key="ft_pos_oversample_multiplier_models",
    )

    b6, b7, _ = st.columns(3)
    with b6:
        if st.button(
            "Lancer le fine-tuning",
            type="primary",
            use_container_width=True,
            disabled=not may_admin,
            key="btn_finetune_models",
        ):
            cmd = [
                sys.executable,
                "scripts/finetune_sentiment.py",
                "--model",
                ft_backbone,
                "--epochs",
                str(ft_epochs),
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
            key="btn_eval_finetune_models",
        ):
            _run_command(
                "eval", [sys.executable, "scripts/finetune_sentiment.py", "--eval-only"]
            )

    finetuned_path = getattr(settings, "sentiment_finetuned_model_path", None)
    if finetuned_path:
        st.caption(f"Checkpoint .env actif : `{finetuned_path}` (nom unifié : {SENTIMENT_MODEL_DISPLAY_NAME})")
    else:
        st.caption(
            "Après fine-tuning, activez le modèle dans **Activation manuelle** "
            f"ou `.env` : `SENTIMENT_FINETUNED_MODEL_PATH=models/{ft_backbone}-sentiment-finetuned`"
        )


def _render_drift_panel(settings) -> None:
    """Drift sentiment/topic — alimente Prometheus (RUNBOOK § 11.4)."""
    import time

    import requests

    api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
    grafana_url = f"http://localhost:{settings.grafana_port}"
    drift_url = f"{api_base}/api/v1/analytics/drift-metrics"
    cache_key = "_drift_cache"

    with st.expander("Drift production (Prometheus + Grafana)", expanded=False):
        st.caption(
            "Distribution sentiment + topic dominance sur la dernière partition Gold. "
            "Cliquez **Rafraîchir drift** (calcul ~5–15 s, n'affecte plus /health)."
        )

        col_btn, col_info = st.columns([1, 3])
        force_refresh = col_btn.button("Rafraîchir drift", use_container_width=True, key="btn_refresh_drift_models")

        cache = st.session_state.get(cache_key)
        now = time.time()
        should_call = force_refresh

        if should_call:
            token = get_token()
            if not token:
                col_info.warning("Pas de token JWT — reconnectez-vous.")
                cache = None
            else:
                try:
                    r = requests.get(
                        drift_url,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=60,
                    )
                    if r.ok:
                        body = r.json()
                        cache = {"ts": now, "data": body, "error": None}
                        st.session_state[cache_key] = cache
                    else:
                        cache = {
                            "ts": now,
                            "data": None,
                            "error": f"HTTP {r.status_code} : {r.text[:120]}",
                        }
                        st.session_state[cache_key] = cache
                except requests.exceptions.ConnectionError:
                    cache = {"ts": now, "data": None, "error": f"API E2 injoignable ({api_base})"}
                    st.session_state[cache_key] = cache
                except Exception as e:
                    cache = {"ts": now, "data": None, "error": f"{type(e).__name__}: {e}"}
                    st.session_state[cache_key] = cache

        if cache is None:
            col_info.info("Cliquez **Rafraîchir drift** pour calculer les gauges Prometheus.")
            return

        if cache.get("error"):
            col_info.error(f"Refresh KO : {cache['error']}")
        else:
            age = int(time.time() - cache["ts"])
            col_info.caption(f"Dernier refresh : il y a {age} s")

        if cache.get("data"):
            data = cache["data"]
            score = data.get("drift_score", 0.0)
            entropy = data.get("sentiment_entropy", 0.0)
            dominance = data.get("topic_dominance", 0.0)
            total = data.get("articles_total", 0)

            m1, m2, m3, m4 = st.columns(4)
            score_status = "🔴" if score >= 0.7 else ("🟠" if score >= 0.5 else "🟢")
            m1.metric(f"{score_status} Drift score", f"{score:.3f}")
            m2.metric("Entropy sentiment", f"{entropy:.3f}")
            m3.metric("Topic dominance", f"{dominance:.3f}")
            m4.metric("Articles base", f"{total:,}".replace(",", " "))

            if score >= 0.7:
                st.error("Drift score ≥ 0.7 — envisager un réentraînement (RUNBOOK § 11.4).")
            elif score >= 0.5:
                st.warning("Drift score ≥ 0.5 — à surveiller.")

        st.markdown(
            f"[Grafana – Métriques & Drift]({grafana_url}/d/datasens-full)"
        )


# ── Bloc 1 : carte « modèle en production » ─────────────────────────────────
def _render_production_hero(
    active_model: str | None, bench: dict | None, eval_metrics: dict, gate: dict
) -> None:
    if active_model:
        name = canonical_sentiment_label(active_model)
        bench_key = "finetuned_local"
        subtitle = "Fine-tune maison de ac0hik/Sentiment_Analysis_French · inférence locale CPU (hors-ligne)."
    else:
        name = _bench_display_name("sentiment_fr") + " (défaut)"
        bench_key = "sentiment_fr"
        subtitle = "Aucun fine-tune activé — modèle de base ac0hik utilisé par défaut."

    entry = (bench or {}).get(bench_key, {}) if isinstance(bench, dict) else {}
    acc = entry.get("accuracy")
    f1m = entry.get("f1_macro")
    pos = (entry.get("per_class", {}).get("pos") or {}).get("f1")
    lat = entry.get("avg_latency_ms")
    auc = (eval_metrics.get(bench_key, {}) or {}).get("roc_auc_macro")

    st.markdown(f"#### Modèle en production : `{name}`")
    st.caption(subtitle)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Accuracy", f"{acc:.1%}" if acc is not None else "—")
    c2.metric("F1 macro", f"{f1m:.3f}" if f1m is not None else "—")
    c3.metric("F1 positif", f"{pos:.3f}" if pos is not None else "—")
    c4.metric("ROC-AUC", f"{auc:.3f}" if auc is not None else "—")
    c5.metric("Latence", f"{lat:.0f} ms" if lat is not None else "—")

    status = str(gate.get("status", "NO-GO"))
    col_v, col_t = st.columns([1, 3])
    with col_v:
        if status == "GO":
            st.success("Verdict prod : GO")
        elif status == "GO avec vigilance":
            st.warning("Verdict prod : GO avec vigilance")
        else:
            st.error("Verdict prod : NO-GO")
    with col_t:
        st.caption(
            "Meilleur des modèles évalués sur le même jeu de test "
            "(`data/goldai/ia/test.parquet`). ROC-AUC en one-vs-rest."
        )


# ── Bloc 2 : tableau comparatif unique ──────────────────────────────────────
def _render_comparison_table(bench: dict | None, eval_metrics: dict) -> None:
    if not bench:
        st.info("Aucun benchmark disponible. Lancez-en un dans **Outils avancés → Lancer un benchmark**.")
        return

    rows: list[dict] = []
    for key, r in bench.items():
        if not isinstance(r, dict) or "error" in r:
            continue
        per = r.get("per_class", {}) or {}
        pos = per.get("pos", {}).get("f1", per.get("positif", {}).get("f1", 0))
        auc = (eval_metrics.get(key, {}) or {}).get("roc_auc_macro")
        rows.append(
            {
                "_acc": r.get("accuracy", 0),
                "_key": key,
                "Modèle": _bench_display_name(key),
                "Type": "Fine-tune maison" if key == "finetuned_local" else "Base",
                "Accuracy": f"{r.get('accuracy', 0):.1%}",
                "F1 macro": f"{r.get('f1_macro', 0):.3f}",
                "F1 positif": f"{pos:.3f}",
                "ROC-AUC": f"{auc:.3f}" if auc is not None else "—",
                "Latence": f"{r.get('avg_latency_ms', 0):.0f} ms",
            }
        )
    if not rows:
        st.info("Benchmark présent mais vide.")
        return

    rows.sort(key=lambda x: x["_acc"], reverse=True)
    medals = ["🥇", "🥈", "🥉", "4", "5", "6"]
    for i, row in enumerate(rows):
        row["Rang"] = medals[min(i, len(medals) - 1)]
        if row["_key"] == "finetuned_local":
            row["Modèle"] = f"⭐ {row['Modèle']} (production)"

    df = pd.DataFrame(rows)[
        ["Rang", "Modèle", "Type", "Accuracy", "F1 macro", "F1 positif", "ROC-AUC", "Latence"]
    ]
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(
        "Tous évalués sur le même `test.parquet`. ROC-AUC (one-vs-rest) calculé sur les deux finalistes."
    )


# ── Outils avancés ──────────────────────────────────────────────────────────
def _render_decision_block(gate: dict) -> None:
    st.caption(
        "Entraînement = qualité d'apprentissage (train/validation). "
        "Inférence = qualité réelle en production (test + latence)."
    )
    explain_rows = [
        {
            "Étape": "Entraînement (offline)",
            "Objectif": "Apprendre le modèle",
            "Mesures clés": "eval_accuracy, eval_f1_macro, eval_f1_pos",
            "Source": "trainer_state.json",
        },
        {
            "Étape": "Inférence (online)",
            "Objectif": "Prédire vite et bien",
            "Mesures clés": "accuracy, f1_macro, f1_pos, latency_ms",
            "Source": "AI_BENCHMARK_RESULTS.json + /ai/predict",
        },
    ]
    st.dataframe(pd.DataFrame(explain_rows), use_container_width=True, hide_index=True)

    c_train, c_inf, c_gate = st.columns(3)
    with c_train:
        st.markdown("**Entraînement (validation)**")
        st.metric("Modèle de référence", canonical_sentiment_label(gate.get("train_model_name")) or "n/a")
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
        st.metric("Modèle évalué", SENTIMENT_MODEL_DISPLAY_NAME)
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
        st.markdown("**Décision Go/No-Go**")
        gate_status = str(gate.get("status", "NO-GO"))
        if gate_status == "GO":
            st.success("GO")
        elif gate_status == "GO avec vigilance":
            st.warning("GO avec vigilance")
        else:
            st.error("NO-GO")

    st.markdown("**Règles de décision (explicites)**")
    for label, ok in gate.get("checks", []):
        st.markdown(f"- {'✅' if ok else '❌'} {label}")


def _render_training_detail(root: Path, trained_models: list[dict]) -> None:
    st.caption(
        "Chaque fine-tuning produit un modèle adapté à vos articles. "
        "Plus il y a de données, plus le modèle est précis."
    )
    if not trained_models:
        st.info("Aucun modèle fine-tuné dans `models/`. Utilisez **Fine-tuning** pour entraîner.")
        return

    rows_t: list[dict] = []
    for m in trained_models:
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
            }
        )
    st.dataframe(pd.DataFrame(rows_t), use_container_width=True, hide_index=True)

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
            df_loss = pd.DataFrame({"step": train_steps, "Train Loss": train_loss}).set_index("step")
            if eval_entries:
                for ev in eval_entries:
                    step = ev.get("step", train_steps[-1])
                    df_loss.loc[step, "Val Loss"] = ev["eval_loss"]
            st.line_chart(df_loss, use_container_width=True)

    run_rows = []
    for m in trained_models:
        if m.get("eval_accuracy"):
            run_rows.append({
                "Run": m["name"],
                "Date": m.get("trained_at", "—"),
                "Accuracy": round(m["eval_accuracy"], 4),
                "F1": round(m.get("eval_f1") or 0, 4),
                "Epochs": m.get("epochs", "—"),
            })
    if len(run_rows) > 1:
        st.caption("**Historique des runs**")
        df_runs = pd.DataFrame(run_rows)
        st.line_chart(df_runs.set_index("Run")[["Accuracy", "F1"]], use_container_width=True)


def _render_benchmark_actions(ctx: PageContext) -> None:
    root = ctx.project_root
    st.caption(
        "Compare les modèles HuggingFace sur votre dataset de test. "
        "**Relancez après chaque grosse collecte** : les métriques évoluent avec les données."
    )
    may_run = can_write()
    if not may_run:
        st.info("Rôle `reader` : benchmark en lecture seule (writer/admin requis pour lancer).")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            "Benchmark rapide (200 ex.)",
            use_container_width=True,
            disabled=not may_run,
            key="btn_bench_quick",
        ):
            _run_command("benchmark", [sys.executable, "scripts/ai_benchmark.py", "--max-samples", "200"])
    with c2:
        if st.button(
            "Benchmark complet",
            use_container_width=True,
            disabled=not may_run,
            key="btn_bench_full",
        ):
            _run_command("benchmark", [sys.executable, "scripts/ai_benchmark.py"])
    _render_last_report("monitoring")


def _render_activation(root: Path, trained_models: list[dict], active_model: str | None) -> None:
    st.caption(
        "Activez un modèle pour la production. Il sera utilisé par l'API `/ai/predict` "
        "et pour les insights Mistral."
    )
    all_model_options: dict[str, str] = {
        f"{_bench_display_name('sentiment_fr')} (base — défaut)": "",
        "CamemBERT (pré-entraîné)": "camembert_pretrained",
    }
    for m in trained_models:
        label = (
            f"{m['name']} — Accuracy {m['eval_accuracy']:.1%}" if m.get("eval_accuracy") else m["name"]
        )
        all_model_options[label] = m["path"]

    current_label = next(
        (lbl for lbl, path in all_model_options.items() if path == (active_model or "")),
        next(iter(all_model_options.keys())),
    )
    chosen_label = st.selectbox(
        "Modèle à activer",
        list(all_model_options.keys()),
        index=list(all_model_options.keys()).index(current_label),
        key="activate_model_select",
    )
    chosen_path = all_model_options[chosen_label]

    may_admin = can_admin()
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Activer ce modèle",
            type="primary",
            use_container_width=True,
            disabled=not may_admin,
            help=("Rôle admin requis (écriture de .env)." if not may_admin else None),
            key="btn_activate_model",
        ):
            if chosen_path:
                if _activate_model(root, chosen_path):
                    st.success(f"Modèle activé : `{canonical_sentiment_label(chosen_path)}`. Redémarrez l'API E2.")
                    st.rerun()
                else:
                    st.error("Impossible d'écrire dans .env — vérifiez les permissions.")
            else:
                if _activate_model(root, ""):
                    st.success(f"Modèle par défaut ({_bench_display_name('sentiment_fr')}) restauré.")
                    st.rerun()
    with col2:
        if trained_models and st.button(
            "Activer le meilleur automatiquement",
            use_container_width=True,
            disabled=not may_admin,
            help=("Rôle admin requis." if not may_admin else "Active le fine-tuné avec la meilleure accuracy"),
            key="btn_activate_best",
        ):
            best = max(trained_models, key=lambda m: m.get("eval_accuracy") or 0)
            if best.get("eval_accuracy") and _activate_model(root, best["path"]):
                st.success(f"Meilleur modèle activé : `{canonical_sentiment_label(best['path'])}` ({best['eval_accuracy']:.1%}).")
                st.rerun()


def render(ctx: PageContext) -> None:
    root = ctx.project_root

    st.markdown("### Modèles IA")
    st.caption("Le modèle en production, la preuve qu'il est le meilleur, et l'outillage MLOps.")

    active_model = _get_active_model(root)
    bench = _load_benchmark_results(root)
    trained = _scan_trained_models(root)
    eval_metrics = _load_eval_metrics(root)
    gate = _go_no_go_snapshot(active_model, bench, trained)

    if not active_model:
        st.warning(
            "Aucun modèle fine-tuné activé — le modèle de base est utilisé. "
            "Activez un fine-tuné dans **Outils avancés → Activation manuelle**."
        )

    # Bloc 1 — Modèle en production
    _render_production_hero(active_model, bench, eval_metrics, gate)

    # Bloc 2 — Comparatif
    st.divider()
    st.subheader("Pourquoi ce modèle ? — comparatif des candidats")
    _render_comparison_table(bench, eval_metrics)

    # Bloc 3 — Outils avancés (repliés)
    st.divider()
    st.markdown("#### Outils avancés")
    with st.expander("Comprendre la décision (entraînement vs inférence · Go/No-Go)", expanded=False):
        _render_decision_block(gate)
    with st.expander("Détail entraînement (validation, courbes de loss, historique)", expanded=False):
        _render_training_detail(root, trained)
    with st.expander("Lancer un benchmark", expanded=False):
        _render_benchmark_actions(ctx)
    with st.expander("Fine-tuning — entraîner un modèle", expanded=False):
        _render_finetune_controls(ctx)
    with st.expander("Activation manuelle d'un modèle", expanded=False):
        _render_activation(root, trained, active_model)
    _render_drift_panel(ctx.settings)
