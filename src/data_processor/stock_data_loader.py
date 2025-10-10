import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import json


class StockDataLoader:
    """
    This module handles loading stock CSV files and creating metadata for each stock.
    
    How it works:
    1. It scans the stock_dataset folder to find all CSV files
    2. For each stock ticker, it reads the CSV data
    3. It creates metadata including statistics like average price, volume, date range
    4. The metadata helps in understanding what data we have for each stock
    """
    
    def __init__(self, dataset_path: str):
        """
        Initialize the data loader.
        
        Parameters:
        - dataset_path: Path to the stock_dataset folder
        """
        self.dataset_path = Path(dataset_path)
        self.metadata_cache = {}
        
    def get_available_dates(self) -> List[str]:
        """Get list of all available dates in the dataset."""
        dates = []
        for item in self.dataset_path.iterdir():
            if item.is_dir() and item.name.replace(" ", "").isdigit():
                dates.append(item.name)
        return sorted(dates)
    
    def get_stock_file_path(self, ticker: str, date: str) -> Optional[Path]:
        """
        Find the CSV file for a specific ticker and date.
        
        Parameters:
        - ticker: Stock ticker symbol (e.g., 'AAPL')
        - date: Date folder name (e.g., '20200102')
        
        Returns:
        - Path to the CSV file if found, None otherwise
        """
        first_letter = ticker[0].upper()
        date_folder = self.dataset_path / date / first_letter
        
        if not date_folder.exists():
            return None
            
        stock_file = date_folder / f"{ticker}.csv"
        return stock_file if stock_file.exists() else None
    
    def load_stock_data(self, ticker: str, date: str) -> Optional[pd.DataFrame]:
        """
        Load stock data for a specific ticker and date.
        
        Parameters:
        - ticker: Stock ticker symbol
        - date: Date string
        
        Returns:
        - DataFrame with stock data or None if not found
        """
        file_path = self.get_stock_file_path(ticker, date)
        if file_path:
            try:
                df = pd.read_csv(file_path)
                return df
            except Exception as e:
                print(f"Error loading {ticker} for {date}: {e}")
                return None
        return None
    
    def create_stock_metadata(self, ticker: str, date: str) -> Optional[Dict]:
        """
        Create metadata for a stock on a specific date.
        
        Metadata includes:
        - Ticker symbol
        - Date
        - Price statistics (open, close, high, low, average)
        - Volume statistics
        - Number of trades
        
        This metadata helps the chatbot understand the stock's trading activity.
        """
        df = self.load_stock_data(ticker, date)
        if df is None or df.empty:
            return None
        
        metadata = {
            'ticker': ticker,
            'date': date,
            'total_records': len(df),
            'first_trade_time': df['TimeBarStart'].iloc[0] if 'TimeBarStart' in df.columns else None,
            'last_trade_time': df['TimeBarStart'].iloc[-1] if 'TimeBarStart' in df.columns else None,
            'opening_price': df['FirstTradePrice'].iloc[0] if 'FirstTradePrice' in df.columns else None,
            'closing_price': df['LastTradePrice'].iloc[-1] if 'LastTradePrice' in df.columns else None,
            'high_price': df['HighTradePrice'].max() if 'HighTradePrice' in df.columns else None,
            'low_price': df['LowTradePrice'].min() if 'LowTradePrice' in df.columns else None,
            'average_price': df['VolumeWeightPrice'].mean() if 'VolumeWeightPrice' in df.columns else None,
            'total_volume': df['Volume'].sum() if 'Volume' in df.columns else None,
            'total_trades': df['TotalTrades'].sum() if 'TotalTrades' in df.columns else None,
            'price_range': (df['HighTradePrice'].max() - df['LowTradePrice'].min()) if 'HighTradePrice' in df.columns and 'LowTradePrice' in df.columns else None
        }
        
        return metadata
    
    def get_all_tickers_for_date(self, date: str) -> List[str]:
        """
        Get all available ticker symbols for a specific date.
        
        Parameters:
        - date: Date string
        
        Returns:
        - List of ticker symbols
        """
        tickers = []
        date_folder = self.dataset_path / date
        
        if not date_folder.exists():
            return tickers
        
        for letter_folder in date_folder.iterdir():
            if letter_folder.is_dir():
                for csv_file in letter_folder.glob('*.csv'):
                    tickers.append(csv_file.stem)
        
        return sorted(tickers)
    
    def create_summary_text(self, metadata: Dict) -> str:
        """
        Create a human-readable summary text from metadata.
        This text will be used for creating embeddings and searching.
        
        The summary includes key information about the stock's trading activity
        in a natural language format that's easy for the chatbot to understand.
        """
        if not metadata:
            return ""
        
        summary = f"""
Stock: {metadata['ticker']}
Date: {metadata['date']}
Trading Summary:
- Opening Price: ${metadata['opening_price']:.2f}
- Closing Price: ${metadata['closing_price']:.2f}
- High Price: ${metadata['high_price']:.2f}
- Low Price: ${metadata['low_price']:.2f}
- Average Price: ${metadata['average_price']:.2f}
- Price Range: ${metadata['price_range']:.2f}
- Total Volume: {metadata['total_volume']:,} shares
- Total Trades: {metadata['total_trades']:,} trades
- Trading Period: {metadata['first_trade_time']} to {metadata['last_trade_time']}
- Total Records: {metadata['total_records']} time bars
"""
        return summary.strip()
    
    def get_all_unique_tickers(self) -> List[str]:
        """Get all unique stock tickers across all dates."""
        dates = self.get_available_dates()
        if not dates:
            return []
        
        # Get tickers from first date (they're generally consistent)
        first_date = dates[0].replace(" ", "")
        return self.get_all_tickers_for_date(first_date)
    
    def load_all_stocks_metadata(self, limit: int = None) -> List[Dict]:
        """
        Create metadata for all unique stocks.
        
        Parameters:
        - limit: Maximum number of stocks to process (None = all stocks)
        
        Returns:
        - List of metadata dictionaries
        """
        all_metadata = []
        dates = self.get_available_dates()
        
        if not dates:
            return all_metadata
        
        # Get all unique tickers
        first_date = dates[0].replace(" ", "")
        tickers = self.get_all_tickers_for_date(first_date)
        
        # Apply limit if specified
        if limit:
            tickers = tickers[:limit]
        
        # Process each ticker
        for ticker in tickers:
            metadata = self.create_stock_metadata(ticker, first_date)
            if metadata:
                all_metadata.append(metadata)
        
        return all_metadata

