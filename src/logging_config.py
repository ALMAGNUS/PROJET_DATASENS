"""
Centralized logging configuration using Loguru.
"""

from pathlib import Path

from loguru import logger

from src.config import get_logs_dir


def setup_logging(
    log_level: str = "INFO",
    log_file: str | None = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
) -> None:
    """
    Configure Loguru for console and optional file logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional log file path. Defaults to logs/datasens.log.
        rotation: Log rotation policy (e.g., "10 MB", "1 day").
        retention: Log retention policy (e.g., "7 days").
    """
    logger.remove()

    logger.add(
        lambda msg: print(msg, end=""),
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
    )

    if log_file is None:
        log_file = str(get_logs_dir() / "datasens.log")

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_path,
        level=log_level,
        rotation=rotation,
        retention=retention,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
    )
