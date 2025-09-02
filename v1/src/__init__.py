#!/usr/bin/env python3
"""
Stock Analysis System - Main Module

Single entry point for all modular components
"""

# Import all classes from their respective modules
from .data_collector import DataCollector
from .chart_generator import ChartGenerator
from .excel_reporter import ExcelReporter
from .video_creator import VideoCreator
from .multimodal_analyzer import MultimodalAnalyzer
from .faiss_builder import FAISSBuilder
from .qa_system import QASystem

# Export all classes
__all__ = [
    'DataCollector',
    'ChartGenerator', 
    'ExcelReporter',
    'VideoCreator',
    'MultimodalAnalyzer',
    'FAISSBuilder',
    'QASystem'
]

# Version info
__version__ = '1.0.0'
__author__ = 'Stock Analysis System'
__description__ = 'Modular stock analysis system with continuous data collection and AI-powered insights'
