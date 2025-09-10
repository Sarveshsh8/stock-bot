#!/usr/bin/env python3
"""
Run the Stock Bot V3 Simple App
"""

import subprocess
import sys

def main():
    """Run the simple app"""
    print("🚀 Starting Stock Bot V3 Simple App...")
    print("📍 Running on: http://localhost:8502")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "web_app.py",
            "--server.port", "8502",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Stopping App...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
