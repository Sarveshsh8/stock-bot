import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def convert_timezone_naive(df):
    """
    Convert timezone-aware datetime index to timezone-naive
    """
    if df is None or df.empty:
        return df
    
    # Check if the index is a DatetimeIndex
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    
    # Also check for datetime columns and convert them
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check if column contains datetime objects
            try:
                if pd.api.types.is_datetime64_any_dtype(df[col]) or df[col].apply(lambda x: isinstance(x, pd.Timestamp)).any():
                    df[col] = pd.to_datetime(df[col]).dt.tz_localize(None)
            except:
                pass
    
    return df

def calculate_technical_indicators(df):
    """
    Calculate technical indicators for the price data
    """
    # Moving averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    # Exponential moving averages
    df['EMA_12'] = df['Close'].ewm(span=12).mean()
    df['EMA_26'] = df['Close'].ewm(span=26).mean()
    
    # MACD
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # Volume indicators
    df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
    
    # Price changes
    df['Daily_Return'] = df['Close'].pct_change()
    df['Price_Change'] = df['Close'] - df['Open']
    df['Price_Change_Pct'] = (df['Price_Change'] / df['Open']) * 100
    
    # Volatility
    df['Volatility'] = df['Daily_Return'].rolling(window=20).std()
    
    return df

def download_apple_trading_data():
    """
    Download comprehensive Apple trading data and save to Excel file
    """
    try:
        # Initialize Apple ticker
        apple = yf.Ticker("AAPL")
        
        print("Downloading Apple (AAPL) comprehensive trading data...")
        
        # Get historical data for the last 2 years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        
        print(f"Downloading data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get historical market data
        hist_data = apple.history(start=start_date, end=end_date, interval="1d")
        
        if hist_data.empty:
            print("No historical data available")
            return None
        
        # Convert timezone-aware datetime to timezone-naive
        hist_data = convert_timezone_naive(hist_data)
        
        # Calculate technical indicators
        hist_data = calculate_technical_indicators(hist_data)
        
        # Get additional market data
        info = apple.info
        
        # Get institutional holders and major holders
        institutional_holders = apple.institutional_holders
        major_holders = apple.major_holders
        
        # Get analyst recommendations
        recommendations = apple.recommendations
        
        # Get earnings dates
        earnings_dates = apple.earnings_dates
        
        # Get calendar
        calendar = apple.calendar
        
        # Get sustainability data
        sustainability = apple.sustainability
        
        # Get options data (next few expiration dates)
        options = apple.options[:5] if apple.options else []
        
        # Create Excel file with multiple sheets
        filename = f"Apple_Trading_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            # Historical Price Data with Technical Indicators
            hist_data.to_excel(writer, sheet_name='Historical_Data', index=True)
            print("Historical trading data with technical indicators added")
            
            # Company Information
            company_info = get_company_info(apple)
            if company_info is not None and not company_info.empty:
                company_info.to_excel(writer, sheet_name='Company_Info', index=False)
            print("Company information added")
            
            # Institutional Holders
            institutional_holders = get_institutional_holders(apple)
            if institutional_holders is not None and not institutional_holders.empty:
                institutional_holders.to_excel(writer, sheet_name='Institutional_Holders', index=False)
            print("Institutional holders data added")
            
            # Major Holders
            major_holders = get_major_holders(apple)
            if major_holders is not None and not major_holders.empty:
                major_holders.to_excel(writer, sheet_name='Major_Holders', index=False)
            print("Major holders data added")
            
            # Analyst Recommendations
            recommendations = get_analyst_recommendations(apple)
            if recommendations is not None and not recommendations.empty:
                recommendations.to_excel(writer, sheet_name='Analyst_Recommendations', index=False)
            print("Analyst recommendations added")
            
            # Earnings Dates
            earnings_dates = get_earnings_dates(apple)
            if earnings_dates is not None and not earnings_dates.empty:
                earnings_dates.to_excel(writer, sheet_name='Earnings_Dates', index=False)
            print("Earnings dates added")
            
            # Calendar data
            calendar = get_calendar(apple)
            if calendar is not None and not calendar.empty:
                calendar.to_excel(writer, sheet_name='Calendar', index=False)
            print("Calendar data added")
            
            # Sustainability data
            sustainability = get_sustainability(apple)
            if sustainability is not None and not sustainability.empty:
                sustainability.to_excel(writer, sheet_name='Sustainability', index=False)
            print("Sustainability data added")
            
            # Options Data (for first few expiration dates)
            options = get_options_chain(apple)
            if options:
                for expiry in list(options.keys())[:3]:  # Limit to 3 expiration dates
                    try:
                        calls = options[expiry]['calls']
                        puts = options[expiry]['puts']
                        
                        calls.to_excel(writer, sheet_name=f'Options_Calls_{expiry}', index=False)
                        puts.to_excel(writer, sheet_name=f'Options_Puts_{expiry}', index=False)
                        print(f"Options data for {expiry} added")
                    except Exception as e:
                        print(f"Could not get options data for {expiry}: {str(e)}")
        
        print(f"\nExcel file created successfully: {filename}")
        print(f"File saved in: {os.getcwd()}")
        
        # Display summary statistics
        print("\n" + "="*50)
        print("TRADING DATA SUMMARY")
        print("="*50)
        print(f"Data Period: {hist_data.index[0].strftime('%Y-%m-%d')} to {hist_data.index[-1].strftime('%Y-%m-%d')}")
        print(f"Total Trading Days: {len(hist_data)}")
        print(f"Current Price: ${hist_data['Close'].iloc[-1]:.2f}")
        print(f"Price Range: ${hist_data['Low'].min():.2f} - ${hist_data['High'].max():.2f}")
        print(f"Average Volume: {hist_data['Volume'].mean():,.0f}")
        print(f"Total Volume: {hist_data['Volume'].sum():,.0f}")
        
        # Recent price movement
        recent_return = ((hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[-2]) / hist_data['Close'].iloc[-2]) * 100
        print(f"Latest Daily Return: {recent_return:.2f}%")
        
        # Technical indicator status
        if not hist_data['SMA_20'].isna().all():
            current_price = hist_data['Close'].iloc[-1]
            sma_20 = hist_data['SMA_20'].iloc[-1]
            sma_50 = hist_data['SMA_50'].iloc[-1]
            
            print(f"\nTechnical Status:")
            print(f"Price vs 20-day SMA: {'Above' if current_price > sma_20 else 'Below'} (${sma_20:.2f})")
            print(f"Price vs 50-day SMA: {'Above' if current_price > sma_50 else 'Below'} (${sma_50:.2f})")
            
            if not hist_data['RSI'].isna().all():
                rsi = hist_data['RSI'].iloc[-1]
                print(f"Current RSI: {rsi:.2f} ({'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral'})")
        
        return filename
        
    except Exception as e:
        print(f"Error downloading Apple trading data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Starting Apple Comprehensive Trading Data Download...")
    result_file = download_apple_trading_data()
    
    if result_file:
        print(f"\nDownload completed successfully!")
        print(f"Check the file: {result_file}")
    else:
        print("\nDownload failed. Please check the error messages above.")
