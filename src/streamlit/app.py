"""
DataSens Streamlit Cockpit
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime
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
    st.caption("Vue complète + pilotage + modifications contrôlées")

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
            "Toutes les sources (RSS, ZZDB, etc.) ingérées ici. ZZDB = source comme les autres, pas du parquet.",
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

    tab_overview, tab_pilotage, tab_datasets, tab_monitoring, tab_chrono, tab_ia = st.tabs(
        ["Cockpit", "Pilotage", "Datasets", "Metriques avancees", "Chronologie", "Assistant IA"]
    )

    with tab_overview:
        col1, col2, col3 = st.columns(3)
        for idx, (name, path, patterns, _desc) in enumerate(stages):
            target = col1 if idx % 3 == 0 else col2 if idx % 3 == 1 else col3
            with target:
                data = _scan_stage(path, patterns)
                st.subheader(name)
                if not data["exists"]:
                    st.error("Dossier absent")
                    continue
                st.metric("Fichiers", data["count"])
                st.metric("Taille totale", _fmt_size(data["size"]))
                if data["latest"]:
                    latest = data["latest"]
                    st.caption(f"Dernier fichier: {latest.name}")
                    st.caption(f"Modifié: {datetime.fromtimestamp(latest.stat().st_mtime)}")

        st.divider()
        st.header("API & Monitoring")
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

    with tab_pilotage:
        st.header("Pilotage complet")
        st.caption("Tout lancer manuellement avec des boutons.")

        with st.expander("Paramètres exécution (pipeline)", expanded=True):
            zzdb_max = st.number_input("ZZDB_MAX_ARTICLES", min_value=0, value=50, step=10)
            zzdb_csv_max = st.number_input(
                "ZZDB_CSV_MAX_ARTICLES", min_value=0, value=1000, step=100
            )
            force_reimport = st.checkbox("FORCE_ZZDB_REIMPORT", value=False)

        env = {
            "ZZDB_MAX_ARTICLES": int(zzdb_max),
            "ZZDB_CSV_MAX_ARTICLES": int(zzdb_csv_max),
            "FORCE_ZZDB_REIMPORT": "true" if force_reimport else "false",
        }

        col_run1, col_run2, col_run3 = st.columns(3)
        with col_run1:
            st.caption(
                "Collecte E1 (sources, ZZDB), enrichissement topics/sentiment, rapport et dashboard. Peut prendre plusieurs minutes."
            )
            if st.button("Lancer pipeline (main.py)"):
                _run_command("pipeline", [sys.executable, "main.py"], extra_env=env)
        with col_run2:
            st.caption(
                "Fusionne les Parquet GOLD par date en un seul fichier (goldai). Prerequis pour le dataset IA."
            )
            if st.button("Fusion GoldAI"):
                _run_command("goldai merge", [sys.executable, "scripts/merge_parquet_goldai.py"])
        with col_run3:
            st.caption(
                "Genere un digest de veille (RSS, benchmarks, resume). Utile pour suivre l'actualite tech et donnees."
            )
            if st.button("Veille IA"):
                _run_command("veille", [sys.executable, "scripts/veille_digest.py"])

        col_run4, col_run5, col_run6 = st.columns(3)
        with col_run4:
            st.caption(
                "Compare les modèles IA (sentiment, topics) sur un échantillon. Affiche précision et temps."
            )
            if st.button("Benchmark IA"):
                _run_command("benchmark", [sys.executable, "scripts/ai_benchmark.py"])
        with col_run5:
            st.caption(
                "Liste les Parquet stockés dans MongoDB GridFS (backups long terme). Pas de téléchargement."
            )
            if st.button("Lister Parquet MongoDB"):
                _run_command(
                    "mongo list", [sys.executable, "scripts/mongo_parquet_restore.py", "--list"]
                )
        with col_run6:
            st.caption(
                "Démarre l'API FastAPI (E2) dans ce terminal. Gardez la page ouverte ; pour usage permanent, lancez run_e2_api.py à part."
            )
            if st.button("Lancer API E2"):
                _run_command("api", [sys.executable, "run_e2_api.py"])

        st.divider()
        st.subheader("Sauvegarde long terme")
        st.caption(
            "Envoie les Parquet GOLD/GoldAI vers MongoDB GridFS pour archivage long terme. Nécessite MongoDB démarré."
        )
        if st.button("Backup MongoDB (Parquet → GridFS)"):
            _run_command(
                "backup MongoDB",
                [sys.executable, "scripts/backup_parquet_to_mongo.py"],
                extra_env={"MONGO_STORE_PARQUET": "true"},
            )

    with tab_datasets:
        st.header("Datasets – visualisation et copies modifiées")
        st.markdown(
            "**Flux :** Sources (dont ZZDB) → **RAW** → **SILVER** (+ topics) → **GOLD** (+ sentiment IA : positif/négatif/neutre) "
            "→ MongoDB → **GoldAI** + **copie IA** (split train/val/test). "
            "La source de vérité (GOLD) contient déjà sentiment et topics ; la copie IA est la même base, dédiée à l'entraînement."
        )
        st.caption(
            "La source de vérité (GOLD) reste intacte. Les modifications créent une copie dans data/edits/."
        )

        stage_names = [s[0] for s in stages]
        stage_descriptions = {s[0]: s[3] for s in stages}
        selected_stage = st.selectbox("Étape", stage_names, index=0)
        stage_map = {name: (path, patterns) for name, path, patterns, _ in stages}
        base_path, patterns = stage_map[selected_stage]
        if selected_stage in stage_descriptions:
            st.caption(stage_descriptions[selected_stage])

        files = []
        if base_path.exists():
            for pattern in patterns:
                files.extend(base_path.rglob(pattern))
        files = [p for p in files if p.is_file()]
        files_sorted = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

        if not files_sorted:
            st.warning("Aucun fichier trouvé")
            return

        selected_file = st.selectbox(
            "Fichier",
            [str(p.relative_to(PROJECT_ROOT)) for p in files_sorted],
        )
        file_path = PROJECT_ROOT / selected_file

        row_limit = st.number_input(
            "Prévisualisation (lignes)", min_value=10, max_value=5000, value=200, step=50
        )
        try:
            if file_path.suffix == ".parquet":
                df = pd.read_parquet(file_path)
            elif file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
            elif file_path.suffix == ".json":
                df = pd.read_json(file_path)
            else:
                st.error("Format non supporté")
                return
            st.dataframe(df.head(int(row_limit)))
        except Exception as exc:
            st.error(f"Erreur lecture: {exc}")
            return

        st.subheader("Copie modifiée (safe)")
        col_left, col_right = st.columns(2)
        with col_left:
            drop_cols = st.multiselect("Supprimer colonnes", list(df.columns))
            keyword = st.text_input("Filtrer (mot-clé dans title/content)")
        with col_right:
            sentiment_filter = st.selectbox(
                "Filtrer sentiment",
                ["(aucun)", "positif", "negatif", "négatif", "neutre"],
                index=0,
            )
            max_rows = st.number_input("Limiter lignes", min_value=0, value=0, step=100)

        df_mod = df.copy()
        if drop_cols:
            df_mod = df_mod.drop(columns=drop_cols, errors="ignore")
        if keyword:
            cols = [c for c in ["title", "content"] if c in df_mod.columns]
            if cols:
                mask = False
                for c in cols:
                    mask = mask | df_mod[c].astype(str).str.contains(keyword, case=False, na=False)
                df_mod = df_mod[mask]
        if sentiment_filter != "(aucun)" and "sentiment" in df_mod.columns:
            df_mod = df_mod[df_mod["sentiment"] == sentiment_filter]
        if max_rows and max_rows > 0:
            df_mod = df_mod.head(int(max_rows))

        st.caption(f"Lignes après modifications: {len(df_mod)}")
        st.dataframe(df_mod.head(200))

        output_dir = PROJECT_ROOT / "data" / "edits" / selected_stage.lower().split()[0]
        output_dir.mkdir(parents=True, exist_ok=True)
        output_name = st.text_input("Nom du fichier de sortie", f"{file_path.stem}_edited.parquet")
        st.caption(
            "Sauvegarde la version modifiée (filtres, colonnes supprimées) dans data/edits/. La source reste intacte."
        )
        if st.button("Enregistrer la copie"):
            out_path = output_dir / output_name
            try:
                if out_path.suffix == ".csv":
                    df_mod.to_csv(out_path, index=False)
                else:
                    df_mod.to_parquet(out_path, index=False)
                st.success(f"OK: {out_path}")
            except Exception as exc:
                st.error(f"Erreur écriture: {exc}")

    with tab_monitoring:
        st.header("Métriques avancées")
        st.caption("Prometheus, Grafana et métriques IA pour piloter et améliorer le modèle.")
        api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
        api_v1 = f"{api_base}{settings.api_v1_prefix}"
        prometheus_url = f"http://localhost:{settings.prometheus_port}"
        grafana_url = f"http://localhost:{settings.grafana_port}"

        try:
            r = requests.get(f"{api_base}/health", timeout=2)
            api_ok = r.ok
        except Exception:
            api_ok = False
        if not api_ok:
            st.info("**API non démarrée.** Onglet Pilotage → **Lancer API E2**, puis rafraîchir.")

        # ---- Ligne statut rapide ----
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.subheader("API (E2)")
            try:
                r = requests.get(f"{api_base}/health", timeout=3)
                st.success("OK" if r.ok else f"Status {r.status_code}")
            except requests.exceptions.ConnectionError:
                st.warning("Arrêtée")
            except Exception as e:
                st.error(str(e)[:80])
        with m2:
            st.subheader("Prometheus")
            try:
                r = requests.get(f"{prometheus_url}/api/v1/status/config", timeout=2)
                st.success("OK" if r.ok else "—")
            except Exception:
                st.caption("Non démarré")
                st.caption(f"Port {settings.prometheus_port}")
        with m3:
            st.subheader("Grafana")
            try:
                r = requests.get(grafana_url, timeout=2)
                st.success("OK" if r.status_code in (200, 302, 401) else "-")
            except Exception:
                st.caption("Non démarré")
                st.caption(f"Port {settings.grafana_port}")
        with m4:
            st.subheader("MongoDB")
            try:
                from pymongo import MongoClient

                client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=2000)
                client.admin.command("ping")
                client.close()
                st.success("OK")
            except Exception:
                st.warning("Hors ligne")

        st.divider()

        # ---- Prometheus ----
        st.subheader("Prometheus")
        st.caption(
            "Metriques exposees par l'API E2 (format Prometheus). Scrapez cette URL dans Prometheus pour Grafana."
        )
        p1, p2 = st.columns([1, 1])
        with p1:
            st.markdown(f"**Endpoint API :** `{api_base}/metrics`")
            st.link_button(
                "Ouvrir /metrics dans le navigateur", f"{api_base}/metrics", type="secondary"
            )
        with p2:
            st.markdown(f"**UI Prometheus :** `{prometheus_url}`")
            st.link_button("Ouvrir Prometheus", prometheus_url, type="secondary")
        try:
            r = requests.get(f"{api_base}/metrics", timeout=5)
            if r.ok:
                lines = [ln for ln in r.text.splitlines() if ln and not ln.startswith("#")][:80]
                with st.expander("Métriques brutes Prometheus (extrait)", expanded=False):
                    st.code("\n".join(lines), language="text")
            else:
                st.caption("Métriques indisponibles (API arrêtée ou erreur).")
        except Exception:
            st.caption("Métriques indisponibles (API arrêtée).")

        st.divider()

        # ---- Grafana ----
        st.subheader("Grafana")
        st.caption(
            "Tableaux de bord : configurez une source de données Prometheus pointant vers l'API ou le serveur Prometheus."
        )
        st.markdown(f"**URL :** {grafana_url}")
        st.link_button("Ouvrir Grafana", grafana_url, type="secondary")
        st.info(
            "**Si « Ce site est inaccessible » / ERR_CONNECTION_REFUSED :** Grafana n'est pas démarré. À la racine du projet, lancez **start_grafana.bat** (Docker requis), attendez 10 s, puis réessayez. Voir monitoring/README_GRAFANA.md."
        )
        st.caption(
            "Dans Grafana : Configuration → Data sources → Add Prometheus → URL = "
            + f"`http://localhost:{settings.prometheus_port}` ou `{api_base}` selon votre setup."
        )
        with st.expander("Comment connecter Grafana et voir les courbes de drift"):
            st.markdown("Voir **monitoring/README_GRAFANA.md** pour le guide pas à pas.")
            st.caption(
                "1) Démarrer Prometheus avec monitoring/prometheus.local.yml. 2) Démarrer Grafana, ajouter la source Prometheus (localhost:9090). 3) Importer le dashboard monitoring/grafana/dashboards/datasens-full.json. 4) Cliquer ci‑dessous pour mettre à jour les métriques de drift, puis regarder les courbes dans Grafana."
            )

        # Bouton pour mettre à jour les gauges de drift (Prometheus les scrape, Grafana affiche les courbes)
        drift_url = f"{api_v1}/analytics/drift-metrics"
        if st.button("Rafraîchir les métriques de drift (pour Grafana)"):
            try:
                r = requests.get(drift_url, timeout=30)
                if r.ok:
                    d = r.json()
                    st.success(
                        f"Drift mis à jour : {d.get('articles_total', 0)} articles, score={d.get('drift_score', 0):.3f}. Prometheus va scraper ces valeurs ; rafraîchissez le dashboard Grafana."
                    )
                else:
                    st.warning(
                        f"API a répondu {r.status_code}. Si 401 : authentification requise (token)."
                    )
            except requests.exceptions.ConnectionError:
                st.warning("API non démarrée.")
            except Exception as e:
                st.error(str(e)[:200])

        st.divider()

        # ---- Métriques IA (pilotage modèle) ----
        st.subheader("Métriques IA – pilotage du modèle")
        st.caption(
            "Indicateurs calculés depuis les données GOLD/GoldAI pour améliorer le modèle (déséquilibres, confiance, volume)."
        )
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

            st.info(
                "**Pour améliorer le modèle :** surveillez le déséquilibre sentiment/topics et le volume par source. "
                "Le sentiment actuel (pipeline) est basé sur des **mots-clés** ; pour de meilleures perfs, fine-tunez "
                "**CamemBERT/FlauBERT** sur la copie IA (dataset amélioré = équilibre, nettoyage, split train/val/test). "
                "Voir **docs/SENTIMENT_ET_FINETUNING.md**."
            )

        st.divider()
        st.subheader("Endpoints API")
        st.code(
            f"{api_base}/health\n{api_base}/metrics\n{api_v1}/ai/predict\n{api_v1}/analytics/statistics",
            language="text",
        )

    with tab_chrono:
        st.header("Vue chronologique")
        df_chrono = _chrono_data(PROJECT_ROOT)
        if df_chrono.empty:
            st.info("Aucune donnée par date (gold/silver/goldai avec partitions date=).")
        else:
            df_chrono = df_chrono.sort_values("date")
            st.caption("Fichiers et taille par date et par étape")
            col_c, col_s = st.columns(2)
            with col_c:
                pivot_c = df_chrono.pivot(index="date", columns="stage", values="count").fillna(0)
                if not pivot_c.empty:
                    st.line_chart(pivot_c)
            with col_s:
                pivot_s = df_chrono.pivot(index="date", columns="stage", values="size").fillna(0)
                if not pivot_s.empty:
                    st.line_chart(pivot_s)
            with st.expander("Donnees brutes"):
                st.dataframe(df_chrono)

    with tab_ia:
        st.header("Assistant IA – Insights")
        st.caption(
            "Posez des questions par theme : utilisateurs, financier ou politique. "
            "Style fenetre chat."
        )
        api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
        api_v1 = f"{api_base}{settings.api_v1_prefix}"
        if "ia_chat_messages" not in st.session_state:
            st.session_state.ia_chat_messages = []
        theme_options = {
            "Utilisateurs": "utilisateurs",
            "Financier": "financier",
            "Politique": "politique",
        }
        selected_label = st.selectbox(
            "Type d'insight",
            list(theme_options.keys()),
            key="ia_theme_select",
        )
        theme = theme_options[selected_label]
        if st.button("Effacer l'historique", key="ia_clear_chat"):
            st.session_state.ia_chat_messages = []
            st.rerun()
        for msg in st.session_state.ia_chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        prompt = st.chat_input("Votre question (insights)...")
        if prompt:
            st.session_state.ia_chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Reponse..."):
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
                        if r.status_code == 200:
                            data = r.json()
                            reply = data.get("reply", "Pas de reponse.")
                        else:
                            reply = f"Erreur API {r.status_code}: {(r.text or '')[:300]}"
                    except requests.exceptions.ConnectionError:
                        reply = "API non disponible. Demarrez l'API E2 (onglet Pilotage)."
                    except Exception as e:
                        reply = f"Erreur: {str(e)[:200]}"
                    st.write(reply)
            st.session_state.ia_chat_messages.append({"role": "assistant", "content": reply})
            st.rerun()


if __name__ == "__main__":
    main()
