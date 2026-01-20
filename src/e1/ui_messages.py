"""
Centralized UI messages for E1 console output (DRY).
"""


class UiMessages:
    @staticmethod
    def banner(title: str, width: int = 70) -> list[str]:
        line = "=" * width
        return [line, f"[{title}]", line]

    @staticmethod
    def extraction_title() -> list[str]:
        line = "=" * 70
        return [line, "[EXTRACTION] All sources", line]

    @staticmethod
    def cleaning_title() -> list[str]:
        line = "=" * 70
        return [line, "[CLEANING] Articles validation", line]

    @staticmethod
    def loading_title() -> list[str]:
        line = "=" * 70
        return [line, "[LOADING] Database ingestion + Tagging + Sentiment", line]

    @staticmethod
    def stats_title() -> list[str]:
        line = "=" * 70
        return [line, "[STATS] Pipeline results", line]

    @staticmethod
    def exports_title() -> list[str]:
        line = "=" * 70
        return [line, "[EXPORTS] RAW/SILVER/GOLD Generation", line]

    @staticmethod
    def pipeline_start_title() -> list[str]:
        line = "=" * 70
        return [line, "[START] DataSens E1+ - INGESTION + EXTRACTION PIPELINE", line]

    @staticmethod
    def resume_title() -> str:
        return "[RESUME] Chargement dans la base de donnees:"

    @staticmethod
    def zzdb_connection_lines(source_name: str, count: int, file_path: str | None) -> list[str]:
        return [
            "",
            "   [ZZDB -> DataSens] Connexion validee :",
            f"      - Source: {source_name}",
            f"      - Articles transferes: {count}",
            f"      - Fichier: {file_path or 'N/A'}",
            "      - Base ZZDB: MongoDB (zzdb) -> datasens.db",
            "      - Status: INTEGRE (fondation statique)",
        ]

    @staticmethod
    def zzdb_loaded_line(count: int) -> str:
        return f"\n   [ZZDB -> DataSens] {count} articles charges dans datasens.db"

    @staticmethod
    def report_title() -> list[str]:
        line = "=" * 80
        return [line, "[RAPPORT] COLLECTE SESSION ACTUELLE", line]

    @staticmethod
    def dashboard_title() -> list[str]:
        line = "=" * 80
        return [line, "[DASHBOARD] DATASENS - ENRICHISSEMENT DATASET", line]

    @staticmethod
    def session_resume_title() -> str:
        return "[SESSION] RESUME DE LA COLLECTE"

    @staticmethod
    def sources_detail_title() -> str:
        return "[SOURCES] DETAIL PAR SOURCE"

    @staticmethod
    def topics_distribution_title() -> str:
        return "[TOPICS] DISTRIBUTION DES TOPICS (SESSION)"

    @staticmethod
    def sentiment_distribution_title() -> str:
        return "[SENTIMENT] DISTRIBUTION DU SENTIMENT (SESSION)"

    @staticmethod
    def vision_title() -> str:
        return "[VISION] FINALITE DU PROJET"

    @staticmethod
    def dashboard_resume_title() -> str:
        return "[RESUME] RESUME GLOBAL"

    @staticmethod
    def dashboard_new_by_source_title() -> str:
        return "[NOUVEAUX] NOUVEAUX ARTICLES AUJOURD'HUI PAR SOURCE"

    @staticmethod
    def dashboard_topics_title() -> str:
        return "[TOPICS] ENRICHISSEMENT TOPICS"

    @staticmethod
    def dashboard_sentiment_title() -> str:
        return "[SENTIMENT] ENRICHISSEMENT SENTIMENT"

    @staticmethod
    def dashboard_sources_title() -> str:
        return "[SOURCES] ARTICLES PAR SOURCE"

    @staticmethod
    def dashboard_classification_title() -> str:
        return "[CLASSIFICATION DES SOURCES]"

    @staticmethod
    def dashboard_ai_title() -> str:
        return "[IA] EVALUATION DATASET POUR IA"
