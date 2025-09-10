# Stock Bot V3 - Unified Financial Analysis Platform

##  Overview
A comprehensive AI-powered financial analysis platform that combines:
- **Yahoo Finance data fetching** (configurable via config.yaml)
- **Multi-modal file uploads** (documents, images, videos, audio)
- **S3 storage with versioning**
- **FAISS vector indexing**
- **Intelligent Q&A system**
- **Kubernetes deployment ready**

##  Features
- **Configurable Data Sources**: Select ETFs/stocks via config.yaml
- **File Upload Support**: Documents, images, videos, audio for analysis
- **S3 Storage**: Organized storage with version management
- **Vector Search**: FAISS-based semantic search
- **Multi-Modal AI**: AWS Bedrock Nova Pro integration (separate modules for images/videos)
- **Web Interface**: Streamlit + Flask API
- **Kubernetes Ready**: Complete K8s deployment with persistent storage
- **Modular Architecture**: Class-based, professional code structure

##  Architecture
```
User Input → Data Pipeline → S3 Storage → FAISS Index → Q&A System
     ↓              ↓            ↓           ↓           ↓
Config.yaml → YF Data + Files → Versioned → Vector DB → AI Response
```

##  Project Structure
```
stock-bot-v3/
 src/                           # Source code (modular, class-based)
    data/                      # Data handling modules
       fetchers/              # Yahoo Finance fetcher
       processors/            # File processors
    storage/                   # Storage management
       s3/                    # S3 operations
    ai/                        # AI/ML modules
       faiss/                 # Vector database
       bedrock/               # AWS Bedrock integration
          image/             # Image analysis
          video/             # Video analysis
       prompts/               # Specialized prompts
    web/                       # Web interfaces
 k8s/                           # Kubernetes manifests
 unified_pipeline.py            # Main pipeline orchestrator
 web_app.py                     # Streamlit web interface
 Dockerfile                     # Container definition
 docker-compose.yml             # Local development
 deploy.sh                      # K8s deployment script
 control.sh                     # Application control script
 config.yaml                    # Configuration file
```

##  Quick Start

### Local Development
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS credentials**:
   ```bash
   cp env_example.txt .env
   # Edit .env with your AWS credentials
   ```

3. **Run the pipeline**:
   ```bash
   python unified_pipeline.py
   ```

4. **Start web interface**:
   ```bash
   streamlit run web_app.py
   ```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Kubernetes Deployment
1. **Update secrets**:
   ```bash
   # Edit k8s/secrets.yaml with your AWS credentials
   ```

2. **Deploy to Kubernetes**:
   ```bash
   ./deploy.sh
   ```

3. **Control the application**:
   ```bash
   ./control.sh start    # Start the app
   ./control.sh status   # Check status
   ./control.sh urls     # Get URLs
   ./control.sh logs     # View logs
   ```

##  Configuration

### config.yaml Structure
```yaml
# ETFs and Stocks to fetch
etfs:
  - symbol: "SPY"
    name: "SPDR S&P 500 ETF Trust"
    category: "US Large Cap"

stocks:
  - symbol: "AAPL"
    name: "Apple Inc."
    category: "Technology"

# System settings
data_settings:
  default_period_months: 6

s3_settings:
  bucket_name: "stock-bot-v3-data"
  version_prefix: "v1.0"

faiss_settings:
  model_name: "all-MiniLM-L6-v2"
  chunk_size: 1000

bedrock_settings:
  region: "us-east-1"
  nova_pro_arn: "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"
```

##  Usage Examples

### Command Line
```bash
# Run full pipeline
python unified_pipeline.py

# Process specific files
python unified_pipeline.py --files document.pdf image.png

# Query the system
python unified_pipeline.py --query "What was Apple's Q4 performance?"

# Check system status
python unified_pipeline.py --status
```

### Web Interface
- **Dashboard**: Overview of configured symbols and system status
- **Data Pipeline**: Run the complete data fetching and indexing pipeline
- **File Upload**: Upload and process documents, images, videos
- **Q&A System**: Ask questions about your financial data
- **System Status**: Monitor system health and configuration

### Programmatic Usage
```python
from unified_pipeline import UnifiedPipeline

# Initialize pipeline
pipeline = UnifiedPipeline('config.yaml')

# Run full pipeline
results = pipeline.run_full_pipeline(['document.pdf', 'chart.png'])

# Query system
answers = pipeline.query_system("What are the top performing stocks?")
```

##  AI Analysis Capabilities

### Image Analysis
- **Financial Charts**: Technical analysis, support/resistance levels
- **Earnings Charts**: Revenue trends, performance metrics
- **General Images**: Business context and market implications

### Video Analysis
- **Earnings Calls**: Management insights, strategic initiatives
- **Market Analysis**: Trading signals, market outlook
- **General Videos**: Financial content analysis

### Text Analysis
- **Financial Data**: Performance evaluation, risk assessment
- **Market Data**: Trend analysis, investment opportunities
- **Earnings Data**: Business insights, growth prospects

##  Kubernetes Features

### Deployment Components
- **Namespace**: Isolated environment
- **ConfigMap**: Application configuration
- **Secrets**: AWS credentials management
- **Deployment**: Application pods with health checks
- **Service**: LoadBalancer for external access
- **PVC**: Persistent storage for data

### Control Commands
```bash
./control.sh start     # Start application
./control.sh stop      # Stop application
./control.sh restart   # Restart application
./control.sh status    # Show status
./control.sh urls      # Get service URLs
./control.sh logs      # View logs
./control.sh cleanup   # Delete all resources
```

##  Data Flow Example

1. **User uploads** `apple_earnings.pdf` and `stock_chart.png`
2. **Config.yaml** specifies `AAPL`, `MSFT`, `SPY` to fetch
3. **Pipeline runs:**
   - Fetches 6 months of YF data for AAPL, MSFT, SPY
   - Processes PDF and image files with Bedrock
   - Stores everything in S3: `v1.0/yahoo_finance/`, `v1.0/documents/`, `v1.0/images/`
   - Creates FAISS index with all data
4. **User asks:** "What was Apple's recent performance?"
5. **System returns:** Relevant data from YF, PDF analysis, and chart insights

##  Security & Best Practices

- **AWS IAM**: Proper permissions for Bedrock and S3
- **Kubernetes Secrets**: Secure credential management
- **Network Isolation**: Namespace-based isolation
- **Health Checks**: Application monitoring
- **Resource Limits**: CPU and memory constraints

##  Benefits

1. **Self-contained**: No imports from V1 or V2
2. **Modular**: Easy to maintain and extend
3. **Class-based**: Professional, object-oriented design
4. **Versioned**: S3 storage with version management
5. **Unified**: Single system for all data types
6. **Scalable**: Kubernetes-ready for production
7. **User-friendly**: Web interface for non-technical users
8. **Production-ready**: Complete deployment automation

This Stock Bot V3 system provides a complete, professional-grade financial analysis platform that combines the best of both V1 and V2 while being completely self-contained, modular, and Kubernetes-ready! 
