"""
DataSens E1 - Complete Python Project
======================================
Modular architecture for news data ingestion, transformation, and analysis
"""

__version__ = "1.0.0"
__author__ = "DataSens Team"

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_ROOT = Path.home() / 'datasens_project'

# Ensure data directories exist
DATA_ROOT.mkdir(parents=True, exist_ok=True)

print("[OK] DataSens E1 initialized")
print(f"   Project: {PROJECT_ROOT}")
print(f"   Data: {DATA_ROOT}")
