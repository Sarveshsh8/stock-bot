#!/bin/bash

# Safe startup script for Stock Bot
# Fixes PyTorch device issues and segmentation faults

echo "Starting Stock Bot (Safe Mode)..."

# Set environment variables to avoid PyTorch issues
export CUDA_VISIBLE_DEVICES=""
export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export PYTORCH_DISABLE_MPS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false

# Activate virtual environment
source venv/bin/activate

# Start Streamlit with proper configuration
streamlit run main.py --server.port 8501 --server.headless true
