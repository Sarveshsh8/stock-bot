"""
CSV Data Processor for Wheel Strategy Analysis
Processes CSV stock data for wheel strategy analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os
from datetime import datetime
import logging

class WheelDataProcessor:
    """Process stock CSV data for wheel strategy analysis"""
    
    def __init__(self, data_folder: str = None):
        """
        Initialize processor
        
        Args:
            data_folder: Path to wheel strategy data folder
        """
        self.data_folder = data_folder or os.path.join(os.path.dirname(__file__), '../../data')
        self.logger = logging.getLogger(__name__)
        
    def get_available_dates(self) -> List[str]:
        """Get list of available date folders"""
        try:
            dates = []
            if os.path.exists(self.data_folder):
                for item in os.listdir(self.data_folder):
                    item_path = os.path.join(self.data_folder, item)
                    if os.path.isdir(item_path) and item.isdigit() and len(item) == 8:
                        dates.append(item)
            return sorted(dates)
        except Exception as e:
            self.logger.error(f"Error getting available dates: {e}")
            return []
    
    def get_available_tickers(self, date: str) -> Dict[str, List[str]]:
        """
        Get available tickers organized by letter for a specific date
        
        Args:
            date: Date folder (e.g., '20200102')
            
        Returns:
            Dictionary with letter as key and list of tickers as value
        """
        tickers_by_letter = {}
        try:
            date_folder = os.path.join(self.data_folder, date)
            if not os.path.exists(date_folder):
                return tickers_by_letter
                
            for letter in os.listdir(date_folder):
                letter_path = os.path.join(date_folder, letter)
                if os.path.isdir(letter_path):
                    tickers = []
                    for file in os.listdir(letter_path):
                        if file.endswith('.csv'):
                            ticker = file.replace('.csv', '')
                            tickers.append(ticker)
                    tickers_by_letter[letter] = sorted(tickers)
                    
        except Exception as e:
            self.logger.error(f"Error getting available tickers for {date}: {e}")
            
        return tickers_by_letter
    
    def load_ticker_data(self, ticker: str, date: str = None) -> Optional[pd.DataFrame]:
        """
        Load CSV data for a specific ticker and date
        
        Args:
            ticker: Stock ticker symbol
            date: Date folder (e.g., '20200102'), uses latest if None
            
        Returns:
            DataFrame with stock data or None if not found
        """
        try:
            # Use latest date if none specified
            if not date:
                available_dates = self.get_available_dates()
                if not available_dates:
                    self.logger.error("No dates available")
                    return None
                date = available_dates[-1]
            
            # Determine the letter folder
            first_letter = ticker[0].upper()
            file_path = os.path.join(self.data_folder, date, first_letter, f"{ticker}.csv")
            
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                return None
                
            # Load the CSV data
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['Date', 'Ticker', 'TimeBarStart', 'FirstTradePrice', 
                              'HighTradePrice', 'LowTradePrice', 'LastTradePrice', 
                              'VolumeWeightPrice', 'Volume', 'TotalTrades']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Missing columns in {ticker} data: {missing_columns}")
                return None
                
            # Convert date and time columns
            df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
            df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['TimeBarStart'], 
                                          format='%Y-%m-%d %H:%M')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading data for {ticker} on {date}: {e}")
            return None
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for wheel strategy analysis
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional technical indicators
        """
        try:
            df = df.copy()
            
            # Basic price metrics
            df['PriceRange'] = df['HighTradePrice'] - df['LowTradePrice']
            df['PriceChange'] = df['LastTradePrice'] - df['FirstTradePrice']
            df['PriceChangePercent'] = (df['PriceChange'] / df['FirstTradePrice']) * 100
            
            # Moving averages (using volume weighted price)
            df['MA_5'] = df['VolumeWeightPrice'].rolling(window=5).mean()
            df['MA_10'] = df['VolumeWeightPrice'].rolling(window=10).mean()
            df['MA_20'] = df['VolumeWeightPrice'].rolling(window=20).mean()
            
            # Volatility measures
            df['Returns'] = df['VolumeWeightPrice'].pct_change()
            df['Volatility_10'] = df['Returns'].rolling(window=10).std() * np.sqrt(252)  # Annualized
            df['Volatility_20'] = df['Returns'].rolling(window=20).std() * np.sqrt(252)
            
            # Support and resistance levels (using rolling min/max)
            df['Support_20'] = df['LowTradePrice'].rolling(window=20).min()
            df['Resistance_20'] = df['HighTradePrice'].rolling(window=20).max()
            
            # Volume analysis
            df['AvgVolume_10'] = df['Volume'].rolling(window=10).mean()
            df['VolumeRatio'] = df['Volume'] / df['AvgVolume_10']
            
            # RSI-like indicator (simplified)
            gains = df['Returns'].where(df['Returns'] > 0, 0)
            losses = -df['Returns'].where(df['Returns'] < 0, 0)
            avg_gains = gains.rolling(window=14).mean()
            avg_losses = losses.rolling(window=14).mean()
            rs = avg_gains / avg_losses
            df['RSI'] = 100 - (100 / (1 + rs))
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def analyze_wheel_suitability(self, df: pd.DataFrame, ticker: str) -> Dict:
        """
        Analyze stock suitability for wheel strategy
        
        Args:
            df: DataFrame with stock data and technical indicators
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with suitability analysis
        """
        try:
            analysis = {
                'ticker': ticker,
                'total_bars': len(df),
                'date_range': f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}"
            }
            
            # Price analysis
            analysis['price_stats'] = {
                'current_price': float(df['VolumeWeightPrice'].iloc[-1]),
                'daily_high': float(df['HighTradePrice'].max()),
                'daily_low': float(df['LowTradePrice'].min()),
                'daily_range': float(df['HighTradePrice'].max() - df['LowTradePrice'].min()),
                'avg_price': float(df['VolumeWeightPrice'].mean()),
                'price_std': float(df['VolumeWeightPrice'].std())
            }
            
            # Volatility analysis
            if 'Volatility_20' in df.columns:
                analysis['volatility'] = {
                    'annualized_volatility': float(df['Volatility_20'].iloc[-1]) if not pd.isna(df['Volatility_20'].iloc[-1]) else 0,
                    'avg_daily_range_pct': float((df['PriceRange'] / df['VolumeWeightPrice']).mean() * 100),
                    'volatility_rank': 'High' if df['Volatility_20'].iloc[-1] > 0.3 else 'Medium' if df['Volatility_20'].iloc[-1] > 0.2 else 'Low'
                }
            
            # Volume and liquidity analysis
            analysis['liquidity'] = {
                'total_volume': int(df['Volume'].sum()),
                'avg_volume': float(df['Volume'].mean()),
                'total_trades': int(df['TotalTrades'].sum()),
                'avg_trades_per_bar': float(df['TotalTrades'].mean()),
                'liquidity_score': 'High' if df['Volume'].mean() > 10000 else 'Medium' if df['Volume'].mean() > 1000 else 'Low'
            }
            
            # Support and resistance levels
            if 'Support_20' in df.columns and 'Resistance_20' in df.columns:
                current_price = df['VolumeWeightPrice'].iloc[-1]
                support = df['Support_20'].iloc[-1]
                resistance = df['Resistance_20'].iloc[-1]
                
                analysis['levels'] = {
                    'support_level': float(support) if not pd.isna(support) else float(df['LowTradePrice'].min()),
                    'resistance_level': float(resistance) if not pd.isna(resistance) else float(df['HighTradePrice'].max()),
                    'distance_to_support_pct': float(((current_price - support) / current_price) * 100) if not pd.isna(support) else 0,
                    'distance_to_resistance_pct': float(((resistance - current_price) / current_price) * 100) if not pd.isna(resistance) else 0
                }
            
            # Wheel strategy recommendations
            current_price = analysis['price_stats']['current_price']
            volatility = analysis.get('volatility', {}).get('annualized_volatility', 0.2)
            
            # Suggest put strike prices (5%, 10%, 15% OTM)
            analysis['wheel_recommendations'] = {
                'put_strikes': {
                    '5_percent_otm': round(current_price * 0.95, 2),
                    '10_percent_otm': round(current_price * 0.90, 2),
                    '15_percent_otm': round(current_price * 0.85, 2)
                },
                'estimated_premium_pct': {
                    '5_percent_otm': round(volatility * 0.1, 2),  # Rough estimate
                    '10_percent_otm': round(volatility * 0.15, 2),
                    '15_percent_otm': round(volatility * 0.2, 2)
                },
                'suitability_score': self._calculate_suitability_score(analysis)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing wheel suitability for {ticker}: {e}")
            return {'error': str(e)}
    
    def _calculate_suitability_score(self, analysis: Dict) -> str:
        """Calculate overall suitability score for wheel strategy"""
        try:
            score = 0
            
            # Liquidity score (40% weight)
            liquidity = analysis.get('liquidity', {})
            if liquidity.get('liquidity_score') == 'High':
                score += 40
            elif liquidity.get('liquidity_score') == 'Medium':
                score += 20
            
            # Volatility score (30% weight)
            volatility = analysis.get('volatility', {})
            vol_rank = volatility.get('volatility_rank', 'Low')
            if vol_rank == 'Medium':  # Sweet spot for wheel strategy
                score += 30
            elif vol_rank == 'High':
                score += 20
            elif vol_rank == 'Low':
                score += 10
            
            # Price stability (30% weight)
            price_stats = analysis.get('price_stats', {})
            if price_stats.get('price_std', 0) > 0:
                cv = price_stats['price_std'] / price_stats.get('avg_price', 1)
                if cv < 0.02:  # Low coefficient of variation is good
                    score += 30
                elif cv < 0.05:
                    score += 20
                elif cv < 0.1:
                    score += 10
            
            # Return suitability rating
            if score >= 80:
                return 'Excellent'
            elif score >= 60:
                return 'Good'
            elif score >= 40:
                return 'Fair'
            else:
                return 'Poor'
                
        except Exception as e:
            self.logger.error(f"Error calculating suitability score: {e}")
            return 'Unknown'
    
    def prepare_analysis_text(self, analysis: Dict, df: pd.DataFrame) -> str:
        """
        Prepare formatted text for AI analysis
        
        Args:
            analysis: Analysis dictionary from analyze_wheel_suitability
            df: Original DataFrame with technical indicators
            
        Returns:
            Formatted text for prompt engineering
        """
        try:
            # Get recent data (last 20 bars or all if less)
            recent_df = df.tail(20) if len(df) > 20 else df
            
            text = f"""WHEEL STRATEGY ANALYSIS DATA FOR {analysis['ticker']}

**STOCK OVERVIEW:**
- Ticker: {analysis['ticker']}
- Analysis Period: {analysis['date_range']}
- Total Data Points: {analysis['total_bars']}
- Current Price: ${analysis['price_stats']['current_price']:.2f}

**PRICE STATISTICS:**
- Daily High: ${analysis['price_stats']['daily_high']:.2f}
- Daily Low: ${analysis['price_stats']['daily_low']:.2f}
- Daily Range: ${analysis['price_stats']['daily_range']:.2f}
- Average Price: ${analysis['price_stats']['avg_price']:.2f}
- Price Standard Deviation: ${analysis['price_stats']['price_std']:.2f}

**VOLATILITY METRICS:**"""
            
            if 'volatility' in analysis:
                vol = analysis['volatility']
                text += f"""
- Annualized Volatility: {vol['annualized_volatility']:.1%}
- Average Daily Range %: {vol['avg_daily_range_pct']:.2f}%
- Volatility Rank: {vol['volatility_rank']}"""
            
            text += f"""

**LIQUIDITY ANALYSIS:**
- Total Volume: {analysis['liquidity']['total_volume']:,}
- Average Volume: {analysis['liquidity']['avg_volume']:,.0f}
- Total Trades: {analysis['liquidity']['total_trades']:,}
- Avg Trades per Bar: {analysis['liquidity']['avg_trades_per_bar']:.1f}
- Liquidity Score: {analysis['liquidity']['liquidity_score']}"""
            
            if 'levels' in analysis:
                levels = analysis['levels']
                text += f"""

**SUPPORT/RESISTANCE LEVELS:**
- Support Level: ${levels['support_level']:.2f}
- Resistance Level: ${levels['resistance_level']:.2f}
- Distance to Support: {levels['distance_to_support_pct']:.1f}%
- Distance to Resistance: {levels['distance_to_resistance_pct']:.1f}%"""
            
            wheel = analysis['wheel_recommendations']
            text += f"""

**WHEEL STRATEGY SETUP:**
- Suitability Score: {wheel['suitability_score']}

**SUGGESTED PUT STRIKES:**
- 5% OTM: ${wheel['put_strikes']['5_percent_otm']}
- 10% OTM: ${wheel['put_strikes']['10_percent_otm']}
- 15% OTM: ${wheel['put_strikes']['15_percent_otm']}

**ESTIMATED PREMIUM COLLECTION:**
- 5% OTM: {wheel['estimated_premium_pct']['5_percent_otm']:.1%}
- 10% OTM: {wheel['estimated_premium_pct']['10_percent_otm']:.1%}
- 15% OTM: {wheel['estimated_premium_pct']['15_percent_otm']:.1%}

**RECENT PRICE ACTION (Last 20 bars):**"""
            
            # Add recent price action data
            for idx, row in recent_df.iterrows():
                text += f"""
Time: {row['TimeBarStart']} | Price: ${row['VolumeWeightPrice']:.2f} | Volume: {row['Volume']:,} | Range: ${row['PriceRange']:.2f}"""
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error preparing analysis text: {e}")
            return f"Error preparing analysis for {analysis.get('ticker', 'unknown')}: {str(e)}"
    
    def get_random_ticker_sample(self, date: str = None, count: int = 5) -> List[str]:
        """
        Get a random sample of tickers for the given date
        
        Args:
            date: Date folder (e.g., '20200102'), uses latest if None
            count: Number of tickers to return
            
        Returns:
            List of ticker symbols
        """
        try:
            # Use latest date if none specified
            if not date:
                available_dates = self.get_available_dates()
                if not available_dates:
                    return []
                date = available_dates[-1]
            
            tickers_by_letter = self.get_available_tickers(date)
            all_tickers = []
            
            for letter, tickers in tickers_by_letter.items():
                all_tickers.extend(tickers)
            
            if len(all_tickers) <= count:
                return all_tickers
            
            # Return a random sample
            import random
            return random.sample(all_tickers, count)
            
        except Exception as e:
            self.logger.error(f"Error getting random ticker sample: {e}")
            return []
