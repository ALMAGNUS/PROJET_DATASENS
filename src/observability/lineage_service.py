"""Lineage service for DataSens cockpit (business logic only)."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path


class LineageService:
    """Compute daily lineage / transformation metrics from SQLite (+ optional GoldAI/Mongo)."""

    def __init__(self, db_path: str, project_root: Path):
        self.db_path = db_path
        self.project_root = project_root

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _as_dicts(rows: list[sqlite3.Row]) -> list[dict]:
        return [dict(r) for r in rows]

    def _goldai_total_rows(self) -> int | None:
        meta = self.project_root / "data" / "goldai" / "metadata.json"
        if not meta.exists():
            return None
        try:
            import json

            payload = json.loads(meta.read_text(encoding="utf-8"))
            return int(payload.get("total_rows", 0))
        except Exception:
            return None

    def _mongo_file_count(self) -> int | None:
        try:
            from pymongo import MongoClient

            from src.config import get_settings

            cfg = get_settings()
            client = MongoClient(cfg.mongo_uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            coll = client[cfg.mongo_db][f"{cfg.mongo_gridfs_bucket}.files"]
            count = int(coll.count_documents({}))
            client.close()
            return count
        except Exception:
            return None

    def get_daily_lineage(self, target_date: date | None = None) -> dict:
        d = target_date or date.today()
        d_s = d.isoformat()
        conn = self._connect()
        try:
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) AS n FROM raw_data WHERE date(collected_at) < ?", (d_s,))
            before_total = int(cur.fetchone()["n"])

            cur.execute("SELECT COUNT(*) AS n FROM raw_data WHERE date(collected_at) = ?", (d_s,))
            added_today = int(cur.fetchone()["n"])

            after_total = before_total + added_today

            cur.execute(
                """
                SELECT COALESCE(SUM(rows_synced), 0) AS n
                FROM sync_log
                WHERE date(sync_date) = ?
                  AND status = 'OK'
                """,
                (d_s,),
            )
            collected_today = int(cur.fetchone()["n"])

            duplicates_today = max(collected_today - added_today, 0)

            cur.execute(
                """
                SELECT s.name AS source, COUNT(*) AS added_rows
                FROM raw_data r
                JOIN source s ON s.source_id = r.source_id
                WHERE date(r.collected_at) = ?
                GROUP BY s.name
                ORDER BY added_rows DESC
                """,
                (d_s,),
            )
            added_by_source = {r["source"]: int(r["added_rows"]) for r in cur.fetchall()}

            cur.execute(
                """
                SELECT s.name AS source, COALESCE(SUM(sl.rows_synced), 0) AS collected_rows
                FROM source s
                LEFT JOIN sync_log sl
                  ON sl.source_id = s.source_id
                 AND date(sl.sync_date) = ?
                 AND sl.status = 'OK'
                GROUP BY s.name
                """,
                (d_s,),
            )
            collected_rows = self._as_dicts(cur.fetchall())
            by_source = []
            for r in collected_rows:
                src = r["source"]
                coll = int(r["collected_rows"] or 0)
                add = int(added_by_source.get(src, 0))
                if coll == 0 and add == 0:
                    continue
                by_source.append(
                    {
                        "source": src,
                        "collected_today": coll,
                        "added_today": add,
                        "duplicates_today": max(coll - add, 0),
                    }
                )
            by_source.sort(key=lambda x: x["added_today"], reverse=True)

            cur.execute(
                """
                SELECT r.raw_data_id AS id, s.name AS source, r.collected_at, r.title, r.url
                FROM raw_data r
                JOIN source s ON s.source_id = r.source_id
                WHERE date(r.collected_at) = ?
                ORDER BY r.raw_data_id DESC
                LIMIT 400
                """,
                (d_s,),
            )
            new_rows = self._as_dicts(cur.fetchall())

            # Échantillon de transformations réelles (article-level lineage)
            cur.execute(
                """
                SELECT
                    r.raw_data_id AS id,
                    s.name AS source,
                    r.collected_at,
                    r.title,
                    r.content,
                    r.url,
                    t1.topic_1,
                    t2.topic_2,
                    mo.label AS sentiment,
                    mo.score AS sentiment_score
                FROM raw_data r
                JOIN source s ON s.source_id = r.source_id
                LEFT JOIN (
                    SELECT dt.raw_data_id, t.name AS topic_1
                    FROM document_topic dt
                    JOIN topic t ON t.topic_id = dt.topic_id
                    JOIN (
                        SELECT raw_data_id, MAX(confidence_score) AS max_conf
                        FROM document_topic
                        GROUP BY raw_data_id
                    ) m ON m.raw_data_id = dt.raw_data_id AND m.max_conf = dt.confidence_score
                ) t1 ON t1.raw_data_id = r.raw_data_id
                LEFT JOIN (
                    SELECT dt.raw_data_id, t.name AS topic_2
                    FROM document_topic dt
                    JOIN topic t ON t.topic_id = dt.topic_id
                    JOIN (
                        SELECT raw_data_id, MIN(confidence_score) AS min_conf
                        FROM document_topic
                        GROUP BY raw_data_id
                    ) m ON m.raw_data_id = dt.raw_data_id AND m.min_conf = dt.confidence_score
                ) t2 ON t2.raw_data_id = r.raw_data_id
                LEFT JOIN (
                    SELECT mo1.raw_data_id, mo1.label, mo1.score
                    FROM model_output mo1
                    JOIN (
                        SELECT raw_data_id, MAX(output_id) AS max_oid
                        FROM model_output
                        WHERE model_name = 'sentiment_keyword'
                        GROUP BY raw_data_id
                    ) x ON x.raw_data_id = mo1.raw_data_id AND x.max_oid = mo1.output_id
                    WHERE mo1.model_name = 'sentiment_keyword'
                ) mo ON mo.raw_data_id = r.raw_data_id
                WHERE date(r.collected_at) = ?
                ORDER BY r.raw_data_id DESC
                LIMIT 60
                """,
                (d_s,),
            )
            transformed_samples = self._as_dicts(cur.fetchall())
            # Dédupliquer l'échantillon sur id (les JOINs topics peuvent créer des ex-aequo)
            seen_ids: set[int] = set()
            uniq_samples: list[dict] = []
            for r in transformed_samples:
                rid = int(r.get("id", 0) or 0)
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)
                uniq_samples.append(r)
            transformed_samples = uniq_samples

            cur.execute(
                """
                SELECT date(collected_at) AS day, COUNT(*) AS added_rows
                FROM raw_data
                GROUP BY date(collected_at)
                ORDER BY day DESC
                LIMIT 40
                """
            )
            hist_added = self._as_dicts(cur.fetchall())

            cur.execute(
                """
                SELECT date(sync_date) AS day, COALESCE(SUM(rows_synced), 0) AS collected_rows
                FROM sync_log
                WHERE status = 'OK'
                GROUP BY date(sync_date)
                ORDER BY day DESC
                LIMIT 40
                """
            )
            hist_collected = {r["day"]: int(r["collected_rows"]) for r in cur.fetchall()}
            history = []
            for r in hist_added:
                day = r["day"]
                add = int(r["added_rows"])
                coll = int(hist_collected.get(day, 0))
                history.append(
                    {
                        "day": day,
                        "collected_rows": coll,
                        "added_rows": add,
                        "duplicates_rows": max(coll - add, 0),
                    }
                )

            # Qualité d'ingestion (jour): ce qui n'est pas ajouté = doublons et/ou rejets
            duplicates_table = [
                {
                    "source": x["source"],
                    "collected_today": x["collected_today"],
                    "added_today": x["added_today"],
                    "non_added_today": x["duplicates_today"],
                }
                for x in by_source
                if x["duplicates_today"] > 0
            ]
            duplicates_table.sort(key=lambda x: x["non_added_today"], reverse=True)

            rejected_table = [
                {
                    "source": x["source"],
                    "rejected_rows_exact": None,
                    "status": "non_persisted",
                    "note": "Les rejets validation ne sont pas persistés ligne à ligne; inclus dans non_added_today.",
                }
                for x in by_source
            ]

            # Enrichissement du jour (articles ajoutés aujourd'hui)
            cur.execute(
                """
                SELECT s.name AS source,
                       COUNT(DISTINCT r.raw_data_id) AS added_today,
                       COUNT(DISTINCT CASE WHEN dt.raw_data_id IS NOT NULL THEN r.raw_data_id END) AS topic_enriched,
                       COUNT(DISTINCT CASE WHEN mo.raw_data_id IS NOT NULL THEN r.raw_data_id END) AS sentiment_enriched,
                       COUNT(DISTINCT CASE WHEN dt.raw_data_id IS NOT NULL AND mo.raw_data_id IS NOT NULL THEN r.raw_data_id END) AS fully_enriched
                FROM raw_data r
                JOIN source s ON s.source_id = r.source_id
                LEFT JOIN document_topic dt ON dt.raw_data_id = r.raw_data_id
                LEFT JOIN model_output mo
                  ON mo.raw_data_id = r.raw_data_id
                 AND mo.model_name = 'sentiment_keyword'
                WHERE date(r.collected_at) = ?
                GROUP BY s.name
                ORDER BY added_today DESC
                """,
                (d_s,),
            )
            enriched_rows = self._as_dicts(cur.fetchall())

            cur.execute("SELECT COUNT(*) AS n FROM raw_data")
            raw_total = int(cur.fetchone()["n"])
            cur.execute("SELECT COUNT(DISTINCT raw_data_id) AS n FROM document_topic")
            silver_total = int(cur.fetchone()["n"])
            cur.execute(
                """
                SELECT COUNT(DISTINCT raw_data_id) AS n
                FROM model_output
                WHERE model_name = 'sentiment_keyword'
                """
            )
            gold_total = int(cur.fetchone()["n"])
            goldai_total = self._goldai_total_rows()
            mongo_files = self._mongo_file_count()

            return {
                "target_date": d_s,
                "formulas": {
                    "collection_to_insert": f"{collected_today:,} - {duplicates_today:,} = {added_today:,}",
                    "before_to_after": f"{before_total:,} + {added_today:,} = {after_total:,}",
                },
                "summary": {
                    "before_total": before_total,
                    "collected_today": collected_today,
                    "duplicates_today": duplicates_today,
                    "added_today": added_today,
                    "after_total": after_total,
                },
                "layers": {
                    "raw_sqlite": raw_total,
                    "silver_sqlite": silver_total,
                    "gold_sqlite": gold_total,
                    "goldai_parquet": goldai_total,
                    "mongo_gridfs_files": mongo_files,
                },
                "by_source": by_source,
                "new_rows_today": new_rows,
                "transformed_samples_today": transformed_samples,
                "duplicates_rows_today_table": duplicates_table,
                "rejected_rows_today_table": rejected_table,
                "enriched_rows_today_table": enriched_rows,
                "history_daily": history,
            }
        finally:
            conn.close()

