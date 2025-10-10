# Stock Bot - RAG Chatbot with AWS Bedrock Nova Pro

A powerful stock analysis chatbot powered by AWS Bedrock Nova Pro for text generation and open-source embeddings for vector search.

## Features

- **AWS Bedrock Nova Pro**: Advanced text generation and analysis
- **Open Source Embeddings**: FREE sentence-transformers (runs locally)
- **FAISS Vector Store**: Lightning-fast similarity search
- **LangGraph Workflow**: Structured RAG pipeline
- **Google Search Integration**: Real-time stock information
- **Streamlit UI**: Beautiful, interactive chat interface

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already configured with AWS credentials:

```env
# AWS Credentials (pre-configured)
AWS_ACCESS_KEY_ID=AKIAUJRTKQNULWFWRMNV
AWS_SECRET_ACCESS_KEY=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
AWS_DEFAULT_REGION=us-east-1

# Embedding Model (FREE - runs locally)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Optional: SERP API for Google Search
SERPAPI_KEY=your_serpapi_key_here
```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will:
1. Load your stock dataset from `stock_dataset/`
2. Create embeddings using open-source model (first run downloads ~100MB model)
3. Build FAISS index
4. Start the chat interface

## Architecture

```
User Query
    ↓
Sentence-Transformers (Local Embeddings - FREE)
    ↓
FAISS Vector Search (Find relevant stocks)
    ↓
Google Search (Real-time info - Optional)
    ↓
AWS Bedrock Nova Pro (Generate answer)
    ↓
Final Answer
```

## Project Structure

```
stock-botv1/
├── app.py                          # Main Streamlit application
├── config_aws.py                   # AWS configuration helper
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables
│
├── src/
│   ├── data_processor/
│   │   └── stock_data_loader.py    # Load and process CSV files
│   │
│   ├── vector_store/
│   │   └── faiss_store.py          # FAISS with open-source embeddings
│   │
│   ├── chatbot/
│   │   ├── rag_chatbot.py          # LangGraph RAG chatbot
│   │   └── nova_text_analyzer.py   # AWS Nova Pro integration
│   │
│   └── serp_integration/
│       └── google_search.py        # Google search via SERP API
│
└── stock_dataset/                  # Your CSV files
    └── YYYYMMDD/
        └── A-Z/
            └── TICKER.csv
```

## How It Works

### 1. Data Loading
- Reads CSV files from `stock_dataset/`
- Creates metadata for each stock (prices, volume, trades)
- Generates text summaries

### 2. Embedding Creation (FREE!)
- Uses open-source `sentence-transformers`
- Runs locally on your machine
- No API costs, no internet needed after model download
- Popular models:
  - `all-MiniLM-L6-v2` (fast, 384 dims) - Default
  - `all-mpnet-base-v2` (better, 768 dims)
  - `multi-qa-MiniLM-L6-cos-v1` (Q&A optimized)

### 3. Vector Search
- FAISS stores embeddings for fast similarity search
- Finds most relevant stocks for user queries
- Subsecond search through thousands of stocks

### 4. Text Generation
- AWS Bedrock Nova Pro analyzes context
- Generates natural language responses
- Provides insights and recommendations

## Configuration

### Embedding Models

Change in `.env`:

```env
# Fast and good quality (default)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Better quality, slower
EMBEDDING_MODEL=all-mpnet-base-v2

# Optimized for Q&A
EMBEDDING_MODEL=multi-qa-MiniLM-L6-cos-v1
```

### Number of Stocks to Index

```env
NUM_STOCKS_TO_INDEX=100  # Adjust as needed
```

### AWS Nova Pro Settings

```env
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
BEDROCK_MAX_TOKENS=2000
BEDROCK_TEMPERATURE=0.7  # 0.0 = focused, 1.0 = creative
BEDROCK_TOP_P=0.9
```

## Testing

### Test AWS Configuration

```bash
python3 config_aws.py
```

### Test Embeddings

```python
from src.vector_store.faiss_store import FAISSVectorStore

# Initialize
vs = FAISSVectorStore(model_name='all-MiniLM-L6-v2')

# Create test index
texts = ["Apple stock price is $150", "Microsoft stock trades at $300"]
metadata = [{"ticker": "AAPL"}, {"ticker": "MSFT"}]
vs.create_index(texts, metadata)

# Search
results = vs.search("What is Apple's price?", k=1)
print(results)
```

### Test Nova Pro

```python
from src.chatbot.nova_text_analyzer import NovaTextAnalyzer
from config_aws import setup_aws_credentials

setup_aws_credentials()
nova = NovaTextAnalyzer()

if nova.test_connection():
    response = nova.generate_response("What is a stock?")
    print(response)
```

## Cost Analysis

### Embeddings: **FREE**
- Open-source models run locally
- No API calls
- Zero cost

### Nova Pro Text Generation: **Paid**
- Input: ~$0.008 per 1K tokens
- Output: ~$0.024 per 1K tokens
- Typical query: < $0.01

### Estimated Monthly Cost
- 100 queries/day: ~$30-40/month
- Just for text generation
- 90%+ cost savings vs using paid embeddings!

## Example Queries

- "Tell me about AAPL trading on 20200102"
- "What was the closing price for Apple?"
- "Compare AAPL and MSFT"
- "Show me high volume trading days"
- "What are the price trends?"

## Advantages

### Open Source Embeddings
✅ **FREE** - No API costs
✅ **Private** - Data never leaves your machine
✅ **Fast** - Local inference
✅ **Offline** - Works without internet (after download)
✅ **Flexible** - Many models to choose from

### AWS Bedrock Nova Pro
✅ **High Quality** - Enterprise-grade AI
✅ **Reliable** - AWS infrastructure
✅ **Scalable** - Handle high loads
✅ **Secure** - AWS security standards

## Troubleshooting

### Error: "No module named 'sentence_transformers'"

```bash
pip install sentence-transformers torch
```

### Error: "AWS credentials not found"

Check `.env` file exists and has:
```env
AWS_ACCESS_KEY_ID=AKIAUJRTKQNULWFWRMNV
AWS_SECRET_ACCESS_KEY=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
```

### Error: "Model download fails"

First run downloads the embedding model (~100MB). Ensure:
- Internet connection available
- Sufficient disk space (~500MB)
- Not behind restrictive firewall

### Slow First Run

Normal! First run:
1. Downloads embedding model (~2-3 minutes)
2. Creates FAISS index (depends on # of stocks)
3. Subsequent runs are fast (uses cached model and saved index)

## Advanced Usage

### Custom Embedding Model

```python
from src.vector_store.faiss_store import FAISSVectorStore

# Use different model
vs = FAISSVectorStore(model_name='all-mpnet-base-v2')
```

### Batch Processing

```python
from src.data_processor.stock_data_loader import StockDataLoader

loader = StockDataLoader("stock_dataset")

# Process multiple dates
dates = loader.get_available_dates()
for date in dates[:10]:
    tickers = loader.get_all_tickers_for_date(date)
    # Process tickers...
```

### Custom Prompts

```python
from src.chatbot.nova_text_analyzer import NovaTextAnalyzer

nova = NovaTextAnalyzer()

# Custom analysis
custom_prompt = "Analyze this stock data focusing on volatility..."
response = nova.generate_response(custom_prompt, temperature=0.5)
```

## Performance

### Embedding Speed
- all-MiniLM-L6-v2: ~100 texts/second (CPU)
- all-mpnet-base-v2: ~50 texts/second (CPU)
- With GPU: 5-10x faster

### Search Speed
- FAISS search: < 10ms for 10K vectors
- Subsecond for 100K vectors

### Nova Pro Response
- Simple query: ~2 seconds
- Complex analysis: ~3-4 seconds

## Requirements

- Python 3.8+
- 4GB RAM minimum (8GB recommended)
- 1GB disk space (for models and index)
- AWS account with Bedrock access
- Internet (first run only, for model download)

## License

This project is provided as-is for educational and commercial use.

## Support

For issues:
1. Check this README
2. Run `python3 config_aws.py` to verify AWS setup
3. Check terminal output for error messages
4. Ensure `.env` file is configured

---

**Built with**: AWS Bedrock Nova Pro + Sentence-Transformers + FAISS + LangGraph + Streamlit

**Status**: Production Ready ✅

**Cost**: ~$30-40/month (text generation only, embeddings are FREE!)
