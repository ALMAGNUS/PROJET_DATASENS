"""
Script pour lancer l'API E2 (FastAPI)
======================================
Usage: python run_e2_api.py
"""

import socket
import sys

import uvicorn

from src.config import get_settings, reset_settings
from src.logging_config import setup_logging


def _ensure_port_available(host: str, port: int, *, retries: int = 8, delay_sec: float = 1.0) -> None:
    """Refuse de démarrer si le port reste pris (même adresse que uvicorn)."""
    import time

    bind_host = "127.0.0.1" if host in ("0.0.0.0", "::", "") else host
    last_err: OSError | None = None
    for attempt in range(1, retries + 1):
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind((bind_host, port))
            return
        except OSError as exc:
            last_err = exc
            if attempt < retries:
                time.sleep(delay_sec)
        finally:
            probe.close()
    print(
        f"[DataSens] ERREUR: impossible de binder {bind_host}:{port} "
        f"(apres {retries} essais).\n"
        f"  -> .\\stop_full.bat\n"
        f"  -> .\\scripts\\kill_port_8001.ps1"
    )
    if last_err:
        print(f"  Detail: {last_err}")
    sys.exit(1)


if __name__ == "__main__":
    reset_settings()
    settings = get_settings()
    setup_logging(log_level=settings.log_level or "INFO")
    bind_host = settings.fastapi_host
    if bind_host in ("0.0.0.0", "::"):
        bind_host = "127.0.0.1"
        print(
            "[DataSens] FASTAPI_HOST=0.0.0.0 detecte sous Windows : "
            f"bind local {bind_host}:{settings.fastapi_port} (cockpit local)."
        )
    print(
        f"[DataSens] JWT session TTL: {settings.access_token_expire_minutes} min "
        f"(ACCESS_TOKEN_EXPIRE_MINUTES)"
    )

    _ensure_port_available(bind_host, settings.fastapi_port)

    uvicorn.run(
        "src.e2.api.main:app",
        host=bind_host,
        port=settings.fastapi_port,
        reload=settings.fastapi_reload,
        workers=1,
        log_level=settings.log_level.lower(),
    )
