"""
DataSens Streamlit Cockpit
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import requests

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.config import get_settings
from src.streamlit.auth_plug import (
    get_token,
    init_session_auth,
    is_logged_in,
    render_login_form,
    render_user_and_logout,
)


def _fmt_size(num: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} PB"


def _inject_css() -> None:
    st.markdown(
        """
    <style>
    .ds-hero { background: linear-gradient(135deg, #1a237e 0%, #283593 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; }
    .ds-hero h3 { color: #e8eaf6; margin: 0 0 0.5rem 0; font-size: 1.1rem; }
    .ds-hero p { color: #c5cae9; margin: 0; font-size: 0.9rem; }
    .ds-flow { display: flex; align-items: center; flex-wrap: wrap; gap: 0.3rem; margin: 1rem 0; font-size: 0.85rem; }
    .ds-flow span { color: #90caf9; }
    .ds-flow .arrow { color: #64b5f6; }
    .ds-card { background: #1e1e2e; border: 1px solid #333; border-radius: 10px; padding: 1rem; margin-bottom: 0.8rem; }
    .ds-card-title { color: #81d4fa; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.3rem; }
    .ds-card-value { color: #fff; font-size: 1.1rem; }
    .ds-card-empty { color: #78909c; }
    </style>
    """,
        unsafe_allow_html=True,
    )


def _scan_stage(path: Path, patterns: list[str]) -> dict:
    if not path.exists():
        return {"exists": False, "count": 0, "latest": None, "size": 0}
    files: list[Path] = []
    for pattern in patterns:
        files.extend(path.rglob(pattern))
    files = [p for p in files if p.is_file()]
    if not files:
        return {"exists": True, "count": 0, "latest": None, "size": 0}
    latest = max(files, key=lambda p: p.stat().st_mtime)
    total_size = sum(p.stat().st_size for p in files)
    return {
        "exists": True,
        "count": len(files),
        "latest": latest,
        "size": total_size,
    }


def _chrono_data(root: Path) -> pd.DataFrame:
    """Construit un DataFrame date -> stage -> nb fichiers, taille pour les graphes."""
    rows: list[dict] = []
    date_re = re.compile(r"^date=(\d{4}-\d{2}-\d{2})$")
    silver_re = re.compile(r"^v_(\d{4}-\d{2}-\d{2})$")

    def scan_stage_dir(stage_dir: Path, stage_name: str, pattern: re.Pattern) -> None:
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

    scan_stage_dir(root / "data" / "gold", "GOLD", date_re)
    scan_stage_dir(root / "data" / "silver", "SILVER", silver_re)
    scan_stage_dir(root / "data" / "goldai", "GoldAI", date_re)

    if not rows:
        return pd.DataFrame(columns=["date", "stage", "count", "size"])
    return pd.DataFrame(rows)


def _ia_metrics_from_parquet(root: Path) -> dict | None:
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
    out = {"total_articles": total, "source": source_label}
    if "sentiment" in df.columns:
        sent = df["sentiment"].value_counts()
        out["sentiment_distribution"] = sent.to_dict()
        out["sentiment_pct"] = (sent / total * 100).round(1).to_dict()
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
    return out


def _run_command(label: str, command: list[str], extra_env: dict | None = None) -> None:
    st.write(f"Commande: `{' '.join(command)}`")
    with st.spinner(f"Exécution: {label}"):
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            if extra_env:
                env.update({k: str(v) for k, v in extra_env.items() if v is not None})
            proc = subprocess.run(
                command,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=1800,
            )
            out = (proc.stdout or "").strip()
            if len(out) > 15000:
                out = "... (début tronqué)\n\n" + out[-15000:]
            st.code(out or "OK", language="text")
            if proc.returncode != 0:
                err = (proc.stderr or "").strip()
                if len(err) > 3000:
                    err = err[-3000:]
                st.error(err or "Erreur inconnue")
        except subprocess.TimeoutExpired:
            st.warning("Timeout: commande trop longue")


def main() -> None:
    settings = get_settings()
    st.set_page_config(page_title="DataSens Cockpit", layout="wide")

    api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
    try:
        r = requests.get(f"{api_base}/health", timeout=2)
        backend_ok = r.ok
    except Exception:
        backend_ok = False

    with st.sidebar:
        st.subheader("Backend (API)")
        st.caption(f"`{api_base}`")
        if backend_ok:
            st.success("Connecte")
        else:
            st.warning("Arrete")
            st.caption("Lancer : start_full.bat ou python run_e2_api.py")
        st.divider()
        init_session_auth()
        if not is_logged_in():
            if render_login_form():
                st.rerun()
        else:
            render_user_and_logout()

    # Securite : aucun panel accessible sans connexion
    if not is_logged_in():
        st.warning("Connectez-vous dans la barre laterale pour acceder au cockpit.")
        st.stop()

    st.title("DataSens Cockpit")
    _inject_css()

    raw_dir = PROJECT_ROOT / "data" / "raw"
    silver_dir = PROJECT_ROOT / "data" / "silver"
    gold_dir = PROJECT_ROOT / "data" / "gold"
    goldai_dir = PROJECT_ROOT / "data" / "goldai"
    ia_dir = goldai_dir / "ia"

    # Flux réel : sources (dont ZZDB) → RAW → SILVER (+ topics) → GOLD (+ sentiment) → MongoDB → GoldAI + copie IA
    # Topics arrivent en SILVER ; sentiment (positif/négatif/neutre) arrive en GOLD. Pas d'« annotation » en plus.
    stages = [
        (
            "RAW (sources brutes)",
            raw_dir,
            ["*.json", "*.csv"],
            "Articles bruts extraits des sources RSS, agrégateurs et jeux de données.",
        ),
        (
            "SILVER (nettoyage, fusion)",
            silver_dir,
            ["*.parquet"],
            "Nettoyage, fusion, agrégation. Les topics (topic_1, topic_2) sont ajoutés ici.",
        ),
        (
            "GOLD (parquet quotidien)",
            gold_dir,
            ["*.parquet"],
            "Source de vérité. Le sentiment IA (positif/négatif/neutre) est ajouté ici. Envoyé vers MongoDB pour stockage long terme.",
        ),
        (
            "GoldAI (fusion long terme)",
            goldai_dir,
            ["merged_all_dates.parquet", "*.parquet"],
            "Fusion de tous les GOLD, stockage long terme MongoDB. Contient déjà sentiment + topics.",
        ),
        (
            "Copie IA (entraînement)",
            ia_dir,
            ["merged_all_dates_annotated.parquet", "*.parquet"],
            "Même données (sentiment + topics déjà dans la source de vérité). Copie dédiée au split train/val/test pour l'entraînement des modèles.",
        ),
    ]

    tab_overview, tab_pipeline, tab_pilotage, tab_ia, tab_monitoring = st.tabs(
        ["Vue d'ensemble", "Pipeline & Fusion", "Pilotage", "IA", "Monitoring"]
    )

    with tab_overview:
        st.markdown(
            """
        <div class="ds-hero">
        <h3>Objectif</h3>
        <p>Interface d'évaluation des sentiments croisant différentes sources de données.</p>
        <div class="ds-flow">
        <span>Sources</span><span class="arrow">→</span><span>RAW</span><span class="arrow">→</span><span>SILVER</span><span>(+ topics)</span><span class="arrow">→</span><span>GOLD</span><span>(+ sentiment)</span><span class="arrow">→</span><span>GoldAI</span><span class="arrow">→</span><span>Copie IA</span>
        </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        for idx, (name, path, patterns, _desc) in enumerate(stages):
            target = col1 if idx % 3 == 0 else col2 if idx % 3 == 1 else col3
            with target:
                data = _scan_stage(path, patterns)
                if data["exists"]:
                    f = "fichier" if data["count"] == 1 else "fichiers"
                    val = f"{data['count']} {f} · {_fmt_size(data['size'])}"
                    cls = ""
                else:
                    val = "—"
                    cls = " ds-card-empty"
                st.markdown(
                    f'<div class="ds-card"><div class="ds-card-title">{name}</div><div class="ds-card-value{cls}">{val}</div></div>',
                    unsafe_allow_html=True,
                )
        st.divider()
        st.caption("API & Dependencies")
        api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
        api_v1 = f"{api_base}{settings.api_v1_prefix}"

        try:
            _ = requests.get(f"{api_base}/health", timeout=2)
            api_ok = True
        except Exception:
            api_ok = False
        if not api_ok:
            st.info(
                "**API non démarrée.** Pour activer /health et /metrics : "
                "onglet **Pilotage** -> bouton **Lancer API E2**. "
                "Gardez ce terminal ouvert (l’API tourne dans un autre)."
            )

        st.write("Endpoints clés:")
        st.code(
            "\n".join(
                [
                    f"{api_base}/health",
                    f"{api_base}/metrics",
                    f"{api_v1}/ai/predict",
                    f"{api_v1}/ai/dataset",
                ]
            ),
            language="text",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.caption("Vérifie que l'API répond et affiche le JSON de santé (version, status).")
            if st.button("Tester /health"):
                try:
                    resp = requests.get(f"{api_base}/health", timeout=5)
                    st.code(resp.text, language="json")
                except requests.exceptions.ConnectionError:
                    st.warning("Connexion refusée. Démarrez l’API (Pilotage → Lancer API E2).")
                except Exception as exc:
                    st.error(str(exc)[:200])

        with col_b:
            st.caption("Récupère les métriques Prometheus de l'API (requêtes, latence, etc.).")
            if st.button("Afficher /metrics"):
                try:
                    resp = requests.get(f"{api_base}/metrics", timeout=5)
                    st.code(resp.text[-2000:], language="text")
                except requests.exceptions.ConnectionError:
                    st.warning("Connexion refusée. Démarrez l’API (Pilotage → Lancer API E2).")
                except Exception as exc:
                    st.error(str(exc)[:200])

    with tab_pipeline:
        gold_dir = PROJECT_ROOT / "data" / "gold"
        goldai_dir = PROJECT_ROOT / "data" / "goldai"
        merged_path = goldai_dir / "merged_all_dates.parquet"
        meta_path = goldai_dir / "metadata.json"

        fusion_err = st.session_state.pop("fusion_error", None)
        if fusion_err:
            st.error(f"Erreur fusion : {fusion_err}")
        fusion = st.session_state.get("fusion_success")
        if fusion:
            st.balloons()
            st.success(
                f"**Fusion réalisée.** GOLD ({fusion['date']}) → GoldAI. "
                f"Avant : **{fusion['avant']:,}** · Maintenant : **{fusion['apres']:,}** (+{fusion['ajoutes']:,})"
            )
            st.session_state.pop("fusion_success", None)

        st.markdown("### Fusion Parquet : GOLD quotidien + GoldAI")
        dates_in_goldai = []
        if meta_path.exists():
            import json

            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            dates_in_goldai = meta.get("dates_included", [])
        if dates_in_goldai:
            st.caption(f"Dates dans GoldAI : {', '.join(sorted(dates_in_goldai))}")

        gold_dates = (
            sorted(
                [
                    d.name.replace("date=", "")
                    for d in gold_dir.iterdir()
                    if d.is_dir() and d.name.startswith("date=")
                ],
                reverse=True,
            )
            if gold_dir.exists()
            else []
        )
        selected_date = st.selectbox("Date GOLD", gold_dates or ["—"], index=0)

        df_gold = df_goldai = None
        gold_file = (
            gold_dir / f"date={selected_date}" / "articles.parquet"
            if selected_date != "—"
            else None
        )
        if gold_file and gold_file.exists():
            df_gold = pd.read_parquet(gold_file)
        if merged_path.exists():
            df_goldai = pd.read_parquet(merged_path)
        n_gold = len(df_gold) if df_gold is not None else 0
        n_goldai = len(df_goldai) if df_goldai is not None else 0

        if st.button("Fusionner GoldAI", type="primary", use_container_width=True):
            with st.spinner("Fusion en cours…"):
                proc = subprocess.run(
                    [sys.executable, "scripts/merge_parquet_goldai.py"],
                    cwd=str(PROJECT_ROOT),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                    timeout=600,
                )
            if proc.returncode == 0 and meta_path.exists():
                import json

                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                apres = meta.get("total_rows", n_goldai + n_gold)
                st.session_state["fusion_success"] = {
                    "avant": n_goldai,
                    "apres": apres,
                    "ajoutes": apres - n_goldai,
                    "date": selected_date or "—",
                }
            elif proc.returncode != 0:
                st.session_state["fusion_error"] = (proc.stderr or proc.stdout or "")[-500:]
            st.rerun()

        w1, w2, w3, w4 = st.columns(4)
        with w1:
            st.markdown("#### 1. GOLD quotidien")
            if df_gold is not None:
                st.metric("Lignes", f"{n_gold:,}")
                st.dataframe(df_gold.head(80), use_container_width=True, height=260)
            else:
                st.info("—")
        with w2:
            st.markdown("#### 2. GoldAI")
            if df_goldai is not None:
                st.metric("Lignes", f"{n_goldai:,}")
                st.dataframe(df_goldai.head(80), use_container_width=True, height=260)
            else:
                st.info("—")
        with w3:
            st.markdown("#### 3. Lignes ajoutées")
            n_new, df_new = 0, None
            if (
                df_gold is not None
                and df_goldai is not None
                and "id" in df_gold.columns
                and "id" in df_goldai.columns
            ):
                ids = set(df_goldai["id"])
                df_new = df_gold[~df_gold["id"].isin(ids)]
                n_new = len(df_new)
            st.metric("+ lignes", f"{n_new:,}")
            if n_new == 0 and df_gold is not None and df_goldai is not None:
                st.caption("Date déjà fusionnée")
            if df_new is not None or df_gold is not None:
                st.dataframe(
                    (df_new if df_new is not None else df_gold).head(80),
                    use_container_width=True,
                    height=260,
                )
            else:
                st.info("—")
        with w4:
            st.markdown("#### 4. Résultat")
            if df_gold is not None and df_goldai is not None:
                merged = pd.concat([df_goldai, df_gold], ignore_index=True)
                n_concat = len(merged)
                if "id" in merged.columns:
                    merged = merged.drop_duplicates(subset=["id"], keep="last")
                n_res = len(merged)
                n_dedup = n_concat - n_res
                st.caption(f"Concat : {n_goldai:,}+{n_gold:,}={n_concat:,}")
                st.markdown(f"→ **{n_res:,}** ({n_dedup:,} doublons)")
                st.dataframe(merged.tail(80), use_container_width=True, height=260)
            elif df_goldai is not None:
                st.metric("Lignes", f"{n_goldai:,}")
                st.dataframe(df_goldai.head(80), use_container_width=True, height=260)
            else:
                st.info("—")

        st.divider()
        st.markdown("### Datasets par étape")
        st.caption("RAW → SILVER → GOLD → GoldAI → Copie IA")

        def _load_df_sample(path: Path, max_rows: int = 100) -> pd.DataFrame | None:
            """Charge un DataFrame à partir d'un CSV ou Parquet, limité à max_rows."""
            if not path.exists():
                return None
            try:
                if path.suffix.lower() == ".parquet":
                    return pd.read_parquet(path).head(max_rows)
                if path.suffix.lower() == ".csv":
                    return pd.read_csv(path, nrows=max_rows, encoding="utf-8", on_bad_lines="skip")
                return None
            except Exception:
                return None

        def _load_df_full(path: Path) -> pd.DataFrame | None:
            """Charge un DataFrame complet (pour count uniquement)."""
            if not path.exists():
                return None
            try:
                if path.suffix.lower() == ".parquet":
                    return pd.read_parquet(path)
                if path.suffix.lower() == ".csv":
                    return pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
                return None
            except Exception:
                return None

        def _render_stage_block(
            title: str,
            desc: str,
            paths: list[Path],
            primary_idx: int = 0,
            exclude_zzdb: bool = False,
        ) -> None:
            """Affiche un bloc pour une étape."""
            primary = (
                paths[primary_idx] if primary_idx < len(paths) else (paths[0] if paths else None)
            )
            if not primary or not primary.exists():
                with st.expander(f"**{title}** – données absentes", expanded=True):
                    st.caption(desc)
                    st.info("Aucun fichier trouvé.")
                    return
            df_full = _load_df_full(primary)
            if df_full is None:
                with st.expander(f"**{title}** – erreur lecture", expanded=True):
                    st.caption(desc)
                    st.error(f"Impossible de lire {primary.name}")
                    return
            if exclude_zzdb and "source" in df_full.columns:
                mask = ~df_full["source"].astype(str).str.lower().str.contains("zzdb", na=False)
                df_full = df_full[mask]
            n_rows = len(df_full)
            cols = list(df_full.columns)
            if n_rows == 0 and exclude_zzdb:
                with st.expander(f"**{title}**", expanded=True):
                    st.caption(desc)
                    st.info("Aucune donnée hors sources synthétiques dans les exports.")
                return
            df_preview = df_full.head(50)
            with st.expander(f"**{title}** · {n_rows:,} lignes · {len(cols)} col.", expanded=True):
                st.caption(desc)
                st.caption(f"`{primary.relative_to(PROJECT_ROOT)}`")
                st.dataframe(df_preview, use_container_width=True, height=320)

        exports_dir = PROJECT_ROOT / "exports"
        raw_dir = PROJECT_ROOT / "data" / "raw"
        silver_dir = PROJECT_ROOT / "data" / "silver"
        gold_dir = PROJECT_ROOT / "data" / "gold"
        goldai_dir = PROJECT_ROOT / "data" / "goldai"
        ia_dir = goldai_dir / "ia"

        # Déterminer les fichiers sources par étape
        raw_paths = []
        if (exports_dir / "raw.csv").exists():
            raw_paths.append(exports_dir / "raw.csv")
        for d in sorted(raw_dir.iterdir(), reverse=True):
            if d.is_dir() and "sources" in d.name:
                for f in [d / "raw_articles.csv", d / "raw_articles.json"]:
                    if f.exists() and f.suffix == ".csv":
                        raw_paths.append(f)
                        break
                if raw_paths:
                    break

        silver_paths = []
        if (exports_dir / "silver.csv").exists():
            silver_paths.append(exports_dir / "silver.csv")
        for d in sorted(silver_dir.iterdir(), reverse=True):
            if d.is_dir():
                for f in d.rglob("*.parquet"):
                    silver_paths.append(f)
                    break
            if silver_paths:
                break

        gold_paths = []
        if (exports_dir / "gold.parquet").exists():
            gold_paths.append(exports_dir / "gold.parquet")
        if (exports_dir / "gold.csv").exists():
            gold_paths.append(exports_dir / "gold.csv")
        for d in sorted(gold_dir.iterdir(), reverse=True):
            if d.is_dir() and d.name.startswith("date="):
                p = d / "articles.parquet"
                if p.exists():
                    gold_paths.append(p)
                    break

        _render_stage_block(
            "1. RAW",
            "Sources brutes (RSS, agrégateurs).",
            raw_paths or [exports_dir / "raw.csv"],
            exclude_zzdb=True,
        )
        _render_stage_block(
            "2. SILVER",
            "Nettoyage, fusion, topics.",
            silver_paths or [exports_dir / "silver.csv"],
            exclude_zzdb=True,
        )
        _render_stage_block(
            "3. GOLD",
            "Parquet quotidien, sentiment IA.",
            gold_paths or [goldai_dir / "merged_all_dates.parquet"],
        )
        _render_stage_block(
            "4. GoldAI",
            "Fusion long terme des GOLD.",
            [goldai_dir / "merged_all_dates.parquet"],
        )
        # Copie IA : merged_all_dates_annotated ou train comme fallback
        ia_paths = [
            ia_dir / "merged_all_dates_annotated.parquet",
            ia_dir / "train.parquet",
            ia_dir / "val.parquet",
            ia_dir / "test.parquet",
        ]
        ia_existing = [p for p in ia_paths if p.exists()]
        ia_primary = (
            ia_existing[0] if ia_existing else ia_dir / "merged_all_dates_annotated.parquet"
        )
        if not ia_primary.exists():
            with st.expander("**5. Copie IA** – données absentes", expanded=True):
                st.caption("Split train/val/test pour l'entraînement.")
                st.info("Pilotage → bouton « Créer copie IA (split) »")
        else:
            _render_stage_block(
                "5. Copie IA",
                "Split train/val/test.",
                ia_existing,
            )

        for name, path in [
            ("train", ia_dir / "train.parquet"),
            ("val", ia_dir / "val.parquet"),
            ("test", ia_dir / "test.parquet"),
        ]:
            if path.exists():
                with st.expander(f"5b. {name}", expanded=False):
                    df = _load_df_full(path)
                    if df is not None:
                        st.dataframe(df.head(30), use_container_width=True, height=280)

    with tab_pilotage:

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
        n_raw, n_silver, n_gold = 0, 0, 0
        if Path(db_path).exists():
            try:
                import sqlite3

                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                has_raw = cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='raw_data'"
                ).fetchone()
                conn.close()
                if has_raw:
                    from src.aggregator import DataAggregator

                    agg = DataAggregator(db_path)
                    n_raw = len(agg.aggregate_raw())
                    n_silver = len(agg.aggregate_silver())
                    n_gold = len(agg.aggregate())
                    agg.close()
            except Exception:
                pass

        m1, m2, m3 = st.columns(3)
        m1.metric("RAW", f"{n_raw:,}")
        m2.metric("SILVER", f"{n_silver:,}")
        m3.metric("GOLD", f"{n_gold:,}")

        st.divider()
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Pipeline E1", type="primary", use_container_width=True):
                env = {
                    "ZZDB_MAX_ARTICLES": "50",
                    "ZZDB_CSV_MAX_ARTICLES": "1000",
                    "FORCE_ZZDB_REIMPORT": "false",
                }
                _run_command("pipeline", [sys.executable, "main.py"], extra_env=env)
        with b2:
            if st.button("Fusion GoldAI", type="primary", use_container_width=True):
                _run_command("goldai", [sys.executable, "scripts/merge_parquet_goldai.py"])
        with b3:
            if st.button("Copie IA", type="primary", use_container_width=True):
                _run_command("copie IA", [sys.executable, "scripts/create_ia_copy.py"])

        b4, b5, _ = st.columns(3)
        with b4:
            if st.button("Lancer API E2", use_container_width=True):
                _run_command("api", [sys.executable, "run_e2_api.py"])
        with b5:
            if st.button("Backup MongoDB", use_container_width=True):
                _run_command(
                    "backup",
                    [sys.executable, "scripts/backup_parquet_to_mongo.py"],
                    extra_env={"MONGO_STORE_PARQUET": "true"},
                )

        st.caption("Fine-tuning : améliore le modèle IA avec les données GoldAI")
        b6, b7, _ = st.columns(3)
        with b6:
            if st.button(
                "Fine-tuner sentiment",
                use_container_width=True,
                help="Entraîne CamemBERT sur train.parquet (Copie IA). Peut prendre 10-30 min.",
            ):
                _run_command(
                    "finetune",
                    [
                        sys.executable,
                        "scripts/finetune_sentiment.py",
                        "--model",
                        "camembert",
                        "--epochs",
                        "3",
                    ],
                )
        with b7:
            if st.button(
                "Évaluer modèle",
                use_container_width=True,
                help="Calcule accuracy/F1 sur val.parquet (modèle fine-tuné)",
            ):
                _run_command(
                    "eval", [sys.executable, "scripts/finetune_sentiment.py", "--eval-only"]
                )
        finetuned_path = getattr(settings, "sentiment_finetuned_model_path", None)
        if finetuned_path:
            st.caption(f"Modèle fine-tuné : {finetuned_path}")

        with st.expander("Paramètres & détails", expanded=False):
            zzdb_max = st.number_input("ZZDB_MAX_ARTICLES", min_value=0, value=50, step=10)
            zzdb_csv_max = st.number_input(
                "ZZDB_CSV_MAX_ARTICLES", min_value=0, value=1000, step=100
            )
            force_reimport = st.checkbox("FORCE_ZZDB_REIMPORT", value=False)
            env = {
                "ZZDB_MAX_ARTICLES": str(zzdb_max),
                "ZZDB_CSV_MAX_ARTICLES": str(zzdb_csv_max),
                "FORCE_ZZDB_REIMPORT": "true" if force_reimport else "false",
            }
            if st.button("Pipeline E1 (avec params)"):
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
            if st.button("Veille IA"):
                _run_command("veille", [sys.executable, "scripts/veille_digest.py"])
            if st.button("Benchmark IA"):
                _run_command("benchmark", [sys.executable, "scripts/ai_benchmark.py"])
            if st.button("Lister Parquet MongoDB"):
                _run_command("mongo", [sys.executable, "scripts/list_mongo_parquet.py"])
            st.divider()
            st.caption("Après fine-tuning : ajoutez dans .env :")
            st.code("SENTIMENT_FINETUNED_MODEL_PATH=models/camembert-sentiment-finetuned")

    with tab_ia:
        api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
        api_v1 = f"{api_base}{settings.api_v1_prefix}"

        st.markdown("### IA – Modèles & Assistant")
        try:
            api_ok = requests.get(f"{api_base}/health", timeout=2).ok
        except Exception:
            api_ok = False
        if not api_ok:
            st.warning(
                "L’API n’est pas démarrée. Allez dans **Pilotage** → *Lancer API E2* avant d’utiliser la prédiction ou l’assistant."
            )
        with st.expander("Comment utiliser cet onglet ?", expanded=True):
            st.markdown("""
            **1. Prédiction** : Testez l’analyse de sentiment sur un texte (ex. « Le marché affiche une hausse »).  
            → Saisissez un texte, choisissez un modèle, cliquez sur *Prédire*. Si un modèle fine-tuné est configuré (SENTIMENT_FINETUNED_MODEL_PATH), il est utilisé automatiquement.

            **2. Assistant** : Posez des questions par domaine (Politique, Financier, Utilisateurs).  
            → Sélectionnez un thème, tapez votre question dans le champ en bas. L’assistant répond en fonction des données du projet.
            """)

        st.subheader("1. Prédiction de sentiment")
        st.caption(
            "Analysez le sentiment (positif / négatif / neutre) d’un texte avec FlauBERT ou CamemBERT."
        )
        pred_text = st.text_area(
            "Texte à analyser",
            "Le marché affiche une hausse.",
            height=70,
            help="Ex. une phrase ou un paragraphe",
        )
        pred_model = st.selectbox(
            "Modèle", ["flaubert", "camembert"], key="pred_model", help="FlauBERT ou CamemBERT"
        )
        if st.button("Prédire le sentiment"):
            token = get_token()
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            try:
                r = requests.post(
                    f"{api_v1}/ai/predict",
                    json={"text": pred_text, "model": pred_model, "task": "sentiment-analysis"},
                    headers=headers,
                    timeout=30,
                )
                if r.ok:
                    data = r.json()
                    st.json(data.get("result", data))
                else:
                    st.error(f"Erreur {r.status_code}")
            except requests.exceptions.ConnectionError:
                st.warning("API non démarrée (Pilotage → Lancer API E2)")
            except Exception as e:
                st.error(str(e)[:150])

        st.divider()
        st.subheader("2. Assistant – Questions par domaine")
        st.caption(
            "Posez des questions sur les données : tendances politiques, financières ou comportement utilisateurs."
        )
        if "ia_chat_messages" not in st.session_state:
            st.session_state.ia_chat_messages = []
        theme_options = {
            "Politique": "politique",
            "Financier": "financier",
            "Utilisateurs": "utilisateurs",
        }
        theme = theme_options[
            st.selectbox(
                "Thème de la question",
                list(theme_options.keys()),
                key="ia_theme",
                help="Politique : veille, tendances | Financier : marché, indicateurs | Utilisateurs : comportement, satisfaction",
            )
        ]
        st.caption(
            "Exemples : « Quelles tendances sur l'inflation ? » (Financier) · « Résume les sujets politiques récents » (Politique)"
        )
        if st.button("Effacer la conversation", key="ia_clear"):
            st.session_state.ia_chat_messages = []
            st.rerun()
        for msg in st.session_state.ia_chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        prompt = st.chat_input("Votre question (insights)...")
        if prompt:
            st.session_state.ia_chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("assistant"), st.spinner("Réponse..."):
                token = get_token()
                headers = {"Content-Type": "application/json"}
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                try:
                    r = requests.post(
                        f"{api_v1}/ai/insight",
                        json={"theme": theme, "message": prompt},
                        headers=headers,
                        timeout=30,
                    )
                    reply = r.json().get("reply", "—") if r.ok else f"Erreur {r.status_code}"
                except requests.exceptions.ConnectionError:
                    reply = "API non disponible"
                except Exception as e:
                    reply = str(e)[:150]
                st.write(reply)
            st.session_state.ia_chat_messages.append({"role": "assistant", "content": reply})
            st.rerun()

    with tab_monitoring:
        st.markdown("### Pilotage du modèle & insights")
        api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
        api_v1 = f"{api_base}{settings.api_v1_prefix}"
        prometheus_url = f"http://localhost:{settings.prometheus_port}"
        grafana_url = f"http://localhost:{settings.grafana_port}"

        st.subheader("Métriques IA")
        st.caption("Déséquilibres, confiance, volume – pour piloter le modèle.")
        ia = _ia_metrics_from_parquet(PROJECT_ROOT)
        if ia is None:
            st.warning(
                "Aucune donnée Parquet (GOLD/GoldAI) disponible. Lancez le pipeline puis Fusion GoldAI."
            )
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total articles", ia["total_articles"])
                st.caption(f"Source : {ia.get('source', '—')}")
            with c2:
                if "sentiment_score_mean" in ia:
                    st.metric("Score sentiment (moy)", f"{ia['sentiment_score_mean']:.3f}")
                if "topic_confidence_mean" in ia:
                    st.metric("Confiance topics (moy)", f"{ia['topic_confidence_mean']:.3f}")
            with c3:
                if "sentiment_distribution" in ia:
                    sent = ia["sentiment_distribution"]
                    st.caption("Distribution sentiment")
                    for label, count in list(sent.items())[:5]:
                        pct = ia.get("sentiment_pct", {}).get(label, 0)
                        st.caption(f"  • {label}: {count} ({pct}%)")

            with st.expander("Distribution des topics (pour rééquilibrer le modèle)"):
                if "topic_distribution" in ia:
                    for topic, count in list(ia["topic_distribution"].items())[:20]:
                        st.text(f"  {topic}: {count}")
                else:
                    st.caption("Colonne topic_1 absente dans le dataset.")

            with st.expander("Top sources (volume)"):
                if "top_sources" in ia:
                    for src, count in list(ia["top_sources"].items())[:10]:
                        st.text(f"  {src}: {count}")
                else:
                    st.caption("Colonne source absente.")

            st.caption(
                "Surveiller déséquilibres et confiance ; fine-tuner CamemBERT/FlauBERT sur la copie IA."
            )

        st.divider()
        st.subheader("Chronologie")
        df_chrono = _chrono_data(PROJECT_ROOT)
        if not df_chrono.empty:
            df_chrono = df_chrono.sort_values("date")
            pivot_c = df_chrono.pivot(index="date", columns="stage", values="count").fillna(0)
            if not pivot_c.empty:
                st.line_chart(pivot_c)
        else:
            st.caption("Aucune donnée par date")

        with st.expander("Prometheus & Grafana"):
            st.caption(
                f"API metrics : {api_base}/metrics · Prometheus : {prometheus_url} · Grafana : {grafana_url}"
            )


if __name__ == "__main__":
    main()
