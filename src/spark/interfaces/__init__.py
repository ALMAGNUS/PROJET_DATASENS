"""
Interfaces - PySpark E2
=======================
Interfaces abstraites pour PySpark (DIP)
"""

from .data_processor import DataProcessor
from .data_reader import DataReader

__all__ = ["DataProcessor", "DataReader"]
