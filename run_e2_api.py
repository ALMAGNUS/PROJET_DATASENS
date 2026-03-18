"""
Script pour lancer l'API E2 (FastAPI)
======================================
Usage: python run_e2_api.py
"""

import uvicorn

from src.config import get_settings
from src.logging_config import setup_logging

if __name__ == "__main__":
    settings = get_settings()
    setup_logging(log_level=settings.log_level or "INFO")

    uvicorn.run(
        "src.e2.api.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.fastapi_reload,
        log_level=settings.log_level.lower(),
    )
