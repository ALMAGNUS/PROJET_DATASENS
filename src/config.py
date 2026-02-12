"""DataSens - Configuration Centralisée (E1 → E2/E3)"""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # E1: Database Configuration
    # ============================================================
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
    flaubert_model_path: str = Field(
        default="models/flaubert-base-uncased", description="FlauBERT model path"
    )
    camembert_model_path: str = Field(
        default="models/camembert-base", description="CamemBERT model path"
    )

    # ============================================================
    # E3: Monitoring & Logging
    # ============================================================
    log_level: str = Field(default="INFO", description="Log level")
    log_file: str = Field(default="logs/datasens.log", description="Log file path")
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    grafana_port: int = Field(default=3000, description="Grafana port")

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


# Path helpers
def get_data_dir() -> Path:
    """Get data directory path"""
    return Path("data")


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
