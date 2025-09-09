"""
Yahoo Finance Data Fetcher
Handles fetching financial data from Yahoo Finance API
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import logging

class YahooFinanceFetcher:
    """Fetches financial data from Yahoo Finance"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Yahoo Finance fetcher
        
        Args:
            config: Configuration dictionary containing ETF/stock settings
        """
        self.config = config
        self.etf_symbols = []
        self.stock_symbols = []
        self.all_symbols = []
        self.symbol_names = {}
        self.symbol_categories = {}
        self.symbol_types = {}
        self.data = {}
        
        self._load_symbols_from_config()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the fetcher"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_symbols_from_config(self):
        """Load ETF and stock symbols from configuration"""
        # Load ETFs
        for etf in self.config.get('etfs', []):
            symbol = etf['symbol']
            self.etf_symbols.append(symbol)
            self.all_symbols.append(symbol)
            self.symbol_names[symbol] = etf['name']
            self.symbol_categories[symbol] = etf.get('category', 'Unknown')
            self.symbol_types[symbol] = 'ETF'
        
        # Load Stocks
        for stock in self.config.get('stocks', []):
            symbol = stock['symbol']
            self.stock_symbols.append(symbol)
            self.all_symbols.append(symbol)
            self.symbol_names[symbol] = stock['name']
            self.symbol_categories[symbol] = stock.get('category', 'Unknown')
            self.symbol_types[symbol] = 'Stock'
    
    def fetch_data(self, period_months: int = 6, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch financial data for specified symbols
        
        Args:
            period_months: Number of months of data to fetch
            symbols: List of symbols to fetch (if None, fetches all configured)
            
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        if symbols is None:
            symbols_to_fetch = self.all_symbols
        else:
            symbols_to_fetch = symbols
            # Validate symbols
            invalid_symbols = [s for s in symbols_to_fetch if s not in self.all_symbols]
            if invalid_symbols:
                self.logger.warning(f"Invalid symbols {invalid_symbols} will be skipped")
                symbols_to_fetch = [s for s in symbols_to_fetch if s in self.all_symbols]
        
        self.logger.info(f"Fetching data for {len(symbols_to_fetch)} symbols over {period_months} months")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_months * 30)
        
        for symbol in symbols_to_fetch:
            try:
                symbol_type = self.symbol_types.get(symbol, 'Unknown')
                self.logger.info(f"Fetching {symbol} ({self.symbol_names[symbol]}) [{symbol_type}]")
                
                # Download data
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if not data.empty:
                    self.data[symbol] = data
                    self.logger.info(f"Successfully fetched {len(data)} days of data for {symbol}")
                else:
                    self.logger.warning(f"No data available for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
        
        self.logger.info(f"Data fetch complete! Retrieved data for {len(self.data)} symbols")
        return self.data
    
    def get_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get data for a specific symbol"""
        return self.data.get(symbol)
    
    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        """Get all fetched data"""
        return self.data
    
    def save_to_csv(self, output_dir: str) -> Dict[str, str]:
        """
        Save all data to CSV files in organized folders
        
        Args:
            output_dir: Base output directory
            
        Returns:
            Dictionary mapping symbol to file path
        """
        if not self.data:
            self.logger.warning("No data available to save")
            return {}
        
        # Create separate directories
        etf_dir = os.path.join(output_dir, 'etfs')
        stock_dir = os.path.join(output_dir, 'stocks')
        
        os.makedirs(etf_dir, exist_ok=True)
        os.makedirs(stock_dir, exist_ok=True)
        
        saved_files = {}
        
        for symbol, data in self.data.items():
            symbol_type = self.symbol_types.get(symbol, 'Unknown')
            
            if symbol_type == 'ETF':
                target_dir = etf_dir
            elif symbol_type == 'Stock':
                target_dir = stock_dir
            else:
                target_dir = output_dir
            
            filename = f"{symbol}_data.csv"
            filepath = os.path.join(target_dir, filename)
            data.to_csv(filepath)
            saved_files[symbol] = filepath
            self.logger.info(f"Saved {symbol} [{symbol_type}] to {filepath}")
        
        return saved_files
    
    def save_to_excel(self, filename: str) -> str:
        """
        Save all data to Excel file with organized sheets
        
        Args:
            filename: Output Excel filename
            
        Returns:
            Path to saved Excel file
        """
        if not self.data:
            self.logger.warning("No data available to save")
            return ""
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Separate ETFs and stocks
            etf_data = {}
            stock_data = {}
            
            for symbol, data in self.data.items():
                symbol_type = self.symbol_types.get(symbol, 'Unknown')
                if symbol_type == 'ETF':
                    etf_data[symbol] = data
                elif symbol_type == 'Stock':
                    stock_data[symbol] = data
            
            # Save ETF data
            for symbol, data in etf_data.items():
                data_export = data.copy()
                if hasattr(data_export.index, 'tz') and data_export.index.tz is not None:
                    data_export.index = data_export.index.tz_localize(None)
                data_export.to_excel(writer, sheet_name=f'ETF_{symbol}')
                self.logger.info(f"Saved ETF sheet: ETF_{symbol}")
            
            # Save Stock data
            for symbol, data in stock_data.items():
                data_export = data.copy()
                if hasattr(data_export.index, 'tz') and data_export.index.tz is not None:
                    data_export.index = data_export.index.tz_localize(None)
                data_export.to_excel(writer, sheet_name=f'Stock_{symbol}')
                self.logger.info(f"Saved Stock sheet: Stock_{symbol}")
        
        self.logger.info(f"All data saved to {filename}")
        return filename
    
    def get_symbol_info(self) -> Dict[str, Any]:
        """Get information about configured symbols"""
        return {
            'etf_symbols': self.etf_symbols,
            'stock_symbols': self.stock_symbols,
            'all_symbols': self.all_symbols,
            'symbol_names': self.symbol_names,
            'symbol_categories': self.symbol_categories,
            'symbol_types': self.symbol_types,
            'total_count': len(self.all_symbols)
        }
