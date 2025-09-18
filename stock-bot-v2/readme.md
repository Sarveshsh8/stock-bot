# Stock Bot  - ETF and Stock Data Fetcher

## Overview

This project provides a simple Yahoo Finance data fetcher for ETFs and individual stocks. It focuses on fetching raw data without any analysis, perfect for getting clean data for further processing. You can easily select which ETFs and stocks to fetch by editing the config file.

## Features

- **Simple Data Fetching**: Automated raw data fetching from Yahoo Finance
- **ETF and Stock Support**: Fetch both ETFs and individual stocks
- **Organized Storage**: Separate folders for ETF and stock data
- **Multiple Export Formats**: CSV files and Excel format with organized sheets
- **Clean Data Structure**: Raw OHLCV data with dividends and stock splits
- **Jupyter Notebook**: Interactive data exploration environment
- **No Analysis**: Pure data fetching without any calculations or analysis

## ETFs Analyzed

1. **SPY** - SPDR S&P 500 ETF Trust
2. **QQQ** - Invesco QQQ Trust
3. **IWM** - iShares Russell 2000 ETF
4. **VTI** - Vanguard Total Stock Market ETF
5. **VEA** - Vanguard FTSE Developed Markets ETF
6. **VWO** - Vanguard FTSE Emerging Markets ETF
7. **AGG** - iShares Core U.S. Aggregate Bond ETF
8. **GLD** - SPDR Gold Trust
9. **XLF** - Financial Select Sector SPDR Fund
10. **XLK** - Technology Select Sector SPDR Fund

## Installation

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
2. **Run Data Fetcher**:

   ```bash
   python etf_data_fetcher.py
   ```

## Usage

### Python Script

```python
from etf_data_fetcher import SimpleETFDataFetcher

# Initialize fetcher
fetcher = SimpleETFDataFetcher()

# Fetch 3 months of raw data
fetcher.fetch_data(period_months=3)

# Display data information
fetcher.display_data_info()

# Save to CSV files
fetcher.save_to_csv("etf_data")

# Save to Excel file
fetcher.save_to_excel("etf_raw_data.xlsx")
```

### Jupyter Notebook

Open `etf_data_notebook.ipynb` in Jupyter Lab/Notebook and run all cells to fetch and explore raw data.

## Output

The system generates organized data in separate folders:

### CSV Files

- **ETF Data**: Saved in `etf_data/etfs/` folder
- **Stock Data**: Saved in `etf_data/stocks/` folder
- **Individual Files**: Each symbol gets its own CSV file

### Excel File

- **Organized Sheets**: Separate sheets for ETFs (`ETF_SYMBOL`) and stocks (`Stock_SYMBOL`)
- **Combined File**: All data in one Excel file with clear organization

### Raw Data

- **Clean OHLCV Data**: Ready for analysis
- **Dividends & Splits**: Included for complete historical data

## Performance Metrics

- **Total Return**: Overall percentage return over the period
- **Volatility**: Annualized standard deviation of returns
- **Sharpe Ratio**: Risk-adjusted return measure
- **Max Drawdown**: Maximum peak-to-trough decline
- **Current Price**: Latest closing price
- **Price Change**: Absolute and percentage price change

## Requirements

- Python 3.8+
- yfinance
- pandas
- numpy
- matplotlib
- seaborn
- plotly
- jupyter
- openpyxl (for Excel export)

## File Structure

```
stock-bot-v2/
├── etf_data_fetcher.py              # Main data fetcher class
├── etf_data_notebook.ipynb          # Jupyter notebook
├── etf_raw_data.xlsx               # Sample Excel output
├── requirements.txt                 # Dependencies
└── readme.md                       # This file
```

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. **Configure ETFs**: Edit `config.yaml` to select which ETFs to fetch
3. Run the fetcher: `python etf_data_fetcher.py`
4. Open the notebook: `jupyter lab etf_data_notebook.ipynb`
5. Run all cells to fetch and explore raw data

## How to Select ETFs

Edit the `config.yaml` file to choose which ETFs to fetch:

```yaml
etfs:
  # Active ETFs (uncommented = will be fetched)
  - symbol: "SPY"
    name: "SPDR S&P 500 ETF Trust"
    category: "US Large Cap"
  
  - symbol: "QQQ"
    name: "Invesco QQQ Trust"
    category: "US Technology"
  
  # Inactive ETFs (commented out = will NOT be fetched)
  # - symbol: "IWM"
  #   name: "iShares Russell 2000 ETF"
  #   category: "US Small Cap"
```

**To add an ETF**: Uncomment it by removing the `#` symbols
**To remove an ETF**: Comment it out by adding `#` symbols

## License

This project is for educational and analysis purposes.
