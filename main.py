#!/usr/bin/env python3
"""DataSens E1+ - MAIN ENTRY (Pipeline SOLID/DRY)"""
import json, sys, os, shutil, time
from pathlib import Path
from datetime import date, datetime
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from core import ContentTransformer, Source, create_extractor
from repository import Repository
from tagger import TopicTagger
from analyzer import SentimentAnalyzer
from aggregator import DataAggregator
from exporter import GoldExporter
from dashboard import DataSensDashboard
from collection_report import CollectionReport
from metrics import (
    MetricsCollector, start_metrics_server, update_database_stats,
    pipeline_runs_total, articles_extracted_total, articles_loaded_total,
    articles_tagged_total, articles_analyzed_total, articles_deduplicated_total,
    extraction_duration_seconds, source_errors_total
)


class E1Pipeline:
    """Complete E1 Pipeline"""

    def __init__(self, metrics_port: int = 8000):
        # Use environment variable or default path
        db_path = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.db = Repository(db_path)
        self.tagger = TopicTagger(db_path)
        self.analyzer = SentimentAnalyzer(db_path)
        self.stats = {'extracted': 0, 'cleaned': 0, 'loaded': 0, 'deduplicated': 0, 'tagged': 0, 'analyzed': 0}
        self.session_start = datetime.now().isoformat()
        
        # Start Prometheus metrics server
        try:
            port = int(os.getenv('METRICS_PORT', metrics_port))
            start_metrics_server(port)
        except Exception as e:
            print(f"[WARN] Metrics server failed: {e}")


    def load_sources(self) -> list:
        """Load sources from JSON config"""
        config_path = Path(__file__).parent / 'sources_config.json'
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                return [Source(**s) for s in config['sources']]
        return []

    def extract(self) -> list:
        """Extract from all sources"""
        print("\n" + "="*70)
        print("[EXTRACTION] All sources")
        print("="*70)

        sources = self.load_sources()
        articles = []

        for source in sources:
            if not source.active:
                continue

            print(f"{source.source_name}... ({source.acquisition_type})", end=" ")
            start_time = time.time()
            try:
                extractor = create_extractor(source)
                extracted = extractor.extract()
                duration = time.time() - start_time
                extraction_duration_seconds.labels(source=source.source_name).observe(duration)
                
                self.stats['extracted'] += len(extracted)
                articles_extracted_total.labels(source=source.source_name).inc(len(extracted))
                articles.extend([(a, source.source_name) for a in extracted])
                
                # Log sync to database
                source_id = self.db.get_source_id(source.source_name)
                if source_id:
                    self.db.log_sync(source_id, len(extracted), 'OK')
                
                # Message spécial pour ZZDB
                if 'zzdb' in source.source_name.lower():
                    print(f"OK {len(extracted)} articles [ZZDB → DataSens]")
                else:
                    print(f"OK {len(extracted)}")
            except Exception as e:
                source_errors_total.labels(source=source.source_name).inc()
                print(f"ERROR: {str(e)[:40]}")

        print(f"\nOK Total extracted: {self.stats['extracted']}")
        return articles

    def clean(self, articles: list) -> list:
        """Clean and validate articles"""
        print("\n" + "="*70)
        print("[CLEANING] Articles validation")
        print("="*70)

        cleaned = []
        for article, source_name in articles:
            article = ContentTransformer.transform(article)
            if article.is_valid():
                cleaned.append((article, source_name))
                self.stats['cleaned'] += 1

        print(f"OK Cleaned: {self.stats['cleaned']}")
        return cleaned

    def _is_foundation_source(self, source_name: str) -> tuple[bool, str]:
        """Détermine si une source est statique (fondation) et son type"""
        source_lower = source_name.lower()
        if 'kaggle' in source_lower:
            return True, 'flat_files'  # Fichiers plats (Kaggle)
        elif 'gdelt' in source_lower:
            return True, 'bigdata'  # Big Data (GDELT)
        elif 'zzdb' in source_lower and 'csv' in source_lower:
            return True, 'db_non_relational'  # CSV export ZZDB
        return False, 'real_source'  # Source dynamique (RSS, API, etc.)
    
    def load(self, articles: list):
        """Load to database + tag topics + analyze sentiment"""
        print("\n" + "="*70)
        print("[LOADING] Database ingestion + Tagging + Sentiment")
        print("="*70)

        # Create sources partition dir for today
        today = date.today()
        sources_dir = Path(__file__).parent / 'data' / 'raw' / f'sources_{today:%Y-%m-%d}'
        sources_dir.mkdir(parents=True, exist_ok=True)
        
        # Track foundation integrations (première fois)
        foundation_sources = {}  # {source_name: (count, source_type, file_path)}
        
        # Save articles as JSON
        articles_data = []
        zzdb_loaded = 0  # Compteur ZZDB
        for article, source_name in articles:
            source_id = self.db.get_source_id(source_name)
            if source_id:
                # Load article and get ID
                raw_data_id = self.db.load_article_with_id(article, source_id)
                if raw_data_id:
                    self.stats['loaded'] += 1
                    articles_loaded_total.inc()
                    
                    # Compteur ZZDB
                    if 'zzdb' in source_name.lower():
                        zzdb_loaded += 1
                    
                    # Track foundation sources (statiques) pour logging
                    is_foundation, foundation_type = self._is_foundation_source(source_name)
                    if is_foundation:
                        if source_name not in foundation_sources:
                            foundation_sources[source_name] = [0, foundation_type, None]
                        foundation_sources[source_name][0] += 1
                    # Tag topics (max 2)
                    if self.tagger.tag(raw_data_id, article.title, article.content):
                        self.stats['tagged'] += 1
                        # Get topics for metrics
                        c = self.db.conn.cursor()
                        topics = c.execute("""
                            SELECT t.name FROM document_topic dt 
                            JOIN topic t ON dt.topic_id = t.topic_id 
                            WHERE dt.raw_data_id = ?
                        """, (raw_data_id,)).fetchall()
                        for (topic_name,) in topics:
                            articles_tagged_total.labels(topic=topic_name).inc()
                    # Analyze sentiment
                    if self.analyzer.save(raw_data_id, article.title, article.content):
                        self.stats['analyzed'] += 1
                        # Get sentiment for metrics
                        c = self.db.conn.cursor()
                        sent = c.execute("""
                            SELECT label FROM model_output 
                            WHERE raw_data_id = ? AND model_name = 'sentiment_keyword'
                        """, (raw_data_id,)).fetchone()
                        if sent:
                            articles_analyzed_total.labels(sentiment=sent[0]).inc()
                else:
                    self.stats['deduplicated'] += 1
                    articles_deduplicated_total.inc()
                
                articles_data.append({
                    'source': source_name,
                    'title': article.title,
                    'content': article.content,
                    'url': article.url,
                    'published_at': article.published_at,
                })
            else:
                print(f"   [WARNING] Source '{source_name}' not found in DB")

        # Write raw_articles.json
        articles_file = sources_dir / 'raw_articles.json'
        with open(articles_file, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=2)
        
        # Also write raw_articles.csv for easy viewing
        articles_csv = sources_dir / 'raw_articles.csv'
        import csv as csv_lib
        with open(articles_csv, 'w', newline='', encoding='utf-8') as f:
            if articles_data:
                w = csv_lib.DictWriter(f, fieldnames=['source', 'title', 'content', 'url', 'published_at'])
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
                        if 'zzdb' in source_name.lower() and 'csv' in source_name.lower():
                            csv_path = Path(__file__).parent / 'data' / 'raw' / 'zzdb_csv' / 'zzdb_dataset.csv'
                            if not csv_path.exists():
                                csv_path = Path(__file__).parent / 'zzdb' / 'export' / 'zzdb_dataset.csv'
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
                            status='INTEGRATED',
                            notes=f'Première intégration - Source statique (fondation) pour structurer le dataset'
                        )
                        
                        # Message détaillé pour ZZDB
                        if 'zzdb' in source_name.lower():
                            print(f"\n   🔗 [ZZDB → DataSens] Connexion validée :")
                            print(f"      • Source: {source_name}")
                            print(f"      • Articles transférés: {count}")
                            print(f"      • Fichier: {file_path or 'N/A'}")
                            print(f"      • Base ZZDB: zzdb/synthetic_data.db → CSV → datasens.db")
                            print(f"      • Status: INTÉGRÉ (fondation statique)")
                        else:
                            print(f"\n   📦 [FONDATION] {source_name} intégrée : {count} articles (première fois)")
        
        print(f"\nOK Total loaded: {self.stats['loaded']}")
        if zzdb_loaded > 0:
            print(f"   🔗 ZZDB → DataSens: {zzdb_loaded} articles chargés dans datasens.db")
        print(f"   Tagged: {self.stats['tagged']}")
        print(f"   Analyzed: {self.stats['analyzed']}")
        print(f"Deduplicated: {self.stats['deduplicated']}")
        print(f"   Saved to: {articles_file} + {articles_csv}")

    def show_stats(self):
        """Display final statistics"""
        print("\n" + "="*70)
        print("[STATS] Pipeline results")
        print("="*70)
        print(f"   Extracted:    {self.stats['extracted']}")
        print(f"   Cleaned:      {self.stats['cleaned']}")
        print(f"   Loaded:       {self.stats['loaded']}")
        print(f"   Deduplicated: {self.stats['deduplicated']}")

        stats = self.db.get_stats()
        total = sum(stats.values())
        print(f"\n   Database: {total} total records")
        print("\n   By source:")
        for name, count in sorted(stats.items(), key=lambda x: -x[1]):
            print(f"      • {name}: {count}")
        print("="*70 + "\n")

    def run(self):
        """Run complete pipeline"""
        with MetricsCollector('full_pipeline'):
            pipeline_runs_total.inc()
            print("\n\n" + "="*70)
            print("[START] DataSens E1+ - INGESTION + EXTRACTION PIPELINE")
            print("="*70)

            # ETAPE 1: Extract + Clean + Load (Kaggle/GDELT déjà en local, fusionnés dans GOLD)
            articles = self.extract()
            articles = self.clean(articles)
            self.load(articles)
            self.show_stats()
            
            # ETAPE 3: Generate RAW/SILVER/GOLD exports
            print("\n" + "="*70)
            print("[EXPORTS] RAW/SILVER/GOLD Generation")
            print("="*70)
            try:
                db_path = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))
                aggregator = DataAggregator(db_path)
                exporter = GoldExporter()
                
                # RAW
                df_raw = aggregator.aggregate_raw()
                r_raw = exporter.export_raw(df_raw)
                print(f"   OK RAW CSV: {r_raw['csv']} ({r_raw['rows']} rows)")
                
                # SILVER
                df_silver = aggregator.aggregate_silver()
                r_silver = exporter.export_silver(df_silver)
                print(f"   OK SILVER CSV: {r_silver['csv']} ({r_silver['rows']} rows)")
                
                # GOLD
                df_gold = aggregator.aggregate()
                r_gold = exporter.export_all(df_gold, date.today())
                print(f"   OK GOLD parquet: {r_gold['parquet']}")
                print(f"   OK GOLD CSV: {r_gold['csv']} ({r_gold['rows']} rows)")
                
                aggregator.close()
            except Exception as e:
                print(f"   ERROR: {str(e)[:100]}")
            
            # ETAPE 4: Rapport de collecte session actuelle
            try:
                db_path = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))
                report = CollectionReport(db_path, self.session_start)
                report.collect_session_stats()
                report.print_report()
                report.close()
            except Exception as e:
                print(f"   ERROR Rapport: {str(e)[:100]}")
            
            # ETAPE 5: Dashboard d'enrichissement global
            try:
                db_path = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))
                dashboard = DataSensDashboard(db_path)
                dashboard.collect_stats()
                dashboard.print_dashboard()
                dashboard.close()
            except Exception as e:
                print(f"   ERROR Dashboard: {str(e)[:100]}")

            # Update database stats for metrics
            try:
                stats = self.db.get_stats()
                total = stats.get('total', 0)
                # Count enriched articles
                c = self.db.conn.cursor()
                enriched = c.execute("""
                    SELECT COUNT(DISTINCT dt.raw_data_id) 
                    FROM document_topic dt 
                    JOIN model_output mo ON dt.raw_data_id = mo.raw_data_id 
                    WHERE mo.model_name = 'sentiment_keyword'
                """).fetchone()[0]
                update_database_stats(total, enriched)
            except:
                pass
        
        # Close DB connections
        try:
            self.db.conn.close()
            self.tagger.close()
            self.analyzer.close()
        except:
            pass



if __name__ == "__main__":
    pipeline = E1Pipeline()
    pipeline.run()
