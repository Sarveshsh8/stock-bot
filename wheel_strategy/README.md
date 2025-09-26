# Wheel Strategy Analysis

A standalone AI-powered wheel options strategy analysis application using prompt engineering.

## Overview

This application analyzes CSV stock data to provide comprehensive wheel strategy recommendations using advanced prompt engineering with AWS Bedrock Nova Pro.

## Features

- **Single Ticker Analysis**: Detailed wheel strategy evaluation for individual stocks
- **Multi-Ticker Comparison**: Side-by-side analysis of multiple stocks  
- **Top Candidates Finder**: Automated screening for best opportunities
- **Custom Analysis**: Flexible analysis with different prompt types

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set AWS Credentials
Create a `.env` file in the wheel_strategy folder with your AWS credentials:
```env
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

Alternatively, you can still use environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Run the Application
```bash
streamlit run wheel_app.py
```

### 4. Test Functionality
```bash
python test_wheel.py
```

## Data Structure

Place your CSV data in the following structure:
```
wheel_strategy/
└── data/
    └── 20200102/  # Date folder (YYYYMMDD)
        ├── A/     # Letter folders
        │   ├── AAPL.csv
        │   ├── AMZN.csv
        │   └── ...
        ├── B/
        └── ...
```

### CSV Format
Each CSV file should contain intraday trading data with columns:
- `Date`: Trading date (YYYYMMDD)
- `Ticker`: Stock symbol
- `TimeBarStart`: Time of bar start (HH:MM)
- `FirstTradePrice`: Opening price for the bar
- `HighTradePrice`: Highest price in the bar
- `LowTradePrice`: Lowest price in the bar
- `LastTradePrice`: Closing price for the bar
- `VolumeWeightPrice`: Volume-weighted average price
- `Volume`: Total volume traded
- `TotalTrades`: Number of trades in the bar

## Analysis Types

1. **General Analysis**: Overall wheel strategy suitability and recommendations
2. **Entry Signals**: Optimal timing and entry points for wheel strategy
3. **Risk Management**: Position sizing and risk control strategies
4. **Performance Tracking**: Strategy optimization and performance analysis

## Architecture

```
wheel_strategy/
├── src/
│   ├── ai/
│   │   └── wheel_analyzer.py      # Main analyzer with AI integration
│   ├── data_processors/
│   │   └── csv_processor.py       # Data processing and technical analysis
│   └── prompts/
│       └── wheel_prompts.py       # AI prompts for wheel strategy
├── data/                          # CSV data files
├── wheel_app.py                   # Streamlit application
├── test_wheel.py                  # Test script
├── requirements.txt               # Dependencies
└── README.md                      # This file
```

## Key Components

### AI Analyzer (`wheel_analyzer.py`)
- Integrates data processing with AI analysis
- Handles AWS Bedrock API calls
- Manages multiple analysis types
- Provides comparison and ranking capabilities

### Data Processor (`csv_processor.py`)
- Loads and validates CSV data
- Calculates technical indicators
- Performs suitability analysis
- Generates formatted text for AI prompts

### Prompt Engineering (`wheel_prompts.py`)
- Specialized prompts for wheel strategy analysis
- Expert-level system prompts
- Structured analysis templates
- Multiple analysis types (entry, risk, performance)

### Streamlit App (`wheel_app.py`)
- User-friendly web interface
- Interactive analysis options
- Real-time data visualization
- Formatted results display

## Usage Examples

### Python API
```python
from src.ai.wheel_analyzer import WheelStrategyAnalyzer

# Initialize analyzer
analyzer = WheelStrategyAnalyzer()

# Analyze single ticker
result = analyzer.analyze_ticker("AAPL", analysis_type="analysis")

# Compare multiple tickers
comparison = analyzer.compare_tickers(["AAPL", "MSFT", "TSLA"])

# Find top candidates
candidates = analyzer.get_top_wheel_candidates(limit=10, min_volume=10000)
```

### Web Interface
1. Open browser to `http://localhost:8501`
2. Select analysis type from dropdown
3. Enter ticker symbols or configure filters
4. Review AI-powered recommendations

## Suitability Scoring

Stocks are evaluated based on:

- **Liquidity (40% weight)**: Volume and trading activity
- **Volatility (30% weight)**: Price movement patterns (Medium volatility optimal)
- **Price Stability (30% weight)**: Consistency of price movements

Final scores: Excellent (80+), Good (60-79), Fair (40-59), Poor (<40)

## Prompt Engineering Features

- **Expert Persona**: AI acts as experienced options trader
- **Structured Output**: Consistent analysis format
- **Actionable Recommendations**: Specific strike prices and timeframes
- **Risk-Aware Analysis**: Comprehensive risk assessment
- **Data-Driven Insights**: Based on actual market data

## Troubleshooting

### Common Issues
1. **"No data available"**: Check data folder structure and CSV format
2. **"Ticker not found"**: Verify ticker symbol exists in data
3. **"AI analysis error"**: Check AWS credentials and Bedrock access
4. **Import errors**: Ensure all dependencies are installed

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Requirements

- Python 3.8+
- AWS Account with Bedrock access
- Nova Pro model permissions
- Streamlit for web interface
- Pandas for data processing

## License

This project is part of the Stock Bot application suite.
