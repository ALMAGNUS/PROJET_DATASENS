"""DataSens Dashboard - Visualisation enrichissement dataset"""
import sqlite3
from datetime import datetime
from pathlib import Path

from loguru import logger

from .e1.console import ConsolePrinter
from .e1.ui_messages import UiMessages


class DataSensDashboard:
    def __init__(self, db_path: str, console: ConsolePrinter | None = None):
        self.conn = sqlite3.connect(db_path)
        self.stats = {}
        self.console = console or ConsolePrinter()

    def collect_stats(self):
        """Collecte toutes les statistiques d'enrichissement"""
        c = self.conn.cursor()
        project_root = Path(__file__).resolve().parents[1]

        # 1. Total par source
        c.execute(
            """
            SELECT s.name, COUNT(r.raw_data_id) as total,
                   COUNT(DISTINCT r.fingerprint) as unique_count,
                   MAX(r.collected_at) as last_collect
            FROM source s
            LEFT JOIN raw_data r ON s.source_id = r.source_id
            GROUP BY s.name
            ORDER BY total DESC
        """
        )
        self.stats["by_source"] = [
            {"source": r[0], "total": r[1], "unique": r[2], "last": r[3]} for r in c.fetchall()
        ]

        # 2. Enrichissement Topics
        c.execute(
            """
            SELECT COUNT(DISTINCT dt.raw_data_id) as tagged_count,
                   COUNT(DISTINCT dt.topic_id) as topics_used,
                   AVG(dt.confidence_score) as avg_confidence
            FROM document_topic dt
        """
        )
        r = c.fetchone()
        self.stats["topics"] = {
            "tagged": r[0] or 0,
            "topics_used": r[1] or 0,
            "avg_confidence": round(r[2] or 0, 2),
        }

        # 3. Enrichissement Sentiment
        c.execute(
            """
            SELECT label, COUNT(*) as count, AVG(score) as avg_score
            FROM model_output
            WHERE model_name = 'sentiment_keyword'
            GROUP BY label
        """
        )
        self.stats["sentiment"] = {
            r[0]: {"count": r[1], "avg_score": round(r[2], 2)} for r in c.fetchall()
        }

        # 4. Articles enrichis (avec topics ET sentiment)
        c.execute(
            """
            SELECT COUNT(DISTINCT r.raw_data_id) as enriched
            FROM raw_data r
            WHERE EXISTS (SELECT 1 FROM document_topic dt WHERE dt.raw_data_id = r.raw_data_id)
            AND EXISTS (SELECT 1 FROM model_output mo WHERE mo.raw_data_id = r.raw_data_id AND mo.model_name = 'sentiment_keyword')
        """
        )
        self.stats["enriched"] = c.fetchone()[0] or 0

        # 5. Nouveaux articles aujourd'hui
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute(
            """
            SELECT COUNT(*) FROM raw_data
            WHERE DATE(collected_at) = ?
        """,
            (today,),
        )
        self.stats["new_today"] = c.fetchone()[0] or 0

        # 6. Nouveaux articles aujourd'hui par source
        c.execute(
            """
            SELECT s.name, COUNT(r.raw_data_id) as count
            FROM source s
            LEFT JOIN raw_data r ON s.source_id = r.source_id AND DATE(r.collected_at) = ?
            GROUP BY s.name
            HAVING COUNT(r.raw_data_id) > 0
            ORDER BY count DESC
        """,
            (today,),
        )
        self.stats["new_by_source"] = {r[0]: r[1] for r in c.fetchall()}

        # 7. Distribution par topic
        c.execute(
            """
            SELECT t.name, COUNT(dt.raw_data_id) as count
            FROM topic t
            LEFT JOIN document_topic dt ON t.topic_id = dt.topic_id
            GROUP BY t.name
            ORDER BY count DESC
        """
        )
        self.stats["topics_dist"] = {r[0]: r[1] for r in c.fetchall()}

        # 8. Total général
        c.execute("SELECT COUNT(*) FROM raw_data")
        self.stats["total"] = c.fetchone()[0] or 0

        c.execute(
            "SELECT COUNT(DISTINCT fingerprint) FROM raw_data WHERE fingerprint IS NOT NULL AND fingerprint != ''"
        )
        self.stats["unique"] = c.fetchone()[0] or 0

        # 9. Stockage & exports (tech)
        raw_dir = project_root / "data" / "raw"
        silver_dir = project_root / "data" / "silver"
        gold_dir = project_root / "data" / "gold"
        exports_dir = project_root / "exports"

        raw_partitions = (
            [p for p in raw_dir.glob("sources_*") if p.is_dir()] if raw_dir.exists() else []
        )
        silver_partitions = (
            [p for p in silver_dir.iterdir() if p.is_dir()] if silver_dir.exists() else []
        )
        gold_partitions = (
            [p for p in gold_dir.glob("date=*") if p.is_dir()] if gold_dir.exists() else []
        )
        gold_latest = max((p.name.replace("date=", "") for p in gold_partitions), default="n/a")
        exports_files = list(exports_dir.glob("*.csv")) if exports_dir.exists() else []

        self.stats["storage"] = {
            "raw_partitions": len(raw_partitions),
            "silver_partitions": len(silver_partitions),
            "gold_partitions": len(gold_partitions),
            "gold_latest": gold_latest,
            "exports_csv": len(exports_files),
        }

        # 10. ZZDB status (tech)
        c.execute(
            """
            SELECT s.name, s.active,
                   COUNT(r.raw_data_id) as total,
                   COUNT(DISTINCT r.fingerprint) as unique_count
            FROM source s
            LEFT JOIN raw_data r ON s.source_id = r.source_id
            WHERE s.name LIKE 'zzdb%'
            GROUP BY s.name, s.active
            ORDER BY s.name
        """
        )
        self.stats["zzdb"] = [
            {"name": r[0], "active": r[1], "total": r[2] or 0, "unique": r[3] or 0}
            for r in c.fetchall()
        ]
        logger.info("Dashboard stats collected")

    def print_dashboard(self):
        """Affiche le dashboard formaté"""
        logger.info("Dashboard print start")
        console_write = self.console.write
        console_write("\n" + UiMessages.dashboard_title()[0])
        console_write(UiMessages.dashboard_title()[1])
        console_write(UiMessages.dashboard_title()[2])

        # Résumé global
        console_write("\n" + UiMessages.dashboard_resume_title())
        console_write(f"   Total articles:        {self.stats['total']:,}")
        console_write(f"   Articles uniques:      {self.stats['unique']:,}")
        console_write(f"   Nouveaux aujourd'hui:  {self.stats['new_today']:,}")
        console_write(
            f"   Articles enrichis:     {self.stats['enriched']:,} ({self.stats['enriched']/max(self.stats['total'],1)*100:.1f}%)"
        )

        # Nouveaux articles par source aujourd'hui
        if self.stats["new_by_source"]:
            console_write("\n" + UiMessages.dashboard_new_by_source_title())
            for source, count in sorted(self.stats["new_by_source"].items(), key=lambda x: -x[1]):
                source_lower = source.lower()
                if "zzdb" in source_lower:
                    marker = " [DB NON-REL] [DONNÉES SYNTHÈSE] [LAB IA]"
                elif "kaggle" in source_lower:
                    marker = " [FICHIERS PLATS]"
                else:
                    marker = ""
                console_write(f"   • {source:30s}: {count:4d} articles{marker}")

        # Enrichissement Topics
        console_write("\n" + UiMessages.dashboard_topics_title())
        console_write(f"   Articles taggés:        {self.stats['topics']['tagged']:,}")
        console_write(f"   Topics utilisés:       {self.stats['topics']['topics_used']}")
        console_write(f"   Confiance moyenne:     {self.stats['topics']['avg_confidence']:.2f}")
        if self.stats["topics_dist"]:
            console_write("   Distribution:")
            for topic, count in sorted(self.stats["topics_dist"].items(), key=lambda x: -x[1])[:5]:
                console_write(f"      • {topic:20s}: {count:4d} articles")

        # Enrichissement Sentiment - AFFICHAGE COMPLET (positif, négatif, neutre)
        console_write("\n" + UiMessages.dashboard_sentiment_title())
        total_sent = sum(s["count"] for s in self.stats["sentiment"].values())
        if total_sent > 0:
            # Afficher dans l'ordre : positif, négatif, neutre (même si 0)
            sentiment_order = ["positif", "négatif", "neutre"]
            for label in sentiment_order:
                data = self.stats["sentiment"].get(label, {"count": 0, "avg_score": 0.0})
                pct = (data["count"] / max(total_sent, 1)) * 100
                marker = " WARN" if label == "négatif" and data["count"] == 0 else ""
                console_write(
                    f"   {label:10s}: {data['count']:4d} articles ({pct:5.1f}%) - Score moyen: {data['avg_score']:.2f}{marker}"
                )

            # Afficher aussi les autres labels s'il y en a
            for label, data in sorted(
                self.stats["sentiment"].items(), key=lambda x: -x[1]["count"]
            ):
                if label not in sentiment_order:
                    pct = (data["count"] / max(total_sent, 1)) * 100
                    console_write(
                        f"   {label:10s}: {data['count']:4d} articles ({pct:5.1f}%) - Score moyen: {data['avg_score']:.2f}"
                    )
        else:
            console_write("   WARN Aucun sentiment analysé")

        # Par source (chiffres uniquement)
        console_write("\n" + UiMessages.dashboard_sources_title())
        console_write(f"   {'Source':<30s} {'Total':>8s} {'Unique':>8s}")
        console_write(f"   {'-'*30} {'-'*8} {'-'*8}")
        zzdb_total = 0
        zzdb_unique = 0
        zzdb_sources = []
        for s in self.stats["by_source"][:15]:
            source_name = s["source"]
            source_lower = source_name.lower()

            # Regrouper les sources ZZDB
            if "zzdb" in source_lower:
                zzdb_total += s["total"]
                zzdb_unique += s["unique"]
                zzdb_sources.append((source_name, s))
                continue  # On affichera après

            console_write(f"   {source_name:<30s} {s['total']:>8d} {s['unique']:>8d}")

        # Afficher ZZDB regroupé
        if zzdb_sources:
            console_write(f"   {'ZZDB (TOTAL)':<30s} {zzdb_total:>8d} {zzdb_unique:>8d}")
            for source_name, s in zzdb_sources:
                console_write(f"      └─ {source_name:<27s} {s['total']:>8d} {s['unique']:>8d}")

        # ZZDB status (tech)
        if self.stats.get("zzdb"):
            console_write("\n   ZZDB status")
            console_write(f"   {'Source':<30s} {'Active':>8s} {'Total':>8s} {'Unique':>8s}")
            console_write(f"   {'-'*30} {'-'*8} {'-'*8} {'-'*8}")
            for item in self.stats["zzdb"]:
                active = "1" if item["active"] else "0"
                console_write(
                    f"   {item['name']:<30s} {active:>8s} {item['total']:>8d} {item['unique']:>8d}"
                )

        # Stockage & exports (tech)
        if self.stats.get("storage"):
            console_write("\n   Stockage & exports")
            console_write(f"   RAW partitions:    {self.stats['storage']['raw_partitions']}")
            console_write(f"   SILVER partitions: {self.stats['storage']['silver_partitions']}")
            console_write(f"   GOLD partitions:   {self.stats['storage']['gold_partitions']}")
            console_write(f"   GOLD latest date:  {self.stats['storage']['gold_latest']}")
            console_write(f"   Exports CSV:       {self.stats['storage']['exports_csv']}")

        # Évaluation dataset pour IA
        console_write("\n" + UiMessages.dashboard_ai_title())
        total = self.stats["total"]
        enriched = self.stats["enriched"]
        pct_enriched = (enriched / max(total, 1)) * 100

        if total < 100:
            status = "[KO] INSUFFISANT"
            msg = "Minimum 100 articles requis"
        elif total < 500:
            status = "[WARN] LIMITÉ"
            msg = "Recommandé: 500+ articles"
        elif total < 1000:
            status = "[OK] BON"
            msg = "Recommandé: 1000+ articles"
        else:
            status = "[OK] EXCELLENT"
            msg = "Dataset prêt pour l'IA"

        console_write(f"   Status: {status} ({total:,} articles)")
        console_write(f"   Message: {msg}")
        console_write(f"   Taux d'enrichissement: {pct_enriched:.1f}%")

        if pct_enriched < 50:
            console_write(
                f"   [WARN] Attention: Seulement {pct_enriched:.1f}% des articles sont enrichis (topics + sentiment)"
            )
            console_write(
                "   [INFO] Solution: Lancer 'python scripts/enrich_all_articles.py' pour enrichir tous les articles"
            )

        console_write("\n" + "=" * 80 + "\n")
        logger.info("Dashboard print complete")

    def close(self):
        self.conn.close()
