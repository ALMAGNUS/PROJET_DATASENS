"""
Tests for E1Pipeline quiet mode.
"""

import sys
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_pipeline(monkeypatch, tmp_path, quiet: bool):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))

    import src.e1.pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "start_metrics_server", lambda *args, **kwargs: None)
    logger.remove()
    return pipeline_module.E1Pipeline(quiet=quiet)


def test_quiet_mode_suppresses_console_output(monkeypatch, tmp_path, capsys):
    pipeline = _build_pipeline(monkeypatch, tmp_path, quiet=True)
    capsys.readouterr()
    pipeline.stats = {
        "extracted": 1,
        "cleaned": 1,
        "loaded": 1,
        "deduplicated": 0,
        "tagged": 1,
        "analyzed": 1,
    }
    pipeline.show_stats()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_non_quiet_mode_outputs_console_text(monkeypatch, tmp_path, capsys):
    pipeline = _build_pipeline(monkeypatch, tmp_path, quiet=False)
    capsys.readouterr()
    pipeline.stats = {
        "extracted": 2,
        "cleaned": 2,
        "loaded": 2,
        "deduplicated": 0,
        "tagged": 2,
        "analyzed": 2,
    }
    pipeline.show_stats()
    captured = capsys.readouterr()
    assert "[STATS] Pipeline results" in captured.out
