#!/usr/bin/env python3
"""
Continuous Data Collection Script

Run this script to start continuous 5-minute data collection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import DataCollector

def main():
    print("🔄 Continuous Stock Data Collection")
    print("=" * 50)
    
    symbol = input("Enter stock symbol (default: AAPL): ").strip().upper() or "AAPL"
    
    print(f"Starting continuous data collection for {symbol}")
    print("Press Ctrl+C to stop")
    
    collector = DataCollector(symbol)
    collector.start_continuous_collection()

if __name__ == "__main__":
    main()
