#!/bin/bash

# Stock Bot - Simple Startup Script
echo "Starting Stock Bot..."

# Activate virtual environment
source venv/bin/activate

# Start Streamlit app
streamlit run main.py --server.port 8501
