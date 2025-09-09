#!/usr/bin/env python3
"""
Data Loader: Load Excel and JSON data, fetch values
"""

import json
import pandas as pd
import os
from typing import Dict, Any, List

class DataLoader:
    """Load Excel and JSON data and extract values"""
    
    def __init__(self):
        self.excel_data = None
        self.json_data = None
        self.extracted_values = {}
    
    def load_excel_data(self, excel_path: str, sheet_name: str = 'Historical_Data') -> bool:
        """Load Excel file and extract trading data"""
        try:
            if not os.path.exists(excel_path):
                print(f"Error: Excel file not found: {excel_path}")
                return False
            
            # Read Excel file
            self.excel_data = pd.read_excel(excel_path, sheet_name=sheet_name, index_col=0)
            
            # Extract key values
            self.extracted_values['excel'] = {
                'shape': self.excel_data.shape,
                'columns': list(self.excel_data.columns),
                'date_range': f"{self.excel_data.index[0]} to {self.excel_data.index[-1]}",
                'current_price': float(self.excel_data['Close'].iloc[-1]),
                'current_volume': int(self.excel_data['Volume'].iloc[-1]),
                'price_range': {
                    'min': float(self.excel_data['Low'].min()),
                    'max': float(self.excel_data['High'].max())
                }
            }
            
            # Add technical indicators if available
            if 'SMA_20' in self.excel_data.columns:
                self.extracted_values['excel']['sma_20'] = float(self.excel_data['SMA_20'].iloc[-1])
            if 'SMA_50' in self.excel_data.columns:
                self.extracted_values['excel']['sma_50'] = float(self.excel_data['SMA_50'].iloc[-1])
            if 'RSI' in self.excel_data.columns:
                self.extracted_values['excel']['rsi'] = float(self.excel_data['RSI'].iloc[-1])
            
            return True
            
        except Exception as e:
            print(f"Error loading Excel data: {e}")
            return False
    
    def load_json_data(self, json_path: str) -> bool:
        """Load JSON analysis file and extract values"""
        try:
            if not os.path.exists(json_path):
                print(f"Error: JSON file not found: {json_path}")
                return False
            
            # Read JSON file
            with open(json_path, 'r', encoding='utf-8') as file:
                self.json_data = json.load(file)
            
            # Extract key values
            self.extracted_values['json'] = {
                'keys': list(self.json_data.keys()),
                'total_files_analyzed': 0,
                'analysis_type': 'Unknown',
                'timestamp': 'Unknown',
                'detailed_results_count': 0,
                'recommendations_count': 0
            }
            
            # Extract metadata
            if 'analysis_metadata' in self.json_data:
                meta = self.json_data['analysis_metadata']
                self.extracted_values['json']['total_files_analyzed'] = meta.get('total_files_analyzed', 0)
                self.extracted_values['json']['analysis_type'] = meta.get('analysis_type', 'Unknown')
                self.extracted_values['json']['timestamp'] = meta.get('timestamp', 'Unknown')
            
            # Count detailed results
            if 'detailed_results' in self.json_data:
                self.extracted_values['json']['detailed_results_count'] = len(self.json_data['detailed_results'])
            
            # Count recommendations
            if 'financial_recommendations' in self.json_data:
                self.extracted_values['json']['recommendations_count'] = len(self.json_data['financial_recommendations'])
            
            return True
            
        except Exception as e:
            print(f"Error loading JSON data: {e}")
            return False
    
    def get_extracted_values(self) -> Dict[str, Any]:
        """Get all extracted values"""
        return self.extracted_values
    
    def print_summary(self):
        """Print summary of loaded data"""
        print("\n" + "=" * 60)
        print("DATA LOADING SUMMARY")
        print("=" * 60)
        
        if 'excel' in self.extracted_values:
            excel = self.extracted_values['excel']
            print("Excel Trading Data:")
            
            if 'sma_20' in excel:
                print(f"  20-day SMA: ${excel['sma_20']:.2f}")
            if 'sma_50' in excel:
                print(f"  50-day SMA: ${excel['sma_50']:.2f}")
            if 'rsi' in excel:
                print(f"  Current RSI: {excel['rsi']:.2f}")
        
        if 'json' in self.extracted_values:
            json_data = self.extracted_values['json']
            print("\nJSON Analysis Data:")
            
        
        print("=" * 60)

def main():
    """Main function to load data"""
    
    # File paths
    excel_path = "data/Apple_Trading_Data_20250902_104928.xlsx"
    json_path = "financial_analysis_20250902_122854.json"
    
    # Initialize loader
    loader = DataLoader()
    
    print("=" * 60)
    print("STEP 1: LOADING EXCEL AND JSON DATA")
    print("=" * 60)
    
    # Load Excel data
    excel_success = loader.load_excel_data(excel_path)
    
    # Load JSON data
    json_success = loader.load_json_data(json_path)
    
    if excel_success and json_success:
        print("All data loaded successfully!")
        
        # Print summary
        loader.print_summary()
        
        # Save extracted values for next step
        extracted_values = loader.get_extracted_values()
        
        # Save to file for next step
        import pickle
        with open('step1_extracted_values.pkl', 'wb') as f:
            pickle.dump(extracted_values, f)
        
        print(f"Extracted values saved to: step1_extracted_values.pkl")
        print("Ready for Step 2: Building FAISS index")
        
    else:
        print("Data loading failed. Please check file paths and formats.")

if __name__ == "__main__":
    main()
