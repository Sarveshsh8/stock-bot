#!/usr/bin/env python3
"""
Data Collector Module

Collects real-time 5-minute data throughout the day
"""

import yfinance as yf
import pandas as pd
import schedule
import time
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class DataCollector:
    def __init__(self, symbol: str = "AAPL"):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.data_dir = f"data/{symbol}_data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize data storage
        self.today_data = []
        self.current_price = None
        self.last_update = None
    
    def collect_current_data(self) -> Dict[str, Any]:
        """Collect current 5-minute data point"""
        try:
            # Get current 1-minute data (since 5m period is invalid)
            current_data = self.ticker.history(period="1d", interval="1m")
            
            if not current_data.empty:
                latest = current_data.iloc[-1]
                
                data_point = {
                    'timestamp': latest.name.isoformat(),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'close': float(latest['Close']),
                    'volume': int(latest['Volume']),
                    'symbol': self.symbol
                }
                
                self.current_price = data_point['close']
                self.last_update = data_point['timestamp']
                
                # Add to today's data
                self.today_data.append(data_point)
                
                print(f"✅ {self.symbol}: ${data_point['close']:.2f} at {data_point['timestamp']}")
                return data_point
            
            return {}
            
        except Exception as e:
            print(f"❌ Error collecting current data: {e}")
            return {}
    
    def save_daily_data(self):
        """Save today's collected data to file"""
        if self.today_data:
            today = datetime.now().strftime('%Y%m%d')
            filename = os.path.join(self.data_dir, f"{self.symbol}_{today}_5min_data.json")
            
            with open(filename, 'w') as f:
                json.dump(self.today_data, f, indent=2)
            
            print(f"💾 Saved {len(self.today_data)} data points to {filename}")
    
    def get_historical_data(self, days: int = 3) -> Dict[str, Any]:
        """Get historical data for analysis"""
        print(f"📊 Collecting {days} days of historical data...")
        
        try:
            # Get 5-minute data for specified days
            hist_5min = self.ticker.history(period=f"{days}d", interval="5m")
            
            # Get daily data
            hist_daily = self.ticker.history(period="1wk", interval="1d")
            
            # Get stock info
            info = self.ticker.info
            
            data = {
                'symbol': self.symbol,
                'hist_5min': hist_5min,
                'hist_daily': hist_daily,
                'info': info,
                'current_price': self.current_price,
                'last_update': self.last_update,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Collected {len(hist_5min)} 5-min data points and {len(hist_daily)} daily data points")
            return data
            
        except Exception as e:
            print(f"❌ Error collecting historical data: {e}")
            return {}
    
    def start_continuous_collection(self):
        """Start continuous 5-minute data collection"""
        print(f"🔄 Starting continuous data collection for {self.symbol}")
        print("📊 Collecting data every 5 minutes...")
        
        # Schedule data collection every 5 minutes
        schedule.every(5).minutes.do(self.collect_current_data)
        
        # Initial collection
        self.collect_current_data()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n⏹️ Stopping data collection...")
            self.save_daily_data()
            print("✅ Data collection stopped")
    
    def get_today_summary(self) -> Dict[str, Any]:
        """Get summary of today's collected data"""
        if not self.today_data:
            return {}
        
        prices = [d['close'] for d in self.today_data]
        volumes = [d['volume'] for d in self.today_data]
        
        return {
            'symbol': self.symbol,
            'data_points': len(self.today_data),
            'current_price': self.current_price,
            'day_high': max(prices),
            'day_low': min(prices),
            'total_volume': sum(volumes),
            'avg_volume': sum(volumes) / len(volumes),
            'price_change': prices[-1] - prices[0] if len(prices) > 1 else 0,
            'last_update': self.last_update
        }
