#!/usr/bin/env python3
"""
Rapport d'état complet de la base SQLite DataSens (JSON + Markdown).

Objectif:
- Expliquer clairement la croissance du dataset entre runs.
- Vérifier la cohérence DB <-> exports <-> GoldAI.
- Détecter les signaux d'anomalie (GoldAI figé, écarts de comptage, etc.).
"""
from __future__ import annotations

import csv
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Encodage console Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def _db_path() -> Path:
    p = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
    return Path(p).resolve()


def _safe_query(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list:
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    except sqlite3.Error:
        return []


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _count_csv_data_rows(csv_path: Path) -> int | None:
    """Compte les lignes de données via parsing CSV (robuste aux retours à la ligne)."""
    if not csv_path.exists():
        return None
    try:
        with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)  # header
            return sum(1 for _ in reader)
    except OSError:
        return None


def _goldai_raw_linkage(raw_ids: set[int]) -> dict:
    """
    Analyse la comparabilité GoldAI vs raw_data via `raw_data_id`.
    - Si beaucoup de lignes GoldAI n'ont pas `raw_data_id`, la comparaison brute
      `GoldAI total_rows - raw_data` n'est pas directement interprétable.
    """
    out = {
        "goldai_rows_total_parquet": None,
        "goldai_rows_with_raw_data_id": None,
        "goldai_rows_without_raw_data_id": None,
        "goldai_raw_id_in_db": None,
        "goldai_raw_id_not_in_db": None,
        "goldai_raw_link_coverage": None,
    }
    parquet_path = PROJECT_ROOT / "data" / "goldai" / "merged_all_dates.parquet"
    if not parquet_path.exists():
        return out
    try:
        import pyarrow.parquet as pq  # optionnel

        pf = pq.ParquetFile(parquet_path)
        total_rows = int(pf.metadata.num_rows)
        out["goldai_rows_total_parquet"] = total_rows
        table = pf.read(columns=["raw_data_id"])
        raw_vals = table.column("raw_data_id").to_pylist()
        with_id = [int(v) for v in raw_vals if v is not None]
        without_id = total_rows - len(with_id)
        in_db = sum(1 for v in with_id if v in raw_ids)
        not_in_db = len(with_id) - in_db
        out["goldai_rows_with_raw_data_id"] = len(with_id)
        out["goldai_rows_without_raw_data_id"] = without_id
        out["goldai_raw_id_in_db"] = in_db
        out["goldai_raw_id_not_in_db"] = not_in_db
        out["goldai_raw_link_coverage"] = (
            round(len(with_id) / total_rows, 6) if total_rows > 0 else None
        )
        return out
    except Exception:
        return out


def _latest_previous_report(current_base: Path) -> tuple[Path, dict] | None:
    candidates = sorted(REPORTS_DIR.glob("db_state_*.json"))
    prev = [p for p in candidates if p.resolve() != current_base.with_suffix(".json").resolve()]
    if not prev:
        return None
    picked = prev[-1]
    payload = _read_json(picked)
    if not payload:
        return None
    return picked, payload


def _by_source_map(by_source: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in by_source:
        name = str(row.get("source", ""))
        out[name] = int(row.get("articles", 0) or 0)
    return out


def collect_state(db_file: Path) -> dict:
    generated = datetime.now(timezone.utc).isoformat()
    if not db_file.exists():
        return {
            "meta": {
                "generated_at_utc": generated,
                "db_path": str(db_file),
                "error": "fichier introuvable",
            }
        }

    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    try:
        state: dict = {
            "meta": {
                "generated_at_utc": generated,
                "db_path": str(db_file),
                "db_size_bytes": db_file.stat().st_size,
            },
            "raw_data": {},
            "by_source": [],
            "enrichment": {},
            "data_quality": {},
            "sync_log_recent": [],
            "goldai_metadata": None,
            "exports_hint": {},
            "run_progress": {},
            "coherence_checks": {},
            "recommendations": [],
        }

        # RAW core
        row = _safe_query(conn, "SELECT COUNT(*), MIN(raw_data_id), MAX(raw_data_id) FROM raw_data")
        raw_ids_set: set[int] = set()
        if row:
            state["raw_data"] = {
                "total_rows": row[0][0],
                "min_id": row[0][1],
                "max_id": row[0][2],
            }
        raw_id_rows = _safe_query(conn, "SELECT raw_data_id FROM raw_data")
        raw_ids_set = {int(r[0]) for r in raw_id_rows if r and r[0] is not None}
        row = _safe_query(conn, "SELECT MIN(collected_at), MAX(collected_at) FROM raw_data")
        if row and row[0][0] is not None:
            state["raw_data"]["collected_at_min"] = row[0][0]
            state["raw_data"]["collected_at_max"] = row[0][1]

        # Sources
        by_src = _safe_query(
            conn,
            """
            SELECT s.name, COUNT(r.raw_data_id) AS n
            FROM source s
            LEFT JOIN raw_data r ON r.source_id = s.source_id
            GROUP BY s.source_id, s.name
            ORDER BY n DESC
            """,
        )
        state["by_source"] = [{"source": r[0], "articles": r[1]} for r in by_src]

        # Enrichment
        mo_total = _safe_query(conn, "SELECT COUNT(*) FROM model_output")
        mo_kw = _safe_query(
            conn,
            "SELECT COUNT(*) FROM model_output WHERE model_name = 'sentiment_keyword'",
        )
        dt_rows = _safe_query(conn, "SELECT COUNT(*) FROM document_topic")
        tagged = _safe_query(conn, "SELECT COUNT(DISTINCT raw_data_id) FROM document_topic")
        with_sent = _safe_query(
            conn,
            """
            SELECT COUNT(DISTINCT raw_data_id) FROM model_output
            WHERE model_name = 'sentiment_keyword'
            """,
        )
        dup_kw = _safe_query(
            conn,
            """
            SELECT COUNT(*) FROM (
                SELECT raw_data_id
                FROM model_output
                WHERE model_name = 'sentiment_keyword'
                GROUP BY raw_data_id
                HAVING COUNT(*) > 1
            )
            """,
        )
        sent_dist = _safe_query(
            conn,
            """
            SELECT label, COUNT(*) FROM model_output
            WHERE model_name = 'sentiment_keyword'
            GROUP BY label
            """,
        )

        state["enrichment"] = {
            "document_topic_rows": dt_rows[0][0] if dt_rows else 0,
            "articles_with_at_least_one_topic": tagged[0][0] if tagged else 0,
            "model_output_rows_total": mo_total[0][0] if mo_total else 0,
            "model_output_sentiment_keyword_rows": mo_kw[0][0] if mo_kw else 0,
            "articles_with_sentiment_keyword": with_sent[0][0] if with_sent else 0,
            "sentiment_keyword_distribution": (
                {r[0]: r[1] for r in sent_dist} if sent_dist else {}
            ),
        }
        state["data_quality"] = {
            "raw_data_ids_with_duplicate_sentiment_keyword": dup_kw[0][0] if dup_kw else 0,
            "note": "Si > 0, la jointure GOLD peut gonfler les lignes (corrigé côté aggregator par MAX(output_id)).",
        }

        # Recent sync log
        recent = _safe_query(
            conn,
            """
            SELECT s.name, sl.sync_date, sl.rows_synced, sl.status,
                   COALESCE(SUBSTR(sl.error_message, 1, 120), '') AS err
            FROM sync_log sl
            JOIN source s ON s.source_id = sl.source_id
            ORDER BY sl.sync_log_id DESC
            LIMIT 30
            """,
        )
        state["sync_log_recent"] = [
            {
                "source": r[0],
                "sync_date": r[1],
                "rows_synced": r[2],
                "status": r[3],
                "error_preview": r[4],
            }
            for r in recent
        ]

        # GoldAI metadata
        meta_path = PROJECT_ROOT / "data" / "goldai" / "metadata.json"
        if meta_path.exists():
            try:
                state["goldai_metadata"] = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception as e:
                state["goldai_metadata"] = {"error": str(e)[:200]}
        state["goldai_linkage"] = _goldai_raw_linkage(raw_ids_set)

        # Export hint (robust CSV parsing)
        gold_csv = PROJECT_ROOT / "exports" / "gold.csv"
        rows_csv = _count_csv_data_rows(gold_csv)
        if rows_csv is not None:
            state["exports_hint"]["exports_gold_csv_data_rows"] = rows_csv

        # Compare with previous report
        base = REPORTS_DIR / f"db_state_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}"
        prev = _latest_previous_report(base)
        if prev:
            prev_path, prev_state = prev
            prev_total = int(prev_state.get("raw_data", {}).get("total_rows", 0) or 0)
            curr_total = int(state.get("raw_data", {}).get("total_rows", 0) or 0)
            state["run_progress"]["previous_report"] = str(prev_path)
            state["run_progress"]["raw_data_delta_since_previous_report"] = curr_total - prev_total

            curr_by = _by_source_map(state.get("by_source", []))
            prev_by = _by_source_map(prev_state.get("by_source", []))
            deltas = []
            for src, cnt in curr_by.items():
                d = cnt - prev_by.get(src, 0)
                if d != 0:
                    deltas.append({"source": src, "delta": d, "current": cnt})
            deltas.sort(key=lambda x: x["delta"], reverse=True)
            state["run_progress"]["source_deltas_since_previous_report"] = deltas

        # Coherence checks
        raw_total = int(state.get("raw_data", {}).get("total_rows", 0) or 0)
        goldai_total = None
        if isinstance(state.get("goldai_metadata"), dict):
            goldai_total = state["goldai_metadata"].get("total_rows")
        csv_total = state.get("exports_hint", {}).get("exports_gold_csv_data_rows")

        checks = {}
        if goldai_total is not None:
            checks["goldai_minus_raw_data"] = int(goldai_total) - raw_total
        if csv_total is not None:
            checks["exports_gold_csv_minus_raw_data"] = int(csv_total) - raw_total
        checks["sentiment_keyword_duplicate_ids"] = state["data_quality"][
            "raw_data_ids_with_duplicate_sentiment_keyword"
        ]
        checks["status"] = "OK"
        reasons = []
        linkage = state.get("goldai_linkage") or {}
        gap = checks.get("goldai_minus_raw_data", 0)
        without_id = linkage.get("goldai_rows_without_raw_data_id")
        not_in_db = linkage.get("goldai_raw_id_not_in_db")
        if isinstance(not_in_db, int) and not_in_db > 0:
            reasons.append("GoldAI contient des raw_data_id absents du buffer SQLite")
        if gap > 0:
            if without_id is None:
                checks["goldai_gap_interpretation"] = "unverified_missing_linkage_metrics"
            elif isinstance(without_id, int) and without_id > 0:
                checks["goldai_gap_interpretation"] = (
                    "non_comparable_legacy_rows_without_raw_data_id"
                )
            else:
                reasons.append("GoldAI > DB (écart sur périmètre comparable)")
        if checks.get("exports_gold_csv_minus_raw_data", 0) != 0:
            reasons.append("gold.csv != raw_data")
        if checks.get("sentiment_keyword_duplicate_ids", 0) > 0:
            reasons.append("doublons sentiment_keyword")
        if reasons:
            checks["status"] = "WARNING"
            checks["reasons"] = reasons
        state["coherence_checks"] = checks

        # Actions automatiques (pilotage opérationnel)
        recos: list[str] = []
        if checks.get("goldai_minus_raw_data", 0) > 0:
            if checks.get("goldai_gap_interpretation") == "non_comparable_legacy_rows_without_raw_data_id":
                recos.append(
                    "Écart GoldAI vs buffer détecté mais non comparable (lignes legacy sans raw_data_id). "
                    "Comparer plutôt les lignes GoldAI avec raw_data_id renseigné."
                )
            elif checks.get("goldai_gap_interpretation") == "unverified_missing_linkage_metrics":
                recos.append(
                    "Écart GoldAI vs buffer détecté mais non vérifié (métriques de liaison indisponibles). "
                    "Lancer le rapport avec l'environnement projet (`.venv`) pour confirmer."
                )
            else:
                recos.append(
                    "GoldAI est au-dessus du buffer SQLite sur périmètre comparable. Pour réaligner, lancer: "
                    "python scripts/merge_parquet_goldai.py --force-full"
                )
        if checks.get("exports_gold_csv_minus_raw_data", 0) != 0:
            recos.append(
                "L'export GOLD diffère du buffer SQLite. Régénérer les exports: "
                "python scripts/regenerate_exports.py"
            )
        delta_raw = state.get("run_progress", {}).get("raw_data_delta_since_previous_report")
        if isinstance(delta_raw, int) and delta_raw <= 0:
            recos.append(
                "Aucune croissance depuis le rapport précédent. Vérifier les sources dynamiques "
                "(RSS/API), puis relancer un run E1."
            )
        if checks.get("sentiment_keyword_duplicate_ids", 0) > 0:
            recos.append(
                "Des doublons sentiment_keyword existent. Lancer une réanalyse sentiment pour "
                "rétablir l'unicité par raw_data_id."
            )
        if not recos:
            recos.append("Aucune action corrective immédiate: cohérence globale satisfaisante.")
        state["recommendations"] = recos

        return state
    finally:
        conn.close()


def render_markdown(state: dict) -> str:
    lines: list[str] = []
    m = state.get("meta", {})
    lines.append("# Rapport d'état — base DataSens\n")
    lines.append(f"- **Généré (UTC)** : {m.get('generated_at_utc', '')}")
    lines.append(f"- **Base** : `{m.get('db_path', '')}`")
    if m.get("db_size_bytes") is not None:
        lines.append(f"- **Taille fichier** : {m['db_size_bytes']:,} octets")
    if m.get("error"):
        lines.append(f"\n**Erreur** : {m['error']}")
        return "\n".join(lines)

    rd = state.get("raw_data", {})
    lines.append("\n## Articles (`raw_data`)\n")
    lines.append(f"- Total : **{rd.get('total_rows', 0):,}**")
    lines.append(f"- `raw_data_id` min / max : {rd.get('min_id')} / {rd.get('max_id')}")
    lines.append(f"- `collected_at` : `{rd.get('collected_at_min')}` → `{rd.get('collected_at_max')}`")

    rp = state.get("run_progress", {})
    if rp:
        lines.append("\n## Évolution depuis le rapport précédent\n")
        if rp.get("previous_report"):
            lines.append(f"- Rapport précédent : `{rp['previous_report']}`")
        d = rp.get("raw_data_delta_since_previous_report")
        if d is not None:
            lines.append(f"- Delta `raw_data` : **{d:+,}**")
        src_deltas = rp.get("source_deltas_since_previous_report", [])
        if src_deltas:
            lines.append("- Deltas par source (non nuls) :")
            for r in src_deltas[:12]:
                lines.append(f"  - `{r['source']}` : {r['delta']:+,} (total {r['current']:,})")

    checks = state.get("coherence_checks", {})
    lines.append("\n## Contrôles de cohérence\n")
    lines.append(f"- Statut : **{checks.get('status', 'n/a')}**")
    if "goldai_minus_raw_data" in checks:
        lines.append(f"- `GoldAI total_rows - raw_data` : **{checks['goldai_minus_raw_data']:+,}**")
    if checks.get("goldai_gap_interpretation"):
        lines.append(f"- Interprétation écart GoldAI : `{checks['goldai_gap_interpretation']}`")
    if "exports_gold_csv_minus_raw_data" in checks:
        lines.append(
            f"- `exports/gold.csv - raw_data` : **{checks['exports_gold_csv_minus_raw_data']:+,}**"
        )
    lines.append(
        f"- IDs avec sentiment dupliqué : **{checks.get('sentiment_keyword_duplicate_ids', 0):,}**"
    )
    for reason in checks.get("reasons", []):
        lines.append(f"- ⚠️ {reason}")

    lines.append("\n## Actions recommandées\n")
    for r in state.get("recommendations", []):
        lines.append(f"- {r}")

    lines.append("\n## Par source\n")
    lines.append("| Source | Articles |")
    lines.append("|--------|----------|")
    for row in state.get("by_source", [])[:40]:
        lines.append(f"| {row['source']} | {row['articles']:,} |")
    if len(state.get("by_source", [])) > 40:
        lines.append("| … | … |")

    en = state.get("enrichment", {})
    lines.append("\n## Enrichissement\n")
    lines.append(f"- Lignes `document_topic` : {en.get('document_topic_rows', 0):,}")
    lines.append(f"- Articles avec au moins un topic : {en.get('articles_with_at_least_one_topic', 0):,}")
    lines.append(f"- Lignes `model_output` (tous modèles) : {en.get('model_output_rows_total', 0):,}")
    lines.append(
        f"- Lignes sentiment `sentiment_keyword` : {en.get('model_output_sentiment_keyword_rows', 0):,}"
    )
    lines.append(f"- Articles avec sentiment keyword : {en.get('articles_with_sentiment_keyword', 0):,}")
    dist = en.get("sentiment_keyword_distribution") or {}
    if dist:
        lines.append("- Distribution sentiment : " + ", ".join(f"{k}={v}" for k, v in sorted(dist.items())))

    dq = state.get("data_quality", {})
    lines.append("\n## Qualité / cohérence technique\n")
    lines.append(
        f"- `raw_data_id` avec **plusieurs** lignes `sentiment_keyword` : **{dq.get('raw_data_ids_with_duplicate_sentiment_keyword', 0)}**"
    )
    lines.append(f"- _{dq.get('note', '')}_")

    gh = state.get("goldai_metadata")
    lines.append("\n## GoldAI (`data/goldai/metadata.json`)\n")
    if gh is None:
        lines.append("_Fichier absent._")
    elif isinstance(gh, dict) and "error" in gh:
        lines.append(f"_Erreur lecture : {gh['error']}_")
    else:
        lines.append(f"```json\n{json.dumps(gh, ensure_ascii=False, indent=2)[:4000]}\n```")

    gl = state.get("goldai_linkage") or {}
    if gl:
        lines.append("\n## Liaison GoldAI ↔ SQLite (`raw_data_id`)\n")
        if gl.get("goldai_rows_total_parquet") is not None:
            lines.append(f"- Lignes GoldAI (parquet) : **{int(gl['goldai_rows_total_parquet']):,}**")
        if gl.get("goldai_rows_with_raw_data_id") is not None:
            lines.append(f"- GoldAI avec `raw_data_id` : **{int(gl['goldai_rows_with_raw_data_id']):,}**")
        if gl.get("goldai_rows_without_raw_data_id") is not None:
            lines.append(f"- GoldAI sans `raw_data_id` : **{int(gl['goldai_rows_without_raw_data_id']):,}**")
        if gl.get("goldai_raw_id_in_db") is not None:
            lines.append(f"- `raw_data_id` GoldAI présents en SQLite : **{int(gl['goldai_raw_id_in_db']):,}**")
        if gl.get("goldai_raw_id_not_in_db") is not None:
            lines.append(f"- `raw_data_id` GoldAI absents de SQLite : **{int(gl['goldai_raw_id_not_in_db']):,}**")

    ex = state.get("exports_hint", {})
    if ex.get("exports_gold_csv_data_rows") is not None:
        lines.append("\n## Export courant\n")
        lines.append(
            f"- `exports/gold.csv` (lignes de données, parsing CSV réel) : **{ex['exports_gold_csv_data_rows']:,}**"
        )

    lines.append("\n## Derniers `sync_log` (30)\n")
    for s in state.get("sync_log_recent", []):
        lines.append(
            f"- `{s.get('sync_date')}` **{s.get('source')}** — {s.get('rows_synced')} lignes, status `{s.get('status')}`"
        )

    return "\n".join(lines)


def main() -> int:
    db_file = _db_path()
    state = collect_state(db_file)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    base = REPORTS_DIR / f"db_state_{stamp}"
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")

    json_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(state), encoding="utf-8")

    print(f"[OK] Rapport JSON : {json_path}")
    print(f"[OK] Rapport MD   : {md_path}")
    rd = state.get("raw_data", {})
    if rd.get("total_rows") is not None:
        print(f"     raw_data total : {rd['total_rows']:,}")
    checks = state.get("coherence_checks", {})
    if checks:
        print(f"     coherence      : {checks.get('status', 'n/a')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
