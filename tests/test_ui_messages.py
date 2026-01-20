"""
Unit tests for UI helpers (ConsolePrinter, UiMessages).
"""

from e1.console import ConsolePrinter
from e1.ui_messages import UiMessages


def test_console_printer_writes_when_not_quiet(capsys):
    printer = ConsolePrinter(quiet=False)
    printer.write("hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"


def test_console_printer_suppresses_when_quiet(capsys):
    printer = ConsolePrinter(quiet=True)
    printer.write("hidden")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_ui_messages_banner_default_width():
    lines = UiMessages.banner("TEST")
    assert len(lines) == 3
    assert lines[0] == "=" * 70
    assert lines[1] == "[TEST]"
    assert lines[2] == "=" * 70


def test_ui_messages_zzdb_lines():
    lines = UiMessages.zzdb_connection_lines("zzdb_csv", 42, None)
    assert "ZZDB -> DataSens" in lines[1]
    assert "Source: zzdb_csv" in lines[2]
    assert "Articles transferes: 42" in lines[3]
    assert "Fichier: N/A" in lines[4]


def test_ui_messages_titles():
    assert UiMessages.extraction_title()[1] == "[EXTRACTION] All sources"
    assert UiMessages.cleaning_title()[1] == "[CLEANING] Articles validation"
    assert UiMessages.loading_title()[1] == "[LOADING] Database ingestion + Tagging + Sentiment"
    assert UiMessages.stats_title()[1] == "[STATS] Pipeline results"
    assert UiMessages.exports_title()[1] == "[EXPORTS] RAW/SILVER/GOLD Generation"
