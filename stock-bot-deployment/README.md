# Stock Bot - Financial Analysis Application

A clean, modular financial analysis application that processes market data, documents, and videos using AI-powered analysis.

## Features

- **📁 File Upload**: Upload and analyze financial documents, charts, and videos
- **📈 Market Data**: Fetch real-time data from Yahoo Finance
- **🎬 YouTube Analysis**: Download and analyze YouTube financial videos
- **❓ Q&A System**: Ask questions about your financial data with AI-powered answers
- **🔍 Vector Search**: FAISS-based knowledge base for intelligent retrieval

## Quick Start

### 1. Setup Environment

```bash
# Clone or navigate to the project directory
cd stock-bot-deployment

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the environment template and configure your settings:

```bash
cp env_example.txt .env
```

Edit `.env` with your AWS credentials:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### 3. Run Tests

Test the application to ensure everything works:

```bash
python test_app.py
```

### 4. Start Application

```bash
streamlit run main.py
```

The application will be available at: http://localhost:8501

## Project Structure

```
stock-bot-deployment/
├── main.py                 # Main Streamlit application
├── test_app.py            # Test suite
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from env_example.txt)
├── src/                   # Source code
│   ├── ai/               # AI components
│   │   ├── faiss/        # Vector database
│   │   ├── bedrock/      # AWS Bedrock integration
│   │   ├── prompts/      # AI prompts
│   │   ├── qa_system.py  # Q&A system
│   │   └── unified_pipeline.py  # Main pipeline
│   ├── data/             # Data processing
│   └── storage/          # Storage management
├── indices/              # FAISS index storage
├── data/                 # Data files
└── logs/                 # Application logs
```

## Configuration

Edit `config.yaml` to customize:

- **Stocks/ETFs**: Add symbols to track
- **FAISS Settings**: Vector database configuration
- **Storage**: Local and S3 storage settings
- **Bedrock**: AWS AI model settings

## Usage

### Upload Files
1. Go to the "Upload Files" tab
2. Upload financial documents, charts, or videos
3. Click "Process Files" to analyze with AI

### Market Data
1. Go to the "Market Data" tab
2. Click "Fetch Market Data" to get real-time data
3. View price metrics and performance

### YouTube Analysis
1. Go to the "YouTube" tab
2. Paste a YouTube URL
3. Click "Download & Analyze" for detailed analysis

### Q&A System
1. Create a knowledge index first
2. Go to the "Q&A" tab
3. Ask questions about your data
4. Get AI-powered answers

## Testing

Run the test suite to verify everything works:

```bash
python test_app.py
```

This will test:
- Import functionality
- Configuration loading
- Pipeline initialization
- Basic functionality

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the correct directory and virtual environment is activated
2. **AWS Errors**: Verify your `.env` file has correct AWS credentials
3. **Config Errors**: Check that `config.yaml` exists and is properly formatted

### Dependencies

If you encounter missing dependencies:

```bash
pip install -r requirements.txt
```

## Development

### Adding New Features

1. Create new modules in the `src/` directory
2. Update the unified pipeline to include new functionality
3. Add tests to `test_app.py`
4. Update the main application interface

### Code Structure

- **Modular Design**: Each component is self-contained
- **Error Handling**: Graceful handling of missing optional components
- **Configuration**: All settings in `config.yaml`
- **Testing**: Comprehensive test suite included

## License

This project is for educational and development purposes.