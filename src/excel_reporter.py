#!/usr/bin/env python3
"""
Excel Reporter Module

Creates Excel reports from stock data
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any

class ExcelReporter:
    def __init__(self):
        self.output_dir = "data/excel"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_report(self, data: Dict[str, Any], symbol: str) -> str:
        """Create comprehensive Excel report"""
        print("📈 Creating Excel report...")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            excel_path = os.path.join(self.output_dir, f"{symbol}_report_{timestamp}.xlsx")
            
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                # Summary sheet
                summary_data = [
                    ['Symbol', symbol],
                    ['Company', data['info'].get('longName', 'N/A')],
                    ['Current Price', f"${data.get('current_price', 'N/A')}"],
                    ['Market Cap', f"${data['info'].get('marketCap', 0):,.0f}"],
                    ['Volume', f"{data['info'].get('volume', 0):,.0f}"],
                    ['Analysis Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                ]
                
                summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Data sheets
                if not data['hist_5min'].empty:
                    hist_5min = data['hist_5min'].copy()
                    hist_5min.index = hist_5min.index.tz_localize(None)
                    hist_5min.to_excel(writer, sheet_name='5min_Data')
                
                if not data['hist_daily'].empty:
                    hist_daily = data['hist_daily'].copy()
                    hist_daily.index = hist_daily.index.tz_localize(None)
                    hist_daily.to_excel(writer, sheet_name='Daily_Data')
            
            print(f"✅ Excel saved: {excel_path}")
            return excel_path
            
        except Exception as e:
            print(f"❌ Error creating Excel: {e}")
            return ""
