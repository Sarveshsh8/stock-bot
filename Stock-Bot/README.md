# Financial Data Analysis System

A comprehensive financial data analysis system with S3 integration, FAISS indexing, and Nova Pro AI-powered QA capabilities.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Local Files   │    │   S3 Bucket     │    │   Nova Pro AI   │
│                 │    │                 │    │                 │
│ - Excel Data    │───▶│ - excel/        │───▶│ - Video Analysis│
│ - Video Files   │    │ - video/        │    │ - Image Analysis│
│ - Image Files   │    │ - image/        │    │ - Text Analysis │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   FAISS Index   │
                       │                 │
                       │ - Vector Search │
                       │ - Context Retrieval│
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   QA System     │
                       │                 │
                       │ - Question Input│
                       │ - Intelligent   │
                       │   Responses     │
                       └─────────────────┘
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd Stock-Bot

# Set up virtual environment (Recommended)
python3 -m venv venv
source venv/bin/activate
# OR use the provided script
source activate_venv.sh

# Install dependencies
pip install -r requirements_venv.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your AWS credentials and S3 bucket name
```

### 2. Virtual Environment Benefits

Using a virtual environment provides several advantages:
- **Isolated dependencies**: Prevents conflicts with system Python packages
- **Clean PATH**: Resolves streamlit command issues on macOS
- **Reproducible environment**: Same setup across different machines
- **Easy cleanup**: Simply delete the `venv` folder to start fresh

### 3. Environment Variables (.env)

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

## 📁 File Structure

```
Stock-Bot/
├── app.py                    # Flask REST API
├── streamlit_app.py          # Streamlit web interface
├── main_upload.py            # S3 upload script
├── main_qa.py               # Command-line QA script
├── requirements_api.txt      # API dependencies
├── requirements_streamlit.txt # Streamlit dependencies
├── src/
│   ├── QA_Agent/            # FAISS and QA components
│   ├── aws_code/            # S3 operations
│   └── model/               # Nova Pro integration
└── data/                    # Local data files
```

## 🔧 Usage Options

**Important**: Always activate the virtual environment first:
```bash
source venv/bin/activate
# OR
source activate_venv.sh
```

### Option 1: Command Line Interface

#### Upload Documents to S3

```bash
python3 main_upload.py
```

#### Run QA System

```bash
python3 main_qa.py
```

### Option 2: REST API

#### Start API Server

```bash
python3 app.py
```

#### API Endpoints

- `GET /health` - Health check
- `POST /upload` - Upload document to S3
- `POST /analyze` - Analyze documents and build index
- `POST /qa` - Ask questions
- `GET /status` - System status

#### Test API

```bash
python3 test_api.py
```

### Option 3: Streamlit Web Interface

#### Start Streamlit App

```bash
span
```

#### Features

- Web-based interface
- System initialization
- Document analysis
- Interactive QA
- Example questions

## 📊 API Examples

### Upload Document

```bash
curl -X POST http://localhost:5000/upload \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/Apple_Trading_Data_20250902_104928.xlsx",
    "file_type": "excel"
  }'
```

### Analyze Documents

```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "excel_key": "excel/Apple_Trading_Data_20250902_104928.xlsx",
    "video_key": "video/appleq1.mp4",
    "image_keys": ["image/test_red_square.png"]
  }'
```

### Ask Question

```bash
curl -X POST http://localhost:5000/qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the current Apple stock price?"
  }'
```

## 🔍 System Features

### 1. Document Processing

- **Excel Files**: Trading data, financial metrics
- **Video Files**: Financial presentations, market analysis
- **Image Files**: Charts, graphs, financial documents

### 2. AI Analysis

- **Nova Pro Integration**: Multimodal analysis
- **Context-Aware**: Intelligent prompt selection
- **Financial Focus**: Specialized for financial data

### 3. Search & Retrieval

- **FAISS Indexing**: Fast vector similarity search
- **Semantic Search**: Meaning-based retrieval
- **Context Retrieval**: Relevant information extraction

### 4. QA System

- **Intelligent Responses**: AI-generated answers
- **Source Citation**: References to original data
- **Interactive Interface**: Multiple input methods

## 🛠️ Development

### Adding New Data Sources

1. Update `src/aws_code/read_from_s3.py`
2. Add new file type handling
3. Update analysis orchestrator
4. Modify FAISS data creation

### Customizing Prompts

Edit `src/QA_Agent/prompts.py` to modify:

- System prompts
- Analysis instructions
- Output templates
- Error messages

### Extending Analysis

1. Add new analysis methods to `AnalysisOrchestrator`
2. Update FAISS indexing logic
3. Modify output generation

## 🚀 Deployment

### Docker (Recommended)

```bash
# Build image
docker build -t financial-qa-system .

# Run container
docker run -p 5000:5000 -p 8501:8501 financial-qa-system
```

### EKS Deployment

1. Create Kubernetes manifests
2. Deploy to EKS cluster
3. Configure load balancing
4. Set up monitoring

## 📈 Performance

### Optimization Tips

- Use GPU for FAISS indexing (if available)
- Implement caching for repeated queries
- Batch process multiple documents
- Optimize S3 transfer speeds

### Monitoring

- API response times
- FAISS index performance
- Nova Pro API usage
- S3 transfer metrics

## 🔒 Security

### Best Practices

- Use IAM roles for AWS access
- Implement API authentication
- Secure environment variables
- Monitor API usage

### Access Control

- S3 bucket policies
- API rate limiting
- User authentication
- Audit logging

## 🆘 Troubleshooting

### Common Issues

1. **S3 Connection Error**: Check AWS credentials
2. **FAISS Index Error**: Verify data format
3. **Nova Pro Error**: Check API limits and ARN
4. **Memory Issues**: Reduce batch sizes

### Debug Mode

```bash
# Enable debug logging
export DEBUG=1
python3 app.py
```

## 📚 Additional Resources

- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [AWS Nova Pro Guide](https://docs.aws.amazon.com/bedrock/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the troubleshooting section
- Review the documentation

---

**Built with ❤️ using Streamlit, FAISS, and AWS Nova Pro**
