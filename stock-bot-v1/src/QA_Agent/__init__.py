"""
QA Agent Package for Financial Data Analysis

This package provides a complete FAISS-based Q&A system for financial data analysis.
"""

from .data_loader import DataLoader
from .index_builder import FAISSIndexBuilder
from .query_engine import FAISSQueryEngine
from .output_generator import FinalOutputGenerator

__version__ = "1.0.0"
__author__ = "Financial Data Analysis System"

__all__ = [
    "DataLoader",
    "FAISSIndexBuilder", 
    "FAISSQueryEngine",
    "FinalOutputGenerator"
]
