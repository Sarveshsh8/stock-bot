# Financial Data Q&A System

This system provides Question & Answer capabilities for Apple trading data using both Excel files and AI analysis results.

## Features

- **Excel Data Integration**: Reads Apple trading data from Excel files
- **AI Analysis Integration**: Incorporates Nova Pro analysis results
- **Smart Search**: Intelligent search across multiple data sources
- **Interactive Q&A**: Command-line interface for asking questions
- **FAISS Indexing**: Advanced vector search capabilities (optional)

## Quick Start

### Option 1: Simple Q&A (Recommended for beginners)

```bash
python3 simple_qa.py
```

This provides immediate Q&A functionality without requiring additional dependencies.

### Option 2: Advanced FAISS-based Q&A

```bash
# First, install dependencies
pip install -r requirements.txt

# Test the setup
python3 test_faiss_setup.py

# Build and use FAISS index
python3 build_faiss_qa.py
```

## File Structure

```
v2/
├── simple_qa.py              # Simple Q&A system (no FAISS required)
├── build_faiss_qa.py         # Advanced FAISS-based Q&A system
├── test_faiss_setup.py       # Test script for dependencies
├── QA_README.md              # This file
├── data/                     # Excel trading data
│   └── Apple_Trading_Data_*.xlsx
└── financial_analysis_*.json # AI analysis results
```

## Example Questions

### Trading Data Questions
- "What is the current Apple stock price?"
- "Show me the trading volume"
- "What are the technical indicators?"
- "Give me a trading summary"

### Analysis Questions
- "What are the financial recommendations?"
- "Show me the video analysis results"
- "What are the key findings?"
- "What is the market sentiment?"

## How It Works

### Simple Q&A System
1. **Data Loading**: Reads Excel file and JSON analysis
2. **Query Processing**: Analyzes your question for keywords
3. **Data Search**: Searches both data sources for relevant information
4. **Answer Generation**: Combines results into a comprehensive answer

### FAISS-based System
1. **Index Building**: Creates vector embeddings of all data
2. **Semantic Search**: Uses AI to find semantically similar content
3. **Advanced Matching**: More sophisticated relevance scoring
4. **Scalable**: Can handle large amounts of data efficiently

## Data Sources

### Excel Data (Historical_Data sheet)
- **Price Data**: Open, High, Low, Close prices
- **Volume**: Trading volume information
- **Technical Indicators**: SMA, RSI, MACD, Bollinger Bands
- **Date Range**: Historical trading periods

### JSON Analysis
- **Video Analysis**: AI analysis of video content
- **Category Summaries**: Organized analysis by data type
- **Financial Recommendations**: Investment insights
- **Overall Insights**: Comprehensive analysis summary

## Usage Examples

### Basic Usage
```bash
# Start the Q&A system
python3 simple_qa.py

# Ask questions interactively
Your question: What is the current Apple stock price?
Your question: Show me technical indicators
Your question: What are the financial recommendations?
```

### Programmatic Usage
```python
from simple_qa import SimpleFinancialQA

# Initialize Q&A system
qa = SimpleFinancialQA("data/Apple_Trading_Data.xlsx", "analysis.json")

# Ask a question
answer = qa.answer_question("What is the current stock price?")
print(answer)
```

## Troubleshooting

### Common Issues

1. **File Not Found**
   - Ensure Excel file exists in `data/` directory
   - Check JSON analysis file exists in root directory
   - Verify file paths are correct

2. **Import Errors**
   - For simple Q&A: Only basic Python packages required
   - For FAISS: Install requirements with `pip install -r requirements.txt`

3. **Data Loading Issues**
   - Check Excel file format and sheet names
   - Verify JSON file is valid JSON format
   - Ensure sufficient disk space

### Performance Tips

- **Simple Q&A**: Fastest for basic questions
- **FAISS System**: Better for complex, semantic queries
- **Large Files**: Consider chunking for very large datasets

## Customization

### Adding New Data Sources
1. Modify the `load_data()` method in `SimpleFinancialQA`
2. Add new search methods for different data types
3. Update the `answer_question()` method to include new sources

### Custom Search Logic
1. Extend the search methods in the Q&A class
2. Add new keyword patterns for specific data types
3. Implement custom relevance scoring

## Advanced Features

### FAISS Indexing Benefits
- **Semantic Understanding**: Better understanding of question intent
- **Scalability**: Handles large datasets efficiently
- **Accuracy**: More relevant search results
- **Performance**: Faster search for complex queries

### Vector Search Capabilities
- **Similarity Scoring**: Ranked results by relevance
- **Context Awareness**: Understands relationships between concepts
- **Multi-modal**: Can handle text, numbers, and structured data

## Support

For issues or questions:
1. Check file paths and permissions
2. Verify data file formats
3. Test with simple questions first
4. Check console output for error messages

## Future Enhancements

- **Web Interface**: Browser-based Q&A system
- **API Integration**: REST API for external access
- **Real-time Data**: Live data integration
- **Advanced Analytics**: More sophisticated financial analysis
- **Multi-language**: Support for different languages

## Requirements

### Simple Q&A
- Python 3.6+
- pandas
- openpyxl

### FAISS System
- All simple Q&A requirements
- faiss-cpu
- sentence-transformers
- torch
- transformers

## Installation

```bash
# Basic installation
pip install pandas openpyxl

# Full installation (for FAISS)
pip install -r requirements.txt
```

## License

This project is for educational and research purposes. Ensure compliance with data privacy regulations and terms of service.
