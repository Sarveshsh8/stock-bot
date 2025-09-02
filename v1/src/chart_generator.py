#!/usr/bin/env python3
"""
Chart Generator Module

Creates charts from stock data and saves as images
"""

import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any

class ChartGenerator:
    def __init__(self):
        self.output_dir = "data/charts"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_price_chart(self, data: Dict[str, Any], symbol: str) -> str:
        """Create price chart with volume"""
        try:
            if data['hist_daily'].empty:
                return ""
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
            
            # Price chart
            ax1.plot(data['hist_daily'].index, data['hist_daily']['Close'], linewidth=2, color='blue')
            ax1.set_title(f'{symbol} Stock Price - Last 7 Days', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price ($)', fontsize=12)
            ax1.grid(True, alpha=0.3)
            
            # Volume chart
            ax2.bar(data['hist_daily'].index, data['hist_daily']['Volume'], color='green', alpha=0.7)
            ax2.set_title('Volume', fontsize=12)
            ax2.set_ylabel('Volume', fontsize=10)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_path = os.path.join(self.output_dir, f"{symbol}_price_chart_{timestamp}.png")
            plt.savefig(image_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Price chart saved: {image_path}")
            return image_path
            
        except Exception as e:
            print(f"❌ Error creating price chart: {e}")
            return ""
    
    def create_technical_chart(self, data: Dict[str, Any], symbol: str) -> str:
        """Create technical analysis chart"""
        try:
            if len(data['hist_daily']) < 20:
                return ""
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Calculate SMA
            sma_20 = data['hist_daily']['Close'].rolling(window=20).mean()
            sma_50 = data['hist_daily']['Close'].rolling(window=50).mean()
            
            ax.plot(data['hist_daily'].index, data['hist_daily']['Close'], label='Price', linewidth=2)
            ax.plot(data['hist_daily'].index, sma_20, label='SMA 20', linewidth=1.5, alpha=0.8)
            ax.plot(data['hist_daily'].index, sma_50, label='SMA 50', linewidth=1.5, alpha=0.8)
            
            ax.set_title(f'{symbol} Technical Analysis', fontsize=14, fontweight='bold')
            ax.set_ylabel('Price ($)', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            tech_path = os.path.join(self.output_dir, f"{symbol}_technical_chart_{timestamp}.png")
            plt.savefig(tech_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Technical chart saved: {tech_path}")
            return tech_path
            
        except Exception as e:
            print(f"❌ Error creating technical chart: {e}")
            return ""
    
    def create_all_charts(self, data: Dict[str, Any], symbol: str) -> List[str]:
        """Create all charts and return paths"""
        print("📊 Creating charts...")
        
        image_paths = []
        
        # Create price chart
        price_path = self.create_price_chart(data, symbol)
        if price_path:
            image_paths.append(price_path)
        
        # Create technical chart
        tech_path = self.create_technical_chart(data, symbol)
        if tech_path:
            image_paths.append(tech_path)
        
        print(f"✅ Created {len(image_paths)} charts")
        return image_paths
