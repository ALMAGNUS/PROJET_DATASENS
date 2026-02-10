"""Prometheus Metrics - DataSens E1 Pipeline Monitoring"""
import time

from prometheus_client import Counter, Gauge, Histogram, start_http_server
from prometheus_client.core import CollectorRegistry

# Registry
registry = CollectorRegistry()

# Counters - Total events
pipeline_runs_total = Counter(
    "datasens_pipeline_runs_total", "Total number of pipeline runs", registry=registry
)

articles_extracted_total = Counter(
    "datasens_articles_extracted_total",
    "Total articles extracted from all sources",
    ["source"],
    registry=registry,
)

articles_loaded_total = Counter(
    "datasens_articles_loaded_total", "Total articles loaded to database", registry=registry
)

articles_tagged_total = Counter(
    "datasens_articles_tagged_total",
    "Total articles tagged with topics",
    ["topic"],
    registry=registry,
)

articles_analyzed_total = Counter(
    "datasens_articles_analyzed_total",
    "Total articles analyzed for sentiment",
    ["sentiment"],
    registry=registry,
)

articles_deduplicated_total = Counter(
    "datasens_articles_deduplicated_total", "Total articles deduplicated", registry=registry
)

# Histograms - Duration metrics
pipeline_duration_seconds = Histogram(
    "datasens_pipeline_duration_seconds",
    "Pipeline execution duration in seconds",
    ["stage"],
    registry=registry,
)

extraction_duration_seconds = Histogram(
    "datasens_extraction_duration_seconds",
    "Source extraction duration in seconds",
    ["source"],
    registry=registry,
)

# Gauges - Current state
articles_in_database = Gauge(
    "datasens_articles_in_database", "Current number of articles in database", registry=registry
)

articles_enriched = Gauge(
    "datasens_articles_enriched",
    "Current number of enriched articles (topics + sentiment)",
    registry=registry,
)

enrichment_rate = Gauge(
    "datasens_enrichment_rate", "Current enrichment rate (0-1)", registry=registry
)

sources_active = Gauge("datasens_sources_active", "Number of active sources", registry=registry)

# Error counters
pipeline_errors_total = Counter(
    "datasens_pipeline_errors_total",
    "Total pipeline errors",
    ["stage", "error_type"],
    registry=registry,
)

source_errors_total = Counter(
    "datasens_source_errors_total", "Total source extraction errors", ["source"], registry=registry
)


class MetricsCollector:
    """Context manager for pipeline metrics"""

    def __init__(self, stage: str):
        self.stage = stage
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        pipeline_duration_seconds.labels(stage=self.stage).observe(duration)
        if exc_type:
            error_type = exc_type.__name__ if exc_type else "Unknown"
            pipeline_errors_total.labels(stage=self.stage, error_type=error_type).inc()


def start_metrics_server(port: int = 8000):
    """Start Prometheus metrics HTTP server"""
    start_http_server(port, registry=registry)
    print(f"[METRICS] Prometheus metrics server started on port {port}")


def update_database_stats(total: int, enriched: int):
    """Update database statistics gauges"""
    articles_in_database.set(total)
    articles_enriched.set(enriched)
    if total > 0:
        enrichment_rate.set(enriched / total)
    else:
        enrichment_rate.set(0.0)
