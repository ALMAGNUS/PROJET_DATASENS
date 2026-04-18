"""Preuve d'enrichissement du pipeline de données (audit / traçabilité).

Surface, en un seul panneau, les lignes ajoutées à chaque étape entre le
rapport `db_state` précédent et le courant : SQLite raw_data, GOLD du jour,
GoldAI, splits IA, prédictions, Mongo (sync_log).

Fournit aussi :
- une timeline de croissance (raw_data + goldai) lue dans tous les reports,
- un bouton d'export MD+CSV horodaté dans `reports/` pour archive d'audit.

Deux rendus :
- `render_last_run_proof_full(ctx)`   : bloc complet (onglet Pipeline).
- `render_last_run_proof_compact(ctx)`: résumé 5 metrics (onglet Vue d'ensemble).
"""

from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
    parquet_row_count_cached,
)


# ---------------------------------------------------------------------------
# Chargement et parsing des rapports db_state
# ---------------------------------------------------------------------------


def _load_all_db_state_reports(root: Path) -> list[dict[str, Any]]:
    """Charge tous les rapports db_state_*.json triés par date (ancien -> récent)."""
    rep = root / "reports"
    if not rep.exists():
        return []
    reports: list[dict[str, Any]] = []
    for p in sorted(rep.glob("db_state_*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["_file"] = p.name
            data["_mtime"] = p.stat().st_mtime
            reports.append(data)
        except Exception:
            continue
    return reports


def _get_db_path() -> Path | None:
    """Résolution du fichier SQLite, cohérente avec overview.py."""
    cand = os.getenv("DB_PATH")
    if cand and Path(cand).exists():
        return Path(cand)
    default_db = Path.home() / "datasens_project" / "datasens.db"
    if default_db.exists():
        return default_db
    return None


# ---------------------------------------------------------------------------
# Calcul des deltas par étape
# ---------------------------------------------------------------------------


@dataclass
class StageDelta:
    stage: str
    before: int
    after: int
    delta: int
    path_hint: str = ""
    detail: str = ""


@dataclass
class LastRunProof:
    previous_report_file: str = ""
    latest_report_file: str = ""
    previous_generated_at: str = ""
    latest_generated_at: str = ""
    stages: list[StageDelta] = field(default_factory=list)
    source_deltas: list[dict[str, Any]] = field(default_factory=list)
    sync_log_last_session: list[dict[str, Any]] = field(default_factory=list)
    coherence_status: str = "—"
    previous_raw_max_id: int = 0
    latest_raw_max_id: int = 0
    latest_gold_date: str = ""


def compute_last_run_deltas(root: Path) -> LastRunProof | None:
    """Construit la preuve structurée du dernier run à partir des 2 derniers reports."""
    reports = _load_all_db_state_reports(root)
    if not reports:
        return None
    latest = reports[-1]
    previous = reports[-2] if len(reports) >= 2 else None

    proof = LastRunProof(
        latest_report_file=latest.get("_file", ""),
        previous_report_file=previous.get("_file", "") if previous else "",
        latest_generated_at=latest.get("meta", {}).get("generated_at_utc", ""),
        previous_generated_at=(
            previous.get("meta", {}).get("generated_at_utc", "") if previous else ""
        ),
        coherence_status=latest.get("coherence_checks", {}).get("status", "—"),
        latest_raw_max_id=int(latest.get("raw_data", {}).get("max_id", 0) or 0),
        previous_raw_max_id=int(
            (previous or {}).get("raw_data", {}).get("max_id", 0) or 0
        ),
    )

    # Stage 1 - SQLite raw_data (compte buffer)
    latest_raw = int(latest.get("raw_data", {}).get("total_rows", 0) or 0)
    prev_raw = int((previous or {}).get("raw_data", {}).get("total_rows", 0) or 0)
    proof.stages.append(
        StageDelta(
            stage="1. SQLite raw_data (buffer)",
            before=prev_raw,
            after=latest_raw,
            delta=latest_raw - prev_raw,
            path_hint="datasens.db · table raw_data",
            detail="Ingestion + dédup fingerprint. Source de vérité buffer.",
        )
    )

    # Stage 2 - GOLD du jour (partition du dernier merge)
    # L'export GOLD est régénéré à chaque run (dump complet enrichi), donc la bonne
    # mesure d'enrichissement est le nombre de lignes neuves intégrées via raw_data :
    # elles passent par le tagging + sentiment_keyword avant d'atterrir dans le GOLD.
    gold_date = latest.get("goldai_metadata", {}).get("last_date_merged", "") or ""
    proof.latest_gold_date = gold_date
    gold_file = root / "data" / "gold" / f"date={gold_date}" / "articles.parquet"
    gold_rows_now = (
        parquet_row_count_cached(str(gold_file)) if gold_file.exists() else 0
    )
    raw_delta = latest_raw - prev_raw
    gold_before = max(0, gold_rows_now - raw_delta) if gold_rows_now else 0
    proof.stages.append(
        StageDelta(
            stage="2. GOLD partition (jour, export enrichi)",
            before=gold_before,
            after=gold_rows_now,
            delta=raw_delta,
            path_hint=f"data/gold/date={gold_date or '?'}/articles.parquet",
            detail=(
                "Export parquet régénéré (sentiment_keyword + topics). "
                f"Delta = nouvelles lignes raw_data enrichies ce run ({raw_delta:+,})."
            ),
        )
    )

    # Stage 3 - GoldAI fusion long terme
    latest_goldai = int(
        latest.get("goldai_metadata", {}).get("total_rows", 0) or 0
    )
    prev_goldai = int(
        (previous or {}).get("goldai_metadata", {}).get("total_rows", 0) or 0
    )
    proof.stages.append(
        StageDelta(
            stage="3. GoldAI fusion long terme",
            before=prev_goldai,
            after=latest_goldai,
            delta=latest_goldai - prev_goldai,
            path_hint="data/goldai/merged_all_dates.parquet",
            detail="Stock long terme dédupliqué par id.",
        )
    )

    # Stage 4 - IA splits (train + val + test)
    ia_prev = (previous or {}).get("ia_artifacts", {}) if previous else {}
    ia_latest = latest.get("ia_artifacts", {})
    split_prev = int(
        (ia_prev.get("goldai_ia_train_rows", 0) or 0)
        + (ia_prev.get("goldai_ia_val_rows", 0) or 0)
        + (ia_prev.get("goldai_ia_test_rows", 0) or 0)
    )
    split_latest = int(
        (ia_latest.get("goldai_ia_train_rows", 0) or 0)
        + (ia_latest.get("goldai_ia_val_rows", 0) or 0)
        + (ia_latest.get("goldai_ia_test_rows", 0) or 0)
    )
    proof.stages.append(
        StageDelta(
            stage="4. IA splits (train+val+test)",
            before=split_prev,
            after=split_latest,
            delta=split_latest - split_prev,
            path_hint="data/goldai/ia/{train,val,test}.parquet",
            detail=(
                f"train={ia_latest.get('goldai_ia_train_rows', 0):,} · "
                f"val={ia_latest.get('goldai_ia_val_rows', 0):,} · "
                f"test={ia_latest.get('goldai_ia_test_rows', 0):,}"
            ),
        )
    )

    # Stage 5 - Mongo long terme : somme rows_synced sur la session la plus récente.
    # On agrège les lignes de sync_log_recent dont le sync_date >= mtime du report précédent.
    sync_log = latest.get("sync_log_recent", [])
    cutoff_iso = proof.previous_generated_at or ""
    mongo_sum = 0
    last_session: list[dict[str, Any]] = []
    for row in sync_log:
        sd = row.get("sync_date", "")
        if cutoff_iso and sd < cutoff_iso:
            continue
        if row.get("status") != "OK":
            continue
        rows = int(row.get("rows_synced", 0) or 0)
        mongo_sum += rows
        last_session.append(row)
    proof.sync_log_last_session = last_session
    proof.stages.append(
        StageDelta(
            stage="5. MongoDB (transferts)",
            before=0,
            after=mongo_sum,
            delta=mongo_sum,
            path_hint="MongoDB · sync_log (rows_synced, status=OK)",
            detail=(
                f"{len(last_session)} synchronisations OK "
                f"entre les deux rapports (depuis {cutoff_iso or 'N/A'})."
            ),
        )
    )

    # Deltas par source (déjà calculés côté db_state_report.py)
    proof.source_deltas = list(
        latest.get("run_progress", {}).get("source_deltas_since_previous_report", [])
        or []
    )

    return proof


# ---------------------------------------------------------------------------
# Extraction des lignes nouvelles réelles (pour inspection cockpit)
# ---------------------------------------------------------------------------


def fetch_new_raw_rows(
    db_path: Path, previous_max_id: int, limit: int = 50
) -> tuple[pd.DataFrame | None, str | None]:
    """Lit les lignes SQLite `raw_data` dont l'id > previous_max_id.

    Retourne (DataFrame, None) si OK, sinon (None, message d'erreur).
    Fait un LEFT JOIN sur la table `source` pour avoir le nom lisible.
    """
    if not db_path or not db_path.exists():
        return None, f"Base SQLite introuvable : {db_path}"
    try:
        conn = sqlite3.connect(str(db_path))
        q = (
            "SELECT r.raw_data_id, s.name AS source, r.title, r.url, r.collected_at "
            "FROM raw_data r LEFT JOIN source s ON r.source_id = s.source_id "
            "WHERE r.raw_data_id > ? "
            "ORDER BY r.raw_data_id ASC LIMIT ?"
        )
        df = pd.read_sql_query(q, conn, params=(previous_max_id, limit))
        conn.close()
        return df, None
    except Exception as exc:
        return None, f"Erreur SQLite : {type(exc).__name__} — {exc}"


def fetch_gold_partition_rows(
    root: Path, gold_date: str, limit: int = 50
) -> pd.DataFrame | None:
    """Retourne un échantillon de la partition GOLD du jour (les lignes enrichies)."""
    if not gold_date:
        return None
    gfile = root / "data" / "gold" / f"date={gold_date}" / "articles.parquet"
    if not gfile.exists():
        return None
    try:
        df = pd.read_parquet(gfile)
        cols = [
            c
            for c in ["id", "source", "title", "sentiment", "topic_1", "topic_2", "collected_at"]
            if c in df.columns
        ]
        view = df[cols] if cols else df
        return view.head(limit)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Timeline de croissance
# ---------------------------------------------------------------------------


def build_growth_timeline(root: Path) -> pd.DataFrame:
    """DataFrame [timestamp, raw_data, goldai, ia_splits] depuis tous les reports."""
    reports = _load_all_db_state_reports(root)
    rows: list[dict[str, Any]] = []
    for r in reports:
        ts = r.get("meta", {}).get("generated_at_utc", "")
        raw = int(r.get("raw_data", {}).get("total_rows", 0) or 0)
        goldai = int(r.get("goldai_metadata", {}).get("total_rows", 0) or 0)
        ia = r.get("ia_artifacts", {})
        ia_total = int(
            (ia.get("goldai_ia_train_rows", 0) or 0)
            + (ia.get("goldai_ia_val_rows", 0) or 0)
            + (ia.get("goldai_ia_test_rows", 0) or 0)
        )
        if ts:
            rows.append(
                {
                    "date": ts[:10],
                    "raw_data": raw,
                    "goldai": goldai,
                    "ia_splits": ia_total,
                }
            )
    if not rows:
        return pd.DataFrame(columns=["date", "raw_data", "goldai", "ia_splits"])
    df = pd.DataFrame(rows).drop_duplicates(subset="date", keep="last")
    return df.set_index("date").sort_index()


# ---------------------------------------------------------------------------
# Export preuve d'enrichissement (MD + CSV)
# ---------------------------------------------------------------------------


def build_export_bytes(proof: LastRunProof) -> tuple[bytes, bytes, str]:
    """Construit (md_bytes, csv_bytes, stem) à partir d'une LastRunProof."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    stem = f"pipeline_proof_{ts}"

    # CSV (lignes tabulaires par étape)
    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow(["stage", "before", "after", "delta", "path_hint", "detail"])
    for s in proof.stages:
        writer.writerow([s.stage, s.before, s.after, s.delta, s.path_hint, s.detail])
    csv_bytes = csv_buf.getvalue().encode("utf-8")

    # Markdown
    lines = [
        "# Preuve d'enrichissement du pipeline DataSens",
        "",
        f"- Généré (UTC) : `{ts}`",
        f"- Rapport courant : `{proof.latest_report_file}` (`{proof.latest_generated_at}`)",
        f"- Rapport précédent : `{proof.previous_report_file or 'aucun'}` "
        f"(`{proof.previous_generated_at or '—'}`)",
        f"- Cohérence technique : **{proof.coherence_status}**",
        "",
        "## Lignes ajoutées par étape",
        "",
        "| Étape | Avant | Après | Delta | Chemin | Détail |",
        "|---|---:|---:|---:|---|---|",
    ]
    for s in proof.stages:
        sign = f"+{s.delta:,}" if s.delta >= 0 else f"{s.delta:,}"
        lines.append(
            f"| {s.stage} | {s.before:,} | {s.after:,} | **{sign}** | "
            f"`{s.path_hint}` | {s.detail} |"
        )
    if proof.source_deltas:
        lines += [
            "",
            "## Deltas par source (raw_data)",
            "",
            "| Source | Delta | Total courant |",
            "|---|---:|---:|",
        ]
        for row in proof.source_deltas:
            lines.append(
                f"| `{row.get('source', '?')}` | "
                f"+{int(row.get('delta', 0)):,} | "
                f"{int(row.get('current', 0)):,} |"
            )
    md_bytes = "\n".join(lines).encode("utf-8")
    return md_bytes, csv_bytes, stem


def write_export_files(root: Path, proof: LastRunProof) -> tuple[Path, Path]:
    """Écrit les fichiers MD/CSV sur disque dans reports/ et retourne les chemins."""
    md_bytes, csv_bytes, stem = build_export_bytes(proof)
    out_dir = root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{stem}.md"
    csv_path = out_dir / f"{stem}.csv"
    md_path.write_bytes(md_bytes)
    csv_path.write_bytes(csv_bytes)
    return md_path, csv_path


# ---------------------------------------------------------------------------
# Rendus Streamlit
# ---------------------------------------------------------------------------


def _format_delta(delta: int) -> str:
    if delta > 0:
        return f"+{delta:,} lignes"
    if delta < 0:
        return f"{delta:,} lignes"
    return "0"


def render_last_run_proof_compact(ctx: PageContext) -> None:
    """Rendu condensé pour l'onglet Vue d'ensemble."""
    proof = compute_last_run_deltas(ctx.project_root)
    st.markdown("#### Dernier run — enrichissement prouvé")
    if not proof or not proof.stages:
        st.info(
            "Aucun rapport `db_state` trouvé. Lancez le pipeline E1 "
            "(onglet **Pilotage** → bouton Pipeline) pour produire la preuve."
        )
        return
    if not proof.previous_report_file:
        st.warning(
            "Un seul rapport db_state disponible : delta non calculable. "
            "Relancez le pipeline pour obtenir une comparaison."
        )
    cols = st.columns(len(proof.stages))
    for col, s in zip(cols, proof.stages):
        label = s.stage.split(". ", 1)[-1]
        col.metric(label, f"{s.after:,}", delta=_format_delta(s.delta))
    st.caption(
        f"Cohérence : **{proof.coherence_status}** · "
        f"Rapport courant : `{proof.latest_report_file}` · "
        f"Précédent : `{proof.previous_report_file or '—'}` · "
        "Détail complet dans l'onglet **Pipeline**."
    )


def render_last_run_proof_full(ctx: PageContext) -> None:
    """Rendu complet pour l'onglet Pipeline."""
    root = ctx.project_root
    st.markdown("### Dernier run — enrichissement prouvé par étape")
    st.caption(
        "Comparaison entre les deux derniers rapports `reports/db_state_*.json`. "
        "Chaque étape affiche les lignes **avant**, **après** et le **delta** ajouté "
        "par l'exécution. Les lignes elles-mêmes sont visibles ci-dessous."
    )
    proof = compute_last_run_deltas(root)
    if not proof or not proof.stages:
        st.info(
            "Aucun rapport `db_state` trouvé. Lancez le pipeline E1 "
            "pour produire la preuve, puis revenez ici."
        )
        return

    # En-tête : dates des rapports comparés
    hdr1, hdr2, hdr3 = st.columns(3)
    hdr1.caption(f"**Rapport courant** : `{proof.latest_report_file}`")
    hdr1.caption(f"{proof.latest_generated_at}")
    hdr2.caption(
        f"**Rapport précédent** : `{proof.previous_report_file or 'aucun'}`"
    )
    hdr2.caption(f"{proof.previous_generated_at or '—'}")
    status_emoji = (
        "✅" if proof.coherence_status == "OK"
        else "⚠️" if proof.coherence_status == "WARNING"
        else "❌" if proof.coherence_status == "ERROR"
        else "•"
    )
    hdr3.caption(f"**Cohérence** : {status_emoji} {proof.coherence_status}")
    hdr3.caption(f"Partition GOLD : `{proof.latest_gold_date or '—'}`")

    # Metrics (5 étapes)
    cols = st.columns(len(proof.stages))
    for col, s in zip(cols, proof.stages):
        label = s.stage.split(". ", 1)[-1]
        col.metric(label, f"{s.after:,}", delta=_format_delta(s.delta))

    # Tableau de preuve détaillé
    proof_df = pd.DataFrame(
        [
            {
                "Étape": s.stage,
                "Avant": s.before,
                "Après": s.after,
                "Delta": s.delta,
                "Chemin / source": s.path_hint,
                "Détail": s.detail,
            }
            for s in proof.stages
        ]
    )
    st.dataframe(proof_df, use_container_width=True, hide_index=True)

    # Deltas par source (si dispo)
    if proof.source_deltas:
        with st.expander(
            f"Deltas par source raw_data ({len(proof.source_deltas)} sources)",
            expanded=False,
        ):
            src_df = pd.DataFrame(proof.source_deltas)
            if not src_df.empty:
                src_df = src_df.rename(
                    columns={"source": "Source", "delta": "Delta", "current": "Total courant"}
                )
                st.dataframe(src_df, use_container_width=True, hide_index=True)

    # Lignes nouvelles réelles — SQLite et GOLD
    st.markdown("#### Lignes nouvelles réelles")
    tab_sql, tab_gold, tab_sync, tab_timeline = st.tabs(
        [
            "Nouvelles lignes SQLite",
            "Partition GOLD du jour",
            "Mongo sync_log (session)",
            "Timeline de croissance",
        ]
    )

    with tab_sql:
        db_path = _get_db_path()
        if db_path is None:
            st.info("Base SQLite introuvable (DB_PATH non défini et default absent).")
        elif proof.latest_raw_max_id <= proof.previous_raw_max_id:
            st.info(
                "Aucune nouvelle ligne SQLite détectée entre les deux rapports "
                f"(max_id {proof.previous_raw_max_id:,} → {proof.latest_raw_max_id:,})."
            )
        else:
            df_new, err = fetch_new_raw_rows(
                db_path, proof.previous_raw_max_id, limit=200
            )
            if err:
                st.error(err)
            elif df_new is None or df_new.empty:
                st.info(
                    "Aucune ligne lue (raw_data_id > "
                    f"{proof.previous_raw_max_id:,})."
                )
            else:
                st.success(
                    f"**{len(df_new):,}** nouvelles lignes affichées "
                    f"(raw_data_id > {proof.previous_raw_max_id:,})."
                )
                st.dataframe(df_new, use_container_width=True, height=320)

    with tab_gold:
        df_gold = fetch_gold_partition_rows(
            root, proof.latest_gold_date, limit=200
        )
        if df_gold is None or df_gold.empty:
            st.info(
                f"Partition GOLD introuvable ou vide : "
                f"data/gold/date={proof.latest_gold_date}/articles.parquet"
            )
        else:
            st.success(
                f"Partition `date={proof.latest_gold_date}` — "
                f"{len(df_gold):,} lignes affichées (échantillon)."
            )
            st.dataframe(df_gold, use_container_width=True, height=320)

    with tab_sync:
        if proof.sync_log_last_session:
            sync_df = pd.DataFrame(proof.sync_log_last_session)
            st.success(
                f"{len(sync_df):,} synchronisations OK depuis le rapport précédent "
                f"(total : **{int(sync_df['rows_synced'].sum()):,}** lignes synchronisées)."
            )
            st.dataframe(sync_df, use_container_width=True, height=320)
        else:
            st.info("Pas de sync_log récent depuis le dernier rapport.")

    with tab_timeline:
        tl = build_growth_timeline(root)
        if tl.empty:
            st.info("Pas d'historique de reports db_state disponible.")
        else:
            st.caption(
                f"Croissance du dataset sur **{len(tl)}** rapports historisés "
                f"(de {tl.index.min()} à {tl.index.max()})."
            )
            st.line_chart(tl, use_container_width=True)
            with st.expander("Données brutes de la timeline", expanded=False):
                st.dataframe(tl, use_container_width=True)

    # Export MD/CSV
    st.markdown("#### Export de la preuve d'enrichissement")
    st.caption(
        "Génère un rapport d'audit horodaté (Markdown + CSV) reprenant les deltas "
        "ci-dessus, pour archivage projet ou annexe de documentation technique."
    )
    md_bytes, csv_bytes, stem = build_export_bytes(proof)
    ex1, ex2, ex3 = st.columns([1, 1, 2])
    with ex1:
        st.download_button(
            "Télécharger MD",
            data=md_bytes,
            file_name=f"{stem}.md",
            mime="text/markdown",
            use_container_width=True,
            key="dl_proof_md",
        )
    with ex2:
        st.download_button(
            "Télécharger CSV",
            data=csv_bytes,
            file_name=f"{stem}.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_proof_csv",
        )
    with ex3:
        if st.button(
            "Sauvegarder aussi dans reports/",
            use_container_width=True,
            help="Écrit le même MD+CSV dans reports/ pour tracer la preuve côté projet.",
            key="save_proof_to_reports",
        ):
            md_path, csv_path = write_export_files(root, proof)
            st.success(
                f"Écrit :\n- `{md_path.relative_to(root)}`\n- `{csv_path.relative_to(root)}`"
            )
