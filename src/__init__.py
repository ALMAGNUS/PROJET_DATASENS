"""
DataSens E1 - Complete Python Project
======================================
Modular architecture for news data ingestion, transformation, and analysis
"""

__version__ = "1.0.0"
__author__ = "DataSens Team"

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_ROOT = Path.home() / "datasens_project"

DATA_ROOT.mkdir(parents=True, exist_ok=True)
