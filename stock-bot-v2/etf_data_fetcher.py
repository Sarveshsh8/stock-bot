"""
ETF and Stock Data Fetcher
Fetches raw data from Yahoo Finance for ETFs and stocks defined in config.yaml
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import yaml

class SimpleETFDataFetcher:
    def __init__(self, config_file='config.yaml'):
        """Initialize with ETFs and stocks from config file"""
        self.config_file = config_file
        self.config = self.load_config()
        self.etf_symbols = []
        self.stock_symbols = []
        self.all_symbols = []
        self.symbol_names = {}
        self.symbol_categories = {}
        self.symbol_types = {}  # 'ETF' or 'Stock'
        self.data = {}
        
        # Load ETF and stock information from config
        self.load_symbols_config()
        
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found. Using default configuration.")
            return self.get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration if config file is not available"""
        return {
            'etfs': [
                {'symbol': 'SPY', 'name': 'SPDR S&P 500 ETF Trust', 'category': 'US Large Cap'},
                {'symbol': 'QQQ', 'name': 'Invesco QQQ Trust', 'category': 'US Technology'},
                {'symbol': 'IWM', 'name': 'iShares Russell 2000 ETF', 'category': 'US Small Cap'},
                {'symbol': 'VTI', 'name': 'Vanguard Total Stock Market ETF', 'category': 'US Total Market'},
                {'symbol': 'VEA', 'name': 'Vanguard FTSE Developed Markets ETF', 'category': 'International Developed'},
                {'symbol': 'VWO', 'name': 'Vanguard FTSE Emerging Markets ETF', 'category': 'International Emerging'},
                {'symbol': 'AGG', 'name': 'iShares Core U.S. Aggregate Bond ETF', 'category': 'US Bonds'},
                {'symbol': 'GLD', 'name': 'SPDR Gold Trust', 'category': 'Commodities'},
                {'symbol': 'XLF', 'name': 'Financial Select Sector SPDR Fund', 'category': 'Financial Sector'},
                {'symbol': 'XLK', 'name': 'Technology Select Sector SPDR Fund', 'category': 'Technology Sector'}
            ],
            'stocks': [
                {'symbol': 'AAPL', 'name': 'Apple Inc.', 'category': 'Technology'},
                {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'category': 'Technology'},
                {'symbol': 'GOOGL', 'name': 'Alphabet Inc. Class A', 'category': 'Technology'},
                {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'category': 'Consumer Discretionary'},
                {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'category': 'Automotive'}
            ],
            'data_settings': {
                'default_period_months': 3,
                'output_directory': 'etf_data',
                'excel_filename': 'etf_raw_data.xlsx'
            }
        }
    
    def load_symbols_config(self):
        """Load ETF and stock symbols, names, and categories from config"""
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
        
    def fetch_data(self, period_months=3, symbols=None):
        """
        Fetch raw ETF and stock data for the specified period
        
        Args:
            period_months (int): Number of months of data to fetch (default: 3)
            symbols (list): List of symbols to fetch. If None, fetches all configured symbols
        """
        # Use provided symbols or all configured symbols
        if symbols is None:
            symbols_to_fetch = self.all_symbols
        else:
            symbols_to_fetch = symbols
            # Validate symbols
            invalid_symbols = [s for s in symbols_to_fetch if s not in self.all_symbols]
            if invalid_symbols:
                print(f"Warning: Invalid symbols {invalid_symbols} will be skipped")
                symbols_to_fetch = [s for s in symbols_to_fetch if s in self.all_symbols]
        
        print("Fetching ETF and Stock data from Yahoo Finance...")
        print(f"Period: Last {period_months} months")
        print(f"Symbols to fetch: {symbols_to_fetch}")
        print("=" * 60)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_months * 30)
        
        for symbol in symbols_to_fetch:
            try:
                symbol_type = self.symbol_types.get(symbol, 'Unknown')
                print(f"Fetching {symbol} ({self.symbol_names[symbol]}) [{symbol_type}]...")
                
                # Download raw data
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if not data.empty:
                    self.data[symbol] = data
                    print(f"   {symbol}: {len(data)} days of data")
                    print(f"   Columns: {list(data.columns)}")
                    print(f"   Date range: {data.index[0].date()} to {data.index[-1].date()}")
                else:
                    print(f"   {symbol}: No data available")
                    
            except Exception as e:
                print(f"   {symbol}: Error - {str(e)}")
        
        print("=" * 60)
        print(f"Data fetch complete! Retrieved data for {len(self.data)} symbols")
        
    def save_to_csv(self, output_dir=None):
        """Save all data to CSV files in separate folders for ETFs and stocks"""
        if not self.data:
            print("No data available. Run fetch_data() first.")
            return
            
        # Use config setting if no output_dir specified
        if output_dir is None:
            base_output_dir = self.config['data_settings']['output_directory']
        else:
            base_output_dir = output_dir
            
        # Create separate directories for ETFs and stocks
        etf_dir = os.path.join(base_output_dir, 'etfs')
        stock_dir = os.path.join(base_output_dir, 'stocks')
        
        os.makedirs(etf_dir, exist_ok=True)
        os.makedirs(stock_dir, exist_ok=True)
        
        print(f"\nSaving data to CSV files...")
        print(f"ETF data will be saved to: {etf_dir}")
        print(f"Stock data will be saved to: {stock_dir}")
        
        for symbol, data in self.data.items():
            symbol_type = self.symbol_types.get(symbol, 'Unknown')
            
            if symbol_type == 'ETF':
                target_dir = etf_dir
            elif symbol_type == 'Stock':
                target_dir = stock_dir
            else:
                target_dir = base_output_dir  # fallback
            
            filename = f"{symbol}_data.csv"
            filepath = os.path.join(target_dir, filename)
            data.to_csv(filepath)
            print(f"Saved {symbol} [{symbol_type}]: {filepath}")
            
        print(f"\nAll data saved with proper organization!")
        
    def save_to_excel(self, filename=None):
        """Save all data to Excel file with separate sheets for ETFs and stocks"""
        if not self.data:
            print("No data available. Run fetch_data() first.")
            return
            
        # Use config setting if no filename specified
        if filename is None:
            filename = self.config['data_settings']['excel_filename']
            
        print(f"\nSaving data to Excel file: {filename}")
        print("Creating separate sheets for ETFs and stocks...")
        
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
            if etf_data:
                for symbol, data in etf_data.items():
                    data_export = data.copy()
                    if hasattr(data_export.index, 'tz') and data_export.index.tz is not None:
                        data_export.index = data_export.index.tz_localize(None)
                    data_export.to_excel(writer, sheet_name=f'ETF_{symbol}')
                    print(f"Saved ETF sheet: ETF_{symbol}")
            
            # Save Stock data
            if stock_data:
                for symbol, data in stock_data.items():
                    data_export = data.copy()
                    if hasattr(data_export.index, 'tz') and data_export.index.tz is not None:
                        data_export.index = data_export.index.tz_localize(None)
                    data_export.to_excel(writer, sheet_name=f'Stock_{symbol}')
                    print(f"Saved Stock sheet: Stock_{symbol}")
        
        print(f"All data saved to {filename} with organized sheets")
        
    def display_data_info(self):
        """Display information about the fetched data"""
        if not self.data:
            print("No data available. Run fetch_data() first.")
            return
            
        print("\nDATA SUMMARY:")
        print("=" * 50)
        
        for symbol, data in self.data.items():
            category = self.symbol_categories.get(symbol, 'Unknown')
            symbol_type = self.symbol_types.get(symbol, 'Unknown')
            print(f"\n{symbol} - {self.symbol_names[symbol]}")
            print(f"  Type: {symbol_type}")
            print(f"  Category: {category}")
            print(f"  Rows: {len(data)}")
            print(f"  Columns: {list(data.columns)}")
            print(f"  Date range: {data.index[0].date()} to {data.index[-1].date()}")
            print(f"  Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
            
    def get_data(self, symbol):
        """Get data for a specific symbol (ETF or Stock)"""
        if symbol in self.data:
            return self.data[symbol]
        else:
            print(f"No data available for {symbol}")
            return None
            
    def get_all_data(self):
        """Get all fetched data"""
        return self.data
    
    def show_config(self):
        """Display current configuration"""
        print("CURRENT CONFIGURATION:")
        print("=" * 50)
        print(f"Config file: {self.config_file}")
        print(f"Number of ETFs: {len(self.etf_symbols)}")
        print(f"Number of Stocks: {len(self.stock_symbols)}")
        print(f"Total symbols: {len(self.all_symbols)}")
        print(f"Default period: {self.config['data_settings']['default_period_months']} months")
        print(f"Output directory: {self.config['data_settings']['output_directory']}")
        print(f"Excel filename: {self.config['data_settings']['excel_filename']}")
        
        print("\nETFs configured:")
        for etf in self.config.get('etfs', []):
            print(f"  {etf['symbol']}: {etf['name']} ({etf.get('category', 'Unknown')})")
        
        print("\nStocks configured:")
        for stock in self.config.get('stocks', []):
            print(f"  {stock['symbol']}: {stock['name']} ({stock.get('category', 'Unknown')})")
    
    def add_etf(self, symbol, name, category="Unknown"):
        """Add a new ETF to the configuration"""
        new_etf = {
            'symbol': symbol,
            'name': name,
            'category': category
        }
        self.config['etfs'].append(new_etf)
        self.etf_symbols.append(symbol)
        self.etf_names[symbol] = name
        self.etf_categories[symbol] = category
        print(f"Added {symbol} to configuration")
    
    def remove_etf(self, symbol):
        """Remove an ETF from the configuration"""
        if symbol in self.etf_symbols:
            self.etf_symbols.remove(symbol)
            del self.etf_names[symbol]
            del self.etf_categories[symbol]
            self.config['etfs'] = [etf for etf in self.config['etfs'] if etf['symbol'] != symbol]
            print(f"Removed {symbol} from configuration")
        else:
            print(f"{symbol} not found in configuration")

# Example usage
if __name__ == "__main__":
    # Initialize fetcher with config file
    fetcher = SimpleETFDataFetcher('config.yaml')
    
    # Show current configuration
    fetcher.show_config()
    
    # Fetch data using default period from config
    default_period = fetcher.config['data_settings']['default_period_months']
    fetcher.fetch_data(period_months=default_period)
    
    # Display data information
    # fetcher.display_data_info()
    
    # Save to CSV files (uses config settings)
    fetcher.save_to_csv()
    
    # Save to Excel file (uses config settings)
    # fetcher.save_to_excel()
    
    print("\nRaw data fetching completed!")
