"""DataSens - Configuration Centralisée (E1 → E2/E3)"""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# BASE_DIR: Windows natif = projet, Docker = /data (override via env)
def _base_dir() -> Path:
    p = Path(__file__).resolve().parent.parent
    return p


class Settings(BaseSettings):
    """Configuration centralisée pour E1, E2, E3"""

    model_config = SettingsConfigDict(
        protected_namespaces=("settings_",),  # Évite le conflit model_device / model_
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================================
    # E1: Database & Paths (Windows + Docker)
    # ============================================================
    base_dir: str | None = Field(
        default=None,
        description="Base path (Windows: projet, Docker: /data). Path() partout dans le code.",
    )
    db_path: str = Field(default="datasens.db", description="SQLite database path")

    # ============================================================
    # E1: Pipeline Configuration
    # ============================================================
    metrics_port: int = Field(default=8000, description="Prometheus metrics port")
    disable_zzdb: bool = Field(default=False, description="Disable ZZDB synthetic data")
    zzdb_max_articles: int = Field(default=50, description="Max ZZDB articles per run")
    disable_zzdb_csv: bool = Field(default=False, description="Disable ZZDB CSV import")
    zzdb_csv_max_articles: int = Field(default=1000, description="Max ZZDB CSV articles")
    force_zzdb_reimport: bool = Field(default=False, description="Force ZZDB reimport")

    # ============================================================
    # E2: PySpark Configuration
    # ============================================================
    spark_app_name: str = Field(default="DataSens-E2", description="Spark application name")
    spark_master: str = Field(default="local[*]", description="Spark master URL")
    spark_driver_memory: str = Field(default="2g", description="Spark driver memory")
    spark_executor_memory: str = Field(default="2g", description="Spark executor memory")
    parquet_base_path: str = Field(default="data/gold", description="Base path for Parquet files")
    parquet_partition_column: str = Field(default="date", description="Partition column name")
    goldai_base_path: str = Field(
        default="data/goldai", description="Base path for GoldAI merged Parquet files"
    )

    # ============================================================
    # E3: FastAPI Configuration
    # ============================================================
    fastapi_host: str = Field(default="0.0.0.0", description="FastAPI host")
    fastapi_port: int = Field(default=8001, description="FastAPI port")
    fastapi_reload: bool = Field(default=True, description="FastAPI auto-reload")
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    cors_origins: str = Field(
        default="*",
        description="CORS allow_origins: '*' (dev) ou liste séparée par virgules (ex: http://localhost:8501,https://app.example.com)",
    )

    # ============================================================
    # E3: Security & Authentication (RBAC)
    # ============================================================
    secret_key: str = Field(
        default="your-secret-key-change-in-production", description="JWT secret key"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")
    bcrypt_rounds: int = Field(default=12, description="BCrypt hashing rounds")

    # ============================================================
    # E3: Mistral AI Configuration
    # ============================================================
    mistral_api_key: str | None = Field(default=None, description="Mistral API key")
    mistral_model: str = Field(default="mistral-medium", description="Mistral model name")
    mistral_temperature: float = Field(default=0.7, description="Mistral temperature")
    mistral_max_tokens: int = Field(default=2000, description="Mistral max tokens")

    # ============================================================
    # E3: Streamlit Configuration
    # ============================================================
    streamlit_server_port: int = Field(default=8501, description="Streamlit server port")
    streamlit_server_address: str = Field(default="0.0.0.0", description="Streamlit server address")
    streamlit_theme_base: str = Field(default="dark", description="Streamlit theme")

    # ============================================================
    # E3: ML Models Configuration
    # ============================================================
    transformers_cache_dir: str = Field(
        default=".cache/transformers", description="Transformers cache"
    )
    model_device: str = Field(default="cpu", description="Model device (cpu/cuda)")
    torch_num_threads: int = Field(
        default=4, description="PyTorch CPU threads (évite saturation RAM, ex: 4 ou 6)"
    )
    inference_batch_size: int = Field(
        default=8, description="Taille micro-batch CPU (8 pour i7, 4-6 pour i5)"
    )
    inference_max_length: int = Field(
        default=256, description="Max tokens par texte (256 = rapide, conforme spec)"
    )
    flaubert_model_path: str = Field(
        default="cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
        description="Multilingue XLM-RoBERTa (pos/neg/neu)",
    )
    camembert_model_path: str = Field(
        default="cmarkea/distilcamembert-base-sentiment",
        description="CamemBERT sentiment pré-entraîné FR (recommandé CPU)",
    )
    sentiment_fr_model_path: str = Field(
        default="ac0hik/Sentiment_Analysis_French",
        description="CamemBERT fine-tuné FR (76.54% accuracy pos/nég/neutre)",
    )
    sentiment_finetuned_model_path: str | None = Field(
        default=None,
        description="Modèle sentiment fine-tuné (prioritaire sur flaubert/camembert pour /predict)",
    )

    # ============================================================
    # E3: Monitoring & Logging
    # ============================================================
    log_level: str = Field(default="INFO", description="Log level")
    log_file: str = Field(default="logs/datasens.log", description="Log file path")
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    grafana_port: int = Field(default=3000, description="Grafana port")

    # ============================================================
    # E3: MongoDB (Optional - backup Parquet)
    # ============================================================
    mongo_uri: str = Field(default="mongodb://localhost:27017", description="MongoDB URI")
    mongo_db: str = Field(default="datasens", description="MongoDB database name")
    mongo_gridfs_bucket: str = Field(default="parquet_fs", description="GridFS bucket for Parquet")
    mongo_store_parquet: bool = Field(default=False, description="Enable Parquet backup to MongoDB")

    # ============================================================
    # E3: Redis (Optional)
    # ============================================================
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database")
    redis_password: str | None = Field(default=None, description="Redis password")

    # ============================================================
    # E3: Celery (Optional)
    # ============================================================
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0", description="Celery result backend"
    )

    # ============================================================
    # Development
    # ============================================================
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(
        default="development", description="Environment (development/staging/production)"
    )

# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get settings singleton instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Path helpers (Windows natif + Docker)
def get_base_dir() -> Path:
    """Base du projet. Windows: projet | Docker: BASE_DIR env (ex: /data)."""
    try:
        s = get_settings()
        if s.base_dir:
            return Path(s.base_dir)
    except Exception:
        pass
    return _base_dir()


def get_data_dir() -> Path:
    """Get data directory path"""
    return get_base_dir() / "data"


def get_project_root() -> Path:
    """Racine du projet (sans BASE_DIR override)."""
    return _base_dir()


def get_db_path() -> Path:
    """Chemin DB. Si base_dir défini, résolu depuis base_dir."""
    try:
        s = get_settings()
        p = Path(s.db_path)
        if s.base_dir and not p.is_absolute():
            return Path(s.base_dir) / p
        return p
    except Exception:
        return Path("datasens.db")


def get_raw_dir() -> Path:
    """Get raw data directory path"""
    return get_data_dir() / "raw"


def get_silver_dir() -> Path:
    """Get silver data directory path"""
    return get_data_dir() / "silver"


def get_gold_dir() -> Path:
    """Get gold data directory path"""
    return get_data_dir() / "gold"


def get_goldai_dir() -> Path:
    """Get goldai data directory path"""
    return get_data_dir() / "goldai"


def get_exports_dir() -> Path:
    """Get exports directory path"""
    return Path("exports")


def get_logs_dir() -> Path:
    """Get logs directory path"""
    return Path("logs")


def get_models_dir() -> Path:
    """Get models directory path"""
    return Path("models")


def get_cache_dir() -> Path:
    """Get cache directory path"""
    return Path(".cache")
