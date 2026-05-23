"""
Page cockpit : onglet pilotage.
Extrait depuis src/streamlit/app.py (phase C, audit 2026-04).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
)
from src.streamlit._cockpit_helpers import (
    launch_api_in_new_window as _launch_api_in_new_window,
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
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def render(ctx: PageContext) -> None:
    PROJECT_ROOT = ctx.project_root
    show_advanced = ctx.show_advanced

    if show_advanced:
        st.caption(
            "Actions opérationnelles : run pipeline, fusion, copie IA, API et backups."
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
        "**Vue d'ensemble** et **Pipeline** ; benchmark / fine-tuning dans **IA → Modèles**. "
        "Ici : lancer le pipeline, fusion, copie IA, API et backups."
    )
    # ── RBAC : seul un role writer/deleter/admin peut executer les pipelines ─
    may_run = can_write()
    may_admin = can_admin()
    if not may_run:
        st.warning(
            "Rôle `reader` : les actions d'exécution sont verrouillées. "
            "Seuls les rôles `writer`, `deleter` ou `admin` peuvent lancer les pipelines, backups et copies IA."
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
            "Copie IA (expérimental) : filtrer finance+politique+météo (peut biaiser l'entraînement)",
            value=False,
            key="copie_ia_topics",
        )
        if copie_ia_topics:
            st.warning(
                "Mode slice métier activé : utile pour test rapide, mais à éviter pour le modèle principal. "
                "Bonne pratique : entraîner global, puis filtrer au niveau des insights."
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
            help=("Rôle admin requis." if not may_admin else None),
        ):
            _launch_api_in_new_window()
    with b5:
        if st.button(
            "Backup MongoDB",
            use_container_width=True,
            disabled=not may_admin,
            help=(
                "Rôle admin requis."
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
            help=("Rôle writer/admin requis." if not may_run else None),
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

    with st.expander("Paramètres pipeline & Mongo (avancé)", expanded=False):
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
        if st.button("Lister Parquet MongoDB", disabled=not may_run):
            _run_command("mongo", [sys.executable, "scripts/list_mongo_parquet.py"])
