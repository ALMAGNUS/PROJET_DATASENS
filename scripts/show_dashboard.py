#!/usr/bin/env python3
"""DataSens Dashboard - Visualisation standalone"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from dashboard import DataSensDashboard

if __name__ == "__main__":
    db_path = str(Path.home() / 'datasens_project' / 'datasens.db')
    dashboard = DataSensDashboard(db_path)
    dashboard.collect_stats()
    dashboard.print_dashboard()
    dashboard.close()

