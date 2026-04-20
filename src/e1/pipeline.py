"""DataSens E1 - Pipeline Isolé"""
import json
import os
import time
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# .env à la racine du dépôt → disponible pour os.getenv (OPENWEATHERMAP_API_KEY, DB_PATH, …)
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

# Imports depuis src/ (utilitaires - peuvent rester en src/ pour l'instant)
# Note: Quand src/ est dans PYTHONPATH, utiliser imports sans préfixe src.
try:
    from collection_report import CollectionReport
    from dashboard import DataSensDashboard
    from metrics import (
        MetricsCollector,
        articles_analyzed_total,
        articles_deduplicated_total,
        articles_extracted_total,
        articles_loaded_total,
        articles_tagged_total,
        extraction_duration_seconds,
        pipeline_runs_total,
        source_errors_total,
        start_metrics_server,
        update_database_stats,
    )
except ImportError:
    # Fallback pour imports locaux (si src/ n'est pas dans PYTHONPATH)
    from src.collection_report import CollectionReport
    from src.dashboard import DataSensDashboard
    from src.metrics import (
        MetricsCollector,
        articles_analyzed_total,
        articles_deduplicated_total,
        articles_extracted_total,
        articles_loaded_total,
        articles_tagged_total,
        extraction_duration_seconds,
        pipeline_runs_total,
        source_errors_total,
        start_metrics_server,
        update_database_stats,
    )

from .aggregator import DataAggregator
from .analyzer import SentimentAnalyzer

# Imports locaux E1
from .console import ConsolePrinter
from .core import ContentTransformer, Source, collection_mode_description, create_extractor
from .exporter import GoldExporter
from .repository import Repository
from .tagger import TopicTagger
from .ui_messages import UiMessages


def _env_float(name: str, default: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def _env_int(name: str, default: int, minimum: int = 0, maximum: int = 1_000_000) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


class E1Pipeline:
    """Complete E1 Pipeline - ISOLÉ"""

    def __init__(self, metrics_port: int = 8000, quiet: bool = False):
        # Use environment variable or default path
        db_path = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.console = ConsolePrinter(quiet=quiet)
        self.db = Repository(db_path)
        self.tagger = TopicTagger(db_path)
        self.analyzer = SentimentAnalyzer(db_path)
        self.stats = {
            "extracted": 0,
            "cleaned": 0,
            "loaded": 0,
            "deduplicated": 0,
            "tagged": 0,
            "analyzed": 0,
        }
        self.cleaning_rejects = {
            "empty_title": 0,
            "empty_content": 0,
            "title_too_short": 0,
            "content_too_short": 0,
            "invalid_url": 0,
            "other_invalid": 0,
        }
        self.cleaning_reject_examples: list[dict[str, str]] = []
        self.source_run_stats: dict[str, dict[str, float | int | str]] = {}
        self.source_anomalies: list[str] = []
        self.session_start = datetime.now().isoformat()
        self.run_started_at = datetime.now()

        # Start Prometheus metrics server
        try:
            port = int(os.getenv("METRICS_PORT", metrics_port))
            start_metrics_server(port)
        except Exception as e:
            logger.warning("Metrics server failed: {}", e)

    def load_sources(self, inject_csv_path: str | None = None, inject_source_name: str = "csv_inject") -> list:
        """Load sources from JSON config + source CSV injectée si --inject-csv"""
        config_path = Path(__file__).parent.parent.parent / "sources_config.json"
        sources = []
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                sources = [Source(**s) for s in config["sources"]]
        if inject_csv_path:
            p = Path(inject_csv_path)
            if p.exists():
                sources.insert(0, Source(source_name=inject_source_name, acquisition_type="csv", url=str(p.resolve())))
        return sources

    def extract(self, inject_csv_path: str | None = None, inject_source_name: str = "csv_inject") -> list:
        """Extract from all sources"""
        console_write = self.console.write
        self.source_run_stats = {}
        console_write("\n" + UiMessages.extraction_title()[0])
        console_write(UiMessages.extraction_title()[1])
        console_write(UiMessages.extraction_title()[2])
        logger.info("Extraction start: all sources")

        sources = self.load_sources(inject_csv_path=inject_csv_path, inject_source_name=inject_source_name)
        articles = []

        total_sources = sum(1 for s in sources if s.active)
        current_source = 0

        for source in sources:
            if not source.active:
                continue

            current_source += 1
            mode_label = collection_mode_description(source)
            console_write(
                f"[{current_source}/{total_sources}] {source.source_name}... [{mode_label}]",
                end=" ",
                flush=True,
            )

            # Vérifier si source fondation déjà intégrée (à figer) - sauf injection à la demande
            is_foundation, _foundation_type, should_freeze = self._is_foundation_source(
                source.source_name
            )
            if source.source_name != inject_source_name and is_foundation and should_freeze:
                if self.db.is_foundation_integrated(source.source_name):
                    console_write("SKIP (fondation déjà intégrée)")
                    continue

            start_time = time.time()
            try:
                extractor = create_extractor(source)
                extracted = extractor.extract()
                duration = time.time() - start_time
                extraction_duration_seconds.labels(source=source.source_name).observe(duration)

                self.stats["extracted"] += len(extracted)
                articles_extracted_total.labels(source=source.source_name).inc(len(extracted))
                articles.extend([(a, source.source_name) for a in extracted])
                self.source_run_stats[source.source_name] = {
                    "extracted": len(extracted),
                    "duration_sec": round(duration, 3),
                    "status": "OK",
                }

                # Log sync to database
                source_id = self.db.get_source_id(source.source_name)
                if source_id:
                    self.db.log_sync(source_id, len(extracted), "OK")

                # Message spécial pour ZZDB
                if "zzdb" in source.source_name.lower():
                    console_write(f"OK {len(extracted)} articles [ZZDB → DataSens]")
                elif len(extracted) > 1000:
                    console_write(f"OK {len(extracted):,} articles (traitement en cours...)")
                else:
                    console_write(f"OK {len(extracted)}")
            except Exception as e:
                source_errors_total.labels(source=source.source_name).inc()
                logger.error("Extraction error: {}", str(e)[:40])
                self.source_run_stats[source.source_name] = {
                    "extracted": 0,
                    "duration_sec": round(time.time() - start_time, 3),
                    "status": "ERR",
                }
                console_write(f"ERR ({str(e)[:45]})")

        logger.info("Extraction complete: {} articles", self.stats["extracted"])
        console_write(f"\nOK Total extracted: {self.stats['extracted']}")
        inactive = [s.source_name for s in sources if not s.active]
        if inactive:
            shown = ", ".join(inactive[:12])
            if len(inactive) > 12:
                shown += f", … (+{len(inactive) - 12})"
            console_write(f"\n   [Info] Sources inactives (non extraites) : {shown}")
        return articles

    def clean(self, articles: list) -> list:
        """Clean and validate articles"""
        console_write = self.console.write
        console_write("\n" + UiMessages.cleaning_title()[0])
        console_write(UiMessages.cleaning_title()[1])
        console_write(UiMessages.cleaning_title()[2])
        logger.info("Cleaning start: {} articles", len(articles))

        cleaned = []
        self.cleaning_rejects = {
            "empty_title": 0,
            "empty_content": 0,
            "title_too_short": 0,
            "content_too_short": 0,
            "invalid_url": 0,
            "other_invalid": 0,
        }
        self.cleaning_reject_examples = []
        for article, source_name in articles:
            article = ContentTransformer.transform(article)
            if article.is_valid():
                cleaned.append((article, source_name))
                self.stats["cleaned"] += 1
            else:
                reason = self._classify_cleaning_reject(article)
                self.cleaning_rejects[reason] = self.cleaning_rejects.get(reason, 0) + 1
                if len(self.cleaning_reject_examples) < 5:
                    self.cleaning_reject_examples.append(
                        {
                            "source": source_name or (article.source_name or "unknown"),
                            "reason": reason,
                            "title": (article.title or "").strip()[:80],
                        }
                    )

        logger.info("Cleaning complete: {} articles", self.stats["cleaned"])
        console_write(f"OK Cleaned: {self.stats['cleaned']}")
        rejected_total = len(articles) - self.stats["cleaned"]
        if rejected_total > 0:
            console_write("   Rejets cleaning (causes):")
            for reason, count in sorted(self.cleaning_rejects.items(), key=lambda x: -x[1]):
                if count > 0:
                    console_write(f"      - {reason}: {count}")
            if self.cleaning_reject_examples:
                console_write("   Exemples de rejets:")
                for ex in self.cleaning_reject_examples:
                    title_preview = ex["title"] if ex["title"] else "<titre vide>"
                    console_write(f"      - [{ex['source']}] {ex['reason']} | {title_preview}")
        return cleaned

    def _classify_cleaning_reject(self, article) -> str:
        """Explique la cause principale d'un rejet de nettoyage."""
        title = (article.title or "").strip()
        content = (article.content or "").strip()
        url = (article.url or "").strip()
        if not title:
            return "empty_title"
        if not content:
            return "empty_content"
        if len(title) <= 3:
            return "title_too_short"
        if len(content) <= 10:
            return "content_too_short"
        if url and not (url.startswith("http://") or url.startswith("https://")):
            return "invalid_url"
        return "other_invalid"

    def _print_source_traceability(self):
        """Affiche la traçabilité par source avec delta vs run précédent."""
        console_write = self.console.write
        self.source_anomalies = []
        warn_drop_pct = _env_float("SOURCE_DROP_WARN_PCT", 80.0, minimum=1.0, maximum=100.0)
        console_write("\n" + "=" * 70)
        console_write("[SOURCE TRACEABILITY] Volumes et deltas")
        console_write("=" * 70)
        if not self.source_run_stats:
            console_write("   Aucune source active dans ce run.")
            return

        c = self.db.conn.cursor()
        for source_name in sorted(self.source_run_stats.keys()):
            stats = self.source_run_stats[source_name]
            prev = c.execute(
                """
                SELECT sl.rows_synced
                FROM sync_log sl
                JOIN source s ON s.source_id = sl.source_id
                WHERE s.name = ? AND sl.status = 'OK'
                ORDER BY sl.sync_date DESC
                LIMIT 1 OFFSET 1
                """,
                (source_name,),
            ).fetchone()
            prev_rows = int(prev[0]) if prev else 0
            current_rows = int(stats["extracted"])
            if prev_rows > 0:
                delta_pct = ((current_rows - prev_rows) / prev_rows) * 100.0
                delta_txt = f"{delta_pct:+.1f}%"
                if current_rows == 0:
                    self.source_anomalies.append(
                        f"source {source_name}: volume nul (prev={prev_rows}, now=0)"
                    )
                elif delta_pct <= -warn_drop_pct:
                    self.source_anomalies.append(
                        f"source {source_name}: chute volume {delta_pct:.1f}% (prev={prev_rows}, now={current_rows})"
                    )
            else:
                delta_txt = "n/a"
            console_write(
                "   "
                f"{source_name:<28} now={current_rows:>4} prev={prev_rows:>4} "
                f"delta={delta_txt:>7} status={stats['status']}"
            )

    def _is_foundation_source(self, source_name: str) -> tuple[bool, str, bool]:
        """
        Détermine si une source est statique (fondation) et son type

        Returns:
            (is_foundation, foundation_type, should_freeze)
            - is_foundation: True si source fondation
            - foundation_type: Type de fondation
            - should_freeze: True si doit être figée après première intégration
        """
        source_lower = source_name.lower()

        # Fondations DYNAMIQUES (collecte quotidienne) - Vérifier EN PREMIER
        if "gdelt_last15" in source_lower or source_name == "GDELT_Last15_English":
            return True, "bigdata", False  # GDELT Last15 = dynamique (collecte quotidienne)
        elif "gdelt_master" in source_lower or source_name == "GDELT_Master_List":
            return True, "bigdata", False  # GDELT Master = dynamique (collecte quotidienne)

        # Fondations à FIGER après première intégration
        elif "kaggle" in source_lower:
            return True, "flat_files", True  # Kaggle = figé
        elif source_name == "gdelt_events" or source_lower == "gdelt_events":
            return True, "bigdata", True  # gdelt_events = figé
        elif "zzdb" in source_lower and "csv" in source_lower:
            # zzdb_csv reste une fondation, mais on autorise la ré-ingestion
            # (déduplication par fingerprint protège la base)
            return True, "db_non_relational", False

        return False, "real_source", False  # Source dynamique (RSS, API, etc.)

    def load(self, articles: list):
        """Load to database + tag topics + analyze sentiment"""
        console_write = self.console.write
        console_write("\n" + UiMessages.loading_title()[0])
        console_write(UiMessages.loading_title()[1])
        console_write(UiMessages.loading_title()[2])
        logger.info("Loading start: {} articles", len(articles))
        total_to_process = len(articles)
        console_write(f"\n   Articles à traiter: {total_to_process:,}")
        console_write("   Vérification des doublons (fingerprint SHA256)...")
        if total_to_process > 1000:
            console_write(
                f"   Traitement de {total_to_process:,} articles (cela peut prendre plusieurs minutes)..."
            )
            console_write("   Progression: ", end="", flush=True)

        # Create sources partition dir for today
        today = date.today()
        project_root = Path(__file__).parent.parent.parent
        sources_dir = project_root / "data" / "raw" / f"sources_{today:%Y-%m-%d}"
        sources_dir.mkdir(parents=True, exist_ok=True)

        # Track foundation integrations (première fois)
        foundation_sources = {}  # {source_name: (count, source_type, file_path)}

        # Save articles as JSON
        articles_data = []
        zzdb_loaded = 0  # Compteur ZZDB
        total_articles = len(articles)
        show_progress = total_articles > 1000

        for idx, (article, source_name) in enumerate(articles, 1):
            # Afficher progression tous les 100 articles si beaucoup d'articles
            if show_progress and idx % 100 == 0:
                console_write(".", end="", flush=True)
            source_id = self.db.get_source_id(source_name)
            if source_id:
                # Load article and get ID
                raw_data_id = self.db.load_article_with_id(article, source_id)
                if raw_data_id:
                    self.stats["loaded"] += 1
                    articles_loaded_total.inc()

                    # Compteur ZZDB
                    if "zzdb" in source_name.lower():
                        zzdb_loaded += 1

                    # Track foundation sources (statiques) pour logging
                    is_foundation, foundation_type, _should_freeze = self._is_foundation_source(
                        source_name
                    )
                    if is_foundation:
                        if source_name not in foundation_sources:
                            foundation_sources[source_name] = [0, foundation_type, None]
                        foundation_sources[source_name][0] += 1
                    # Tag topics (max 2)
                    if self.tagger.tag(raw_data_id, article.title, article.content):
                        self.stats["tagged"] += 1
                        # Get topics for metrics
                        c = self.db.conn.cursor()
                        topics = c.execute(
                            """
                            SELECT t.name FROM document_topic dt
                            JOIN topic t ON dt.topic_id = t.topic_id
                            WHERE dt.raw_data_id = ?
                        """,
                            (raw_data_id,),
                        ).fetchall()
                        for (topic_name,) in topics:
                            articles_tagged_total.labels(topic=topic_name).inc()
                    # Analyze sentiment
                    if self.analyzer.save(raw_data_id, article.title, article.content):
                        self.stats["analyzed"] += 1
                        # Get sentiment for metrics
                        c = self.db.conn.cursor()
                        sent = c.execute(
                            """
                            SELECT label FROM model_output
                            WHERE raw_data_id = ? AND model_name = 'sentiment_keyword'
                        """,
                            (raw_data_id,),
                        ).fetchone()
                        if sent:
                            articles_analyzed_total.labels(sentiment=sent[0]).inc()
                else:
                    self.stats["deduplicated"] += 1
                    articles_deduplicated_total.inc()

                articles_data.append(
                    {
                        "source": source_name,
                        "title": article.title,
                        "content": article.content,
                        "url": article.url,
                        "published_at": article.published_at,
                    }
                )
            else:
                logger.warning("Source '{}' not found in DB", source_name)

        # Write raw_articles.json
        articles_file = sources_dir / "raw_articles.json"
        with open(articles_file, "w", encoding="utf-8") as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=2)

        # Also write raw_articles.csv for easy viewing
        articles_csv = sources_dir / "raw_articles.csv"
        import csv as csv_lib

        with open(articles_csv, "w", newline="", encoding="utf-8") as f:
            if articles_data:
                w = csv_lib.DictWriter(
                    f, fieldnames=["source", "title", "content", "url", "published_at"]
                )
                w.writeheader()
                w.writerows(articles_data)

        # Logger les intégrations de fondation (première fois)
        for source_name, (count, foundation_type, _) in foundation_sources.items():
            if count > 0:
                source_id = self.db.get_source_id(source_name)
                if source_id:
                    # Vérifier si c'est la première intégration
                    if not self.db.is_foundation_integrated(source_name):
                        # Trouver le chemin du fichier source
                        file_path = None
                        file_size = None
                        if "zzdb" in source_name.lower() and "csv" in source_name.lower():
                            csv_path = (
                                project_root / "data" / "raw" / "zzdb_csv" / "zzdb_dataset.csv"
                            )
                            if not csv_path.exists():
                                csv_path = project_root / "zzdb" / "export" / "zzdb_dataset.csv"
                            if csv_path.exists():
                                file_path = str(csv_path)
                                file_size = csv_path.stat().st_size

                        # Logger l'intégration de fondation
                        self.db.log_foundation_integration(
                            source_id=source_id,
                            source_name=source_name,
                            source_type=foundation_type,
                            file_path=file_path,
                            file_size=file_size,
                            rows_integrated=count,
                            status="INTEGRATED",
                            notes="Première intégration - Source statique (fondation) pour structurer le dataset",
                        )

                        # Message détaillé pour ZZDB
                        if "zzdb" in source_name.lower():
                            for line in UiMessages.zzdb_connection_lines(
                                source_name, count, file_path
                            ):
                                console_write(line)
                        else:
                            console_write(
                                f"\n   [FONDATION] {source_name} integree : {count} articles (premiere fois)"
                            )

        if show_progress:
            console_write()  # Nouvelle ligne après les points de progression

        # Résumé clair de la déduplication
        logger.info(
            "Loading summary: processed={}, loaded={}, deduplicated={}",
            total_to_process,
            self.stats["loaded"],
            self.stats["deduplicated"],
        )
        console_write("\n" + UiMessages.resume_title())
        console_write(f"   Articles traites: {total_to_process:,}")
        console_write(f"   Nouveaux articles charges: {self.stats['loaded']:,}")
        console_write(f"   Articles dedupliques (deja presents): {self.stats['deduplicated']:,}")
        console_write(f"\n   Explication: {total_to_process:,} articles extraits et nettoyes")
        console_write(
            f"                {self.stats['deduplicated']:,} etaient deja dans la DB (meme fingerprint)"
        )
        console_write(f"                {self.stats['loaded']:,} nouveaux articles ajoutes a la DB")

        if zzdb_loaded > 0:
            console_write(UiMessages.zzdb_loaded_line(zzdb_loaded))
        console_write("\n   Enrichissement:")
        console_write(f"   Tagged: {self.stats['tagged']}")
        console_write(f"   Analyzed: {self.stats['analyzed']}")
        console_write("\n   Fichiers sauvegardes:")
        console_write(f"   {articles_file}")
        console_write(f"   {articles_csv}")

    def show_stats(self):
        """Display final statistics"""
        console_write = self.console.write
        console_write("\n" + UiMessages.stats_title()[0])
        console_write(UiMessages.stats_title()[1])
        console_write(UiMessages.stats_title()[2])
        logger.info(
            "Stats: extracted={}, cleaned={}, loaded={}, deduplicated={}, tagged={}, analyzed={}",
            self.stats["extracted"],
            self.stats["cleaned"],
            self.stats["loaded"],
            self.stats["deduplicated"],
            self.stats["tagged"],
            self.stats["analyzed"],
        )
        console_write(f"   Extracted:    {self.stats['extracted']:,} articles (toutes sources)")
        console_write(f"   Cleaned:      {self.stats['cleaned']:,} articles (valides)")
        console_write(
            f"   Loaded:       {self.stats['loaded']:,} nouveaux articles (ajoutes a la DB)"
        )
        console_write(
            f"   Deduplicated: {self.stats['deduplicated']:,} articles (deja presents, non ajoutes)"
        )
        console_write("\n   Note: Les articles dedupliques sont ceux deja presents dans la base")
        console_write("         avec le meme fingerprint (hash SHA256 du titre+contenu)")

        stats = self.db.get_stats()
        total = sum(stats.values())
        console_write(f"\n   Database: {total:,} total records (tous articles depuis le debut)")
        console_write("\n   By source:")
        for name, count in sorted(stats.items(), key=lambda x: -x[1]):
            console_write(f"      • {name}: {count:,}")
        console_write("=" * 70 + "\n")

    def _build_run_contract(self) -> tuple[str, list[str], dict[str, float]]:
        """Construit un statut de run lisible (PASS/WARN/FAIL) + KPI clés."""
        reasons: list[str] = []
        min_loaded = _env_int("MIN_LOADED_THRESHOLD", 20, minimum=0, maximum=1_000_000)
        min_enriched_ratio = _env_float("MIN_ENRICHED_RATIO", 0.95, minimum=0.0, maximum=1.0)
        min_clean_ratio = _env_float("MIN_CLEAN_RATIO", 0.90, minimum=0.0, maximum=1.0)
        if self.stats["extracted"] <= 0:
            reasons.append("Aucun article extrait")
        if self.stats["cleaned"] > self.stats["extracted"]:
            reasons.append("Incohérence: cleaned > extracted")
        if self.stats["loaded"] < min_loaded:
            reasons.append(
                f"loaded sous seuil ({self.stats['loaded']} < MIN_LOADED_THRESHOLD={min_loaded})"
            )
        if self.stats["tagged"] < self.stats["loaded"] or self.stats["analyzed"] < self.stats["loaded"]:
            reasons.append("Couverture enrichissement incomplète")
        run_duration_sec = (datetime.now() - self.run_started_at).total_seconds()
        enriched_ratio = 0.0
        clean_ratio = 0.0
        if self.stats["extracted"] > 0:
            clean_ratio = self.stats["cleaned"] / self.stats["extracted"]
        if self.stats["loaded"] > 0:
            enriched_ratio = min(self.stats["tagged"], self.stats["analyzed"]) / self.stats["loaded"]
        if clean_ratio < min_clean_ratio:
            reasons.append(
                f"clean_ratio sous seuil ({clean_ratio * 100:.1f}% < MIN_CLEAN_RATIO={min_clean_ratio * 100:.1f}%)"
            )
        if enriched_ratio < min_enriched_ratio:
            reasons.append(
                f"enriched_ratio sous seuil ({enriched_ratio * 100:.1f}% < MIN_ENRICHED_RATIO={min_enriched_ratio * 100:.1f}%)"
            )
        reasons.extend(self.source_anomalies)
        status = "PASS" if not reasons else "WARN"
        kpis = {
            "extracted": float(self.stats["extracted"]),
            "cleaned": float(self.stats["cleaned"]),
            "loaded": float(self.stats["loaded"]),
            "deduplicated": float(self.stats["deduplicated"]),
            "clean_ratio": clean_ratio,
            "enriched_ratio": enriched_ratio,
            "run_duration_sec": run_duration_sec,
            "min_loaded_threshold": float(min_loaded),
            "min_clean_ratio": min_clean_ratio,
            "min_enriched_ratio": min_enriched_ratio,
        }
        return status, reasons, kpis

    def _persist_run_summary(self, status: str, reasons: list[str], kpis: dict[str, float]) -> None:
        """Persist un résumé de run JSON dans reports/ pour le cockpit."""
        try:
            root = Path(__file__).parent.parent.parent
            out_dir = root / "reports"
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
            payload = {
                "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "status": status,
                "reasons": reasons,
                "kpis": kpis,
                "source_traceability": self.source_run_stats,
            }
            out_path = out_dir / f"run_summary_{ts}.json"
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info("Run summary persisted: {}", out_path)
        except Exception as e:
            logger.warning("Run summary persistence failed: {}", str(e)[:120])

    def run(
        self,
        inject_csv_path: str | None = None,
        inject_source_name: str = "csv_inject",
    ):
        """Run complete pipeline. inject_csv_path: CSV à injecter comme source (parcourt tout le pipeline)."""
        with MetricsCollector("full_pipeline"):
            pipeline_runs_total.inc()
            console_write = self.console.write
            console_write("\n\n" + UiMessages.pipeline_start_title()[0])
            console_write(UiMessages.pipeline_start_title()[1])
            console_write(UiMessages.pipeline_start_title()[2])
            logger.info("Pipeline run start")

            if inject_csv_path:
                self.db.ensure_source(inject_source_name, "csv", inject_csv_path)

            # ETAPE 1: Extract + Clean + Load
            articles = self.extract(
                inject_csv_path=inject_csv_path,
                inject_source_name=inject_source_name,
            )
            articles = self.clean(articles)
            self.load(articles)
            self.show_stats()

            # ETAPE 3: Generate RAW/SILVER/GOLD exports
            console_write("\n" + UiMessages.exports_title()[0])
            console_write(UiMessages.exports_title()[1])
            console_write(UiMessages.exports_title()[2])
            logger.info("Exports start: RAW/SILVER/GOLD")
            try:
                db_path = os.getenv(
                    "DB_PATH", str(Path.home() / "datasens_project" / "datasens.db")
                )
                aggregator = DataAggregator(db_path)
                exporter = GoldExporter()

                # RAW
                df_raw = aggregator.aggregate_raw()
                r_raw = exporter.export_raw(df_raw)
                console_write(f"   OK RAW CSV: {r_raw['csv']} ({r_raw['rows']} rows)")

                # SILVER (incrémental: seulement les nouveaux raw_data_id)
                df_silver = aggregator.aggregate_silver(incremental=True)
                r_silver = exporter.export_silver(df_silver)
                silver_label = "incrémental" if df_silver.empty else f"{r_silver['rows']} nouvelles lignes"
                console_write(f"   OK SILVER: {r_silver.get('parquet', r_silver['csv'])} ({silver_label})")

                # GOLD
                df_gold = aggregator.aggregate()
                r_gold = exporter.export_all(df_gold, date.today())
                console_write(f"   OK GOLD parquet: {r_gold['parquet']}")
                console_write(f"   OK GOLD CSV: {r_gold['csv']} ({r_gold['rows']} rows)")

                aggregator.close()
                logger.info("Exports complete")
            except Exception as e:
                logger.error("Export error: {}", str(e)[:100])

            # ETAPE 4: Rapport de collecte session actuelle
            try:
                db_path = os.getenv(
                    "DB_PATH", str(Path.home() / "datasens_project" / "datasens.db")
                )
                report = CollectionReport(db_path, self.session_start, self.console)
                report.collect_session_stats()
                report.print_report()
                report.close()
                logger.info("Report complete")
            except Exception as e:
                logger.error("Report error: {}", str(e)[:100])

            # ETAPE 5: Dashboard d'enrichissement global
            try:
                db_path = os.getenv(
                    "DB_PATH", str(Path.home() / "datasens_project" / "datasens.db")
                )
                dashboard = DataSensDashboard(db_path, self.console)
                dashboard.collect_stats()
                dashboard.print_dashboard()
                dashboard.close()
                logger.info("Dashboard complete")
            except Exception as e:
                logger.error("Dashboard error: {}", str(e)[:100])

            # Update database stats for metrics
            try:
                stats = self.db.get_stats()
                total = stats.get("total", 0)
                # Count enriched articles
                c = self.db.conn.cursor()
                enriched = c.execute(
                    """
                    SELECT COUNT(DISTINCT dt.raw_data_id)
                    FROM document_topic dt
                    JOIN model_output mo ON dt.raw_data_id = mo.raw_data_id
                    WHERE mo.model_name = 'sentiment_keyword'
                """
                ).fetchone()[0]
                update_database_stats(total, enriched)
                logger.info("Metrics database stats updated")
            except Exception as e:
                logger.warning("Metrics update failed: {}", str(e)[:120])

            # Traçabilité par source (anti-boite-noire)
            self._print_source_traceability()

            # Contrat de run (anti boite noire) : statut + KPI + causes
            status, reasons, kpis = self._build_run_contract()
            console_write("\n" + "=" * 70)
            console_write("[RUN CONTRACT] Synthese d'execution")
            console_write("=" * 70)
            console_write(f"   RUN_STATUS: {status}")
            console_write(f"   extracted: {int(kpis['extracted']):,}")
            console_write(f"   cleaned: {int(kpis['cleaned']):,}")
            console_write(f"   loaded: {int(kpis['loaded']):,}")
            console_write(f"   deduplicated: {int(kpis['deduplicated']):,}")
            console_write(f"   clean_ratio: {kpis['clean_ratio'] * 100:.1f}%")
            console_write(f"   enriched_ratio: {kpis['enriched_ratio'] * 100:.1f}%")
            console_write(f"   run_duration_sec: {kpis['run_duration_sec']:.1f}")
            console_write(
                "   quality_gates: "
                f"MIN_LOADED_THRESHOLD={int(kpis['min_loaded_threshold'])}, "
                f"MIN_CLEAN_RATIO={kpis['min_clean_ratio'] * 100:.1f}%, "
                f"MIN_ENRICHED_RATIO={kpis['min_enriched_ratio'] * 100:.1f}%"
            )
            if reasons:
                console_write("   WARN_REASONS:")
                for reason in reasons:
                    console_write(f"      - {reason}")
            logger.info("Run contract: status={}, reasons={}", status, reasons)
            self._persist_run_summary(status, reasons, kpis)

        # Close DB connections
        try:
            self.db.conn.close()
            self.tagger.close()
            self.analyzer.close()
        except Exception as e:
            logger.debug("Resource cleanup warning: {}", str(e)[:120])
