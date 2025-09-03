#!/usr/bin/env python3
"""
Docker startup script for Stock-Bot
Starts both Streamlit and Flask services
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

def start_streamlit():
    """Start Streamlit app"""
    try:
        print("Starting Streamlit app...")
        cmd = [
            "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.headless", "true",
            "--server.address", "0.0.0.0"
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Streamlit started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Error starting Streamlit: {e}")
        return None

def start_flask():
    """Start Flask API"""
    try:
        print("Starting Flask API...")
        cmd = ["python", "app.py"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Flask API started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Error starting Flask API: {e}")
        return None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    sys.exit(0)

def main():
    """Main function"""
    print("=" * 60)
    print("STOCK-BOT DOCKER CONTAINER STARTING")
    print("=" * 60)
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check if required files exist
    required_files = [
        "streamlit_app.py",
        "app.py", 
        "requirements.txt"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"ERROR: Required file {file} not found!")
            sys.exit(1)
    
    print("All required files found. Starting services...")
    
    # Start services
    streamlit_process = start_streamlit()
    time.sleep(3)  # Wait for Streamlit to start
    
    flask_process = start_flask()
    time.sleep(3)  # Wait for Flask to start
    
    if not streamlit_process or not flask_process:
        print("ERROR: Failed to start one or more services!")
        sys.exit(1)
    
    print("=" * 60)
    print("SERVICES STARTED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Streamlit App: http://localhost:8501")
    print(f"Flask API: http://localhost:5001")
    print("=" * 60)
    print("Container is running. Press Ctrl+C to stop.")
    print("=" * 60)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if streamlit_process.poll() is not None:
                print("WARNING: Streamlit process stopped unexpectedly!")
                break
                
            if flask_process.poll() is not None:
                print("WARNING: Flask process stopped unexpectedly!")
                break
                
    except KeyboardInterrupt:
        print("\nShutting down services...")
    
    finally:
        # Cleanup
        if streamlit_process:
            streamlit_process.terminate()
            streamlit_process.wait()
            print("Streamlit stopped")
            
        if flask_process:
            flask_process.terminate()
            flask_process.wait()
            print("Flask API stopped")
            
        print("All services stopped. Goodbye!")

if __name__ == "__main__":
    main()
