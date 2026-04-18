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
from datetime import date, datetime, timedelta, timezone
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


# ---------------------------------------------------------------------------
# The Cockpit Show : un article traversant RAW -> SILVER -> GOLD -> GoldAI
# ---------------------------------------------------------------------------


def _fetch_article_samples(
    root: Path, fallback_days: int = 14
) -> tuple[list[dict[str, Any]], str]:
    """Récupère un échantillon d'articles avec leurs enrichissements.

    Essaie d'abord aujourd'hui, puis remonte jusqu'à `fallback_days` jours en
    arrière jusqu'à trouver des données. Retourne (samples, date_utilisée).
    """
    from src.observability.lineage_service import LineageService

    db_path = _get_db_path()
    if db_path is None or not db_path.exists():
        return [], ""

    service = LineageService(db_path=str(db_path), project_root=root)
    today = date.today()
    for delta in range(fallback_days + 1):
        target = today - timedelta(days=delta)
        try:
            payload = service.get_daily_lineage(target_date=target)
        except Exception:
            continue
        samples = payload.get("transformed_samples_today") or []
        if samples:
            return samples, target.isoformat()
    return [], ""


def _html_escape(txt: str) -> str:
    """Échappe le HTML pour injection sûre dans st.markdown(unsafe_allow_html=True)."""
    return (
        txt.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _sentiment_style(label: str) -> tuple[str, str, str]:
    """Retourne (bg, fg, border) pour un sentiment FR."""
    palette = {
        "positif": ("#e8f5e9", "#2e7d32", "#66bb6a"),
        "neutre": ("#eceff1", "#455a64", "#90a4ae"),
        "negatif": ("#ffebee", "#c62828", "#ef5350"),
        "négatif": ("#ffebee", "#c62828", "#ef5350"),
    }
    return palette.get(label.lower(), ("#eceff1", "#455a64", "#90a4ae"))


# CSS injecté une seule fois pour styliser les cartes du show.
_SHOW_CSS = """
<style>
.ds-show-wrap {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr;
  align-items: stretch;
  gap: 0;
  margin: 8px 0 4px 0;
}
.ds-show-card {
  background: #ffffff;
  border: 1px solid #e0e4ea;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  min-height: 340px;
  overflow: hidden;
}
.ds-show-card__head {
  padding: 10px 14px;
  color: #ffffff;
  font-weight: 600;
  letter-spacing: 0.3px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}
.ds-show-card__head .ds-step {
  font-size: 0.72rem;
  text-transform: uppercase;
  opacity: 0.85;
  letter-spacing: 1px;
}
.ds-show-card__head .ds-name {
  font-size: 1.0rem;
}
.ds-show-card__subhead {
  padding: 6px 14px;
  background: #fafbfc;
  border-bottom: 1px solid #eef1f5;
  font-size: 0.78rem;
  color: #5a6774;
  font-style: italic;
}
.ds-show-card__body {
  padding: 12px 14px;
  flex: 1 1 auto;
  font-size: 0.87rem;
  color: #1f2937;
}
.ds-show-card__body .ds-meta {
  color: #6b7684;
  font-size: 0.78rem;
  margin-bottom: 6px;
}
.ds-show-card__body .ds-headline {
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.35;
  color: #111827;
}
.ds-show-card__body .ds-snippet {
  color: #4b5563;
  font-size: 0.82rem;
  line-height: 1.4;
  margin-bottom: 8px;
}
.ds-show-card__body .ds-link {
  font-size: 0.8rem;
}
.ds-show-card__body .ds-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.85rem;
  margin: 2px 6px 2px 0;
  border: 1px solid transparent;
}
.ds-show-card__body .ds-badge--topic {
  background: #ede7f6;
  color: #4527a0;
  border-color: #b39ddb;
}
.ds-show-card__body .ds-badge--topic-secondary {
  background: #f3eefc;
  color: #6c4cb3;
  border-color: #d1c4e9;
  opacity: 0.9;
}
.ds-show-card__body .ds-label {
  text-transform: uppercase;
  color: #6b7684;
  font-size: 0.7rem;
  letter-spacing: 1px;
  margin-top: 10px;
  margin-bottom: 4px;
}
.ds-show-card__body .ds-score-big {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 1.4rem;
  color: #111827;
  letter-spacing: 0.5px;
  margin-top: 4px;
}
.ds-show-card__body .ds-empty {
  color: #9ca3af;
  font-style: italic;
  font-size: 0.82rem;
}
.ds-show-card__footer {
  padding: 8px 14px;
  background: #f7f9fb;
  border-top: 1px solid #eef1f5;
  font-size: 0.78rem;
  color: #3a8d6a;
  font-weight: 600;
}
.ds-show-card__footer.ds-footer--muted {
  color: #6b7684;
  font-weight: 500;
}
.ds-show-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  font-size: 1.3rem;
  font-weight: 700;
  color: #9ca3af;
  user-select: none;
}
@media (max-width: 1100px) {
  .ds-show-wrap {
    grid-template-columns: 1fr;
  }
  .ds-show-arrow {
    width: 100%;
    height: 20px;
    transform: rotate(90deg);
  }
  .ds-show-card {
    min-height: 0;
  }
}
</style>
"""


def render_article_journey(ctx: PageContext) -> None:
    """THE COCKPIT SHOW — suivi visuel d'un article dans le pipeline.

    Quatre cartes visuelles côte à côte (RAW → SILVER → GOLD → GoldAI)
    montrent comment le même article est enrichi à chaque étape :
    brut → topics → sentiment → stock long terme.
    """
    root = ctx.project_root
    samples, used_date = _fetch_article_samples(root)

    st.markdown("### Le parcours d'un article — enrichissement visible étape par étape")
    if not samples:
        st.info(
            "Aucun article récent dans la base SQLite. Lancez le pipeline E1 "
            "(onglet **Pilotage** → **Pipeline E1**) pour déclencher "
            "l'ingestion, puis revenez ici."
        )
        return

    today_iso = date.today().isoformat()
    if used_date == today_iso:
        st.caption(
            f"**{len(samples)}** articles ingérés aujourd'hui ({used_date}). "
            "Choisissez-en un et suivez son trajet : "
            "**brut** → **topics** → **sentiment** → **archivé**."
        )
    else:
        st.caption(
            f"Aucune ingestion aujourd'hui. Affichage des **{len(samples)}** "
            f"articles du dernier jour actif (**{used_date}**)."
        )

    labels = []
    for r in samples:
        src = str(r.get("source") or "?")
        title = str(r.get("title") or "Sans titre").strip()
        labels.append(f"#{r.get('id')} · {src} · {title[:70]}")
    pick = st.selectbox(
        "Article à suivre",
        labels,
        index=0,
        key="pipeline_article_pick",
        label_visibility="collapsed",
    )
    chosen = samples[labels.index(pick)]

    art_id = chosen.get("id")
    source = str(chosen.get("source") or "?")
    title = str(chosen.get("title") or "")
    content = str(chosen.get("content") or "")
    url = str(chosen.get("url") or "")
    topic_1 = str(chosen.get("topic_1") or "")
    topic_2 = str(chosen.get("topic_2") or "")
    sentiment = str(chosen.get("sentiment") or "")
    score = chosen.get("sentiment_score")
    collected_at = str(chosen.get("collected_at") or "")

    # Formattage soft de la date (YYYY-MM-DDTHH:MM:SS.fff -> JJ/MM HH:MM)
    collected_short = ""
    if collected_at:
        try:
            dt = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
            collected_short = dt.strftime("%d/%m %H:%M")
        except Exception:
            collected_short = collected_at[:16]

    # Preview contenu tronqué proprement
    snippet = ""
    if content:
        snip = content.strip()
        if len(snip) > 220:
            snip = snip[:220].rstrip() + "…"
        snippet = snip

    # Couleurs par étape (bandeau head)
    accents = {
        "raw": "#546e7a",      # ardoise
        "silver": "#7e57c2",   # violet
        "gold": "#f9a825",     # doré
        "goldai": "#26a69a",   # turquoise
    }

    # RAW card body
    raw_meta = f"ID <b>#{art_id}</b> · Source <code>{_html_escape(source)}</code>"
    if collected_short:
        raw_meta += f" · {collected_short}"
    raw_headline = _html_escape(title) if title else "<i>(sans titre)</i>"
    raw_snippet = (
        f"<div class='ds-snippet'>{_html_escape(snippet)}</div>" if snippet else ""
    )
    raw_link = (
        f"<div class='ds-link'><a href='{_html_escape(url)}' target='_blank' "
        f"rel='noopener'>Source ↗</a></div>"
        if url.startswith("http")
        else ""
    )
    raw_body = (
        f"<div class='ds-meta'>{raw_meta}</div>"
        f"<div class='ds-headline'>{raw_headline}</div>"
        f"{raw_snippet}"
        f"{raw_link}"
    )

    # SILVER card body
    topic1_html = (
        f"<span class='ds-badge ds-badge--topic'>{_html_escape(topic_1)}</span>"
        if topic_1
        else "<span class='ds-empty'>non déterminé</span>"
    )
    topic2_html = (
        f"<span class='ds-badge ds-badge--topic-secondary'>{_html_escape(topic_2)}</span>"
        if topic_2
        else "<span class='ds-empty'>aucun</span>"
    )
    silver_body = (
        "<div class='ds-label'>Thème principal</div>"
        f"<div>{topic1_html}</div>"
        "<div class='ds-label'>Thème secondaire</div>"
        f"<div>{topic2_html}</div>"
    )
    silver_footer = (
        "+ 2 colonnes : <code>topic_1</code>, <code>topic_2</code>"
        if topic_1 or topic_2
        else "Tagger à relancer"
    )
    silver_footer_muted = not (topic_1 or topic_2)

    # GOLD card body
    try:
        score_val = float(score) if score is not None else None
    except Exception:
        score_val = None
    if sentiment:
        s_bg, s_fg, s_border = _sentiment_style(sentiment)
        sentiment_html = (
            f"<span class='ds-badge' style='background:{s_bg};color:{s_fg};"
            f"border-color:{s_border}'>{_html_escape(sentiment)}</span>"
        )
    else:
        sentiment_html = "<span class='ds-empty'>en attente du scoring</span>"
    score_html = (
        f"<div class='ds-score-big'>{score_val:+.3f}</div>"
        if score_val is not None
        else "<div class='ds-empty'>—</div>"
    )
    gold_body = (
        "<div class='ds-label'>Sentiment</div>"
        f"<div>{sentiment_html}</div>"
        "<div class='ds-label'>Score de confiance</div>"
        f"{score_html}"
    )
    gold_footer = (
        "+ 2 colonnes : <code>sentiment</code>, <code>sentiment_score</code>"
        if sentiment
        else "Scoring à relancer"
    )
    gold_footer_muted = not sentiment

    # GoldAI card body
    goldai_path = root / "data" / "goldai" / "merged_all_dates.parquet"
    goldai_rows = (
        parquet_row_count_cached(str(goldai_path)) if goldai_path.exists() else 0
    )
    goldai_body = (
        "<div class='ds-label'>Identifiant de conservation</div>"
        f"<div class='ds-headline'><code>id = {art_id}</code></div>"
        "<div class='ds-label'>Stock consolidé</div>"
        f"<div class='ds-headline'>{goldai_rows:,} lignes</div>"
        "<div class='ds-meta' style='margin-top:10px'>"
        "Règle : <code>keep=&#39;last&#39;</code> sur <code>collected_at</code><br>"
        "Fichier : <code>data/goldai/merged_all_dates.parquet</code>"
        "</div>"
    )
    goldai_footer = "Alimente les splits IA (train / val / test)"

    # Assemblage
    def _card(step: str, name: str, accent: str, subhead: str, body: str,
              footer: str, muted: bool = False) -> str:
        muted_cls = " ds-footer--muted" if muted else ""
        return (
            "<div class='ds-show-card'>"
            f"<div class='ds-show-card__head' style='background:{accent}'>"
            f"<span class='ds-step'>{step}</span>"
            f"<span class='ds-name'>{name}</span>"
            "</div>"
            f"<div class='ds-show-card__subhead'>{subhead}</div>"
            f"<div class='ds-show-card__body'>{body}</div>"
            f"<div class='ds-show-card__footer{muted_cls}'>{footer}</div>"
            "</div>"
        )

    arrow = "<div class='ds-show-arrow'>→</div>"

    html = (
        _SHOW_CSS
        + "<div class='ds-show-wrap'>"
        + _card(
            "Étape 1",
            "RAW",
            accents["raw"],
            "Article brut tel que collecté",
            raw_body,
            "Texte non structuré",
            muted=True,
        )
        + arrow
        + _card(
            "Étape 2",
            "SILVER",
            accents["silver"],
            "Tagger lexical (titre ×3, seuil topic_2)",
            silver_body,
            silver_footer,
            muted=silver_footer_muted,
        )
        + arrow
        + _card(
            "Étape 3",
            "GOLD",
            accents["gold"],
            "Scoring IA (keyword ou fine-tuné)",
            gold_body,
            gold_footer,
            muted=gold_footer_muted,
        )
        + arrow
        + _card(
            "Étape 4",
            "GoldAI",
            accents["goldai"],
            "Fusion long terme dédupliquée par id",
            goldai_body,
            goldai_footer,
        )
        + "</div>"
    )

    st.markdown(html, unsafe_allow_html=True)
    st.caption(
        "La même ligne traverse les 4 étapes. À chaque étape, on **ajoute** "
        "des colonnes ; aucune donnée n'est perdue."
    )
