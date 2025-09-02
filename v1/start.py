#!/usr/bin/env python3
"""
Startup Script

Quick way to start the backend service and Q&A app
"""

import subprocess
import time
import os
import sys

def main():
    print("🚀 Stock Analysis System Startup")
    print("=" * 50)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️ Please activate virtual environment first:")
        print("source .venv/bin/activate")
        return
    
    print("1. Starting backend service...")
    print("   This will collect data and build the database.")
    print("   Press Ctrl+C to stop the backend service.")
    print()
    
    try:
        # Start backend service
        subprocess.run([sys.executable, "backend_service.py"])
    except KeyboardInterrupt:
        print("\n⏹️ Backend service stopped.")
    
    print("\n2. To start the Q&A app, run:")
    print("   streamlit run qa_app.py")
    print("\n3. Or to run both together:")
    print("   python3 backend_service.py & streamlit run qa_app.py")

if __name__ == "__main__":
    main()
