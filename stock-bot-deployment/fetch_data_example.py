#!/usr/bin/env python3
"""
Example script to fetch Yahoo Finance data for ETFs and stocks
"""

import yaml
import os
from src.data.fetchers.yahoo_finance_fetcher import YahooFinanceFetcher

def main():
    # Load configuration
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Initialize the fetcher
    fetcher = YahooFinanceFetcher(config)
    
    # Show what symbols are configured
    info = fetcher.get_symbol_info()
    print(" Configured Symbols:")
    print(f"ETFs: {info['etf_symbols']}")
    print(f"Stocks: {info['stock_symbols']}")
    print(f"Total: {info['total_count']} symbols")
    print()
    
    # Fetch data for all configured symbols
    print(" Fetching data...")
    data = fetcher.fetch_data(period_months=3)  # Last 3 months
    
    if data:
        print(f" Successfully fetched data for {len(data)} symbols")
        
        # Save to CSV files
        print(" Saving to CSV files...")
        csv_files = fetcher.save_to_csv('data')
        print(f"Saved {len(csv_files)} CSV files")
        
        # Save to Excel
        print(" Saving to Excel...")
        excel_file = fetcher.save_to_excel('financial_data.xlsx')
        print(f"Saved to: {excel_file}")
        
        # Show sample data
        print("\n Sample Data:")
        for symbol, df in list(data.items())[:2]:  # Show first 2 symbols
            print(f"\n{symbol} ({fetcher.symbol_names[symbol]}):")
            print(f"  Data points: {len(df)}")
            print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")
            print(f"  Latest close: ${df['Close'].iloc[-1]:.2f}")
    else:
        print(" No data fetched")

if __name__ == "__main__":
    main()
