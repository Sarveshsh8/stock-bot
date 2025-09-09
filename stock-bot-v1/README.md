# Stock Bot v1.0

A comprehensive AI-powered stock analysis application deployed on AWS EKS with multi-modal analysis capabilities.

## 🚀 Features

- **Multi-Modal Analysis**: Image, video, and audio processing using AWS Bedrock Nova Pro
- **Streamlit Web Interface**: Interactive web application for stock analysis
- **Flask API Backend**: RESTful API for programmatic access
- **Jupyter Lab Environment**: Interactive development and analysis environment
- **AWS EKS Deployment**: Scalable Kubernetes deployment on AWS
- **Persistent Storage**: Data persistence across sessions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Flask API     │    │   Jupyter Lab   │
│   Frontend      │    │   Backend       │    │   Environment   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   AWS EKS       │
                    │   Kubernetes    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   AWS Bedrock   │
                    │   Nova Pro      │
                    └─────────────────┘
```

## 📁 Project Structure

```
stock-bot-v1/
├── src/                          # Source code
│   ├── QA_Agent/                 # Question-Answering agent
│   ├── model/                    # AI model integrations
│   ├── aws_code/                 # AWS utilities
│   └── misc/                     # Miscellaneous utilities
├── k8s/                          # Kubernetes manifests
│   ├── jupyter-custom-deps.yaml  # Jupyter deployment
│   ├── simple-deployment.yaml    # Main app deployment
│   ├── secrets.yaml              # AWS credentials
│   └── ebs-storage-class.yaml    # Storage configuration
├── data/                         # Sample data files
│   ├── images/                   # Test images
│   ├── videos/                   # Test videos
│   ├── audio/                    # Test audio files
│   └── excel/                    # Stock data files
├── aws-infrastructure/           # Terraform infrastructure
├── stock_bot.ipynb              # Main Jupyter notebook
├── streamlit_app.py             # Streamlit application
├── app.py                       # Flask API
├── stock-bot-control-simple.sh  # Application control script
└── jupyter-control.sh           # Jupyter control script
```

## 🛠️ Quick Start

### Prerequisites

- AWS CLI configured
- kubectl installed
- Docker installed
- EKS cluster running

### Control Your Applications

Use the control script to manage all applications:

```bash
# Show all application URLs
./stock-bot-control-simple.sh urls

# Start all applications
./stock-bot-control-simple.sh start all

# Stop all applications
./stock-bot-control-simple.sh stop all

# Check status of all apps
./stock-bot-control-simple.sh status all

# Start just Jupyter
./stock-bot-control-simple.sh start jupyter

# Get specific app URL
./stock-bot-control-simple.sh url jupyter
```

### Jupyter Lab Control

```bash
# Start Jupyter
./jupyter-control.sh start

# Stop Jupyter
./jupyter-control.sh stop

# Get Jupyter URL
./jupyter-control.sh url
```

## 🔗 Application URLs

Once deployed, your applications will be available at:

- **Jupyter Lab**: `https://[loadbalancer-url]` (Token: `stock-bot-jupyter-2024`)
- **Streamlit App**: `https://[loadbalancer-url]`
- **Flask API**: `https://[loadbalancer-url]`

## 🧠 AI Capabilities

### Image Analysis
- Financial chart analysis
- Pattern recognition
- Trend identification

### Video Analysis
- Stock market video content analysis
- Earnings call video processing
- Market sentiment analysis

### Audio Analysis
- Audio file metadata analysis
- File format and quality assessment
- Intelligent property-based analysis

## 🚀 Deployment

### AWS EKS Deployment

1. **Setup Infrastructure**:
   ```bash
   cd aws-infrastructure/terraform
   terraform init
   terraform plan
   terraform apply
   ```

2. **Deploy Applications**:
   ```bash
   ./scripts/setup-eks.sh
   ```

3. **Control Applications**:
   ```bash
   ./stock-bot-control-simple.sh start all
   ```

## 📊 Data Sources

- **Stock Data**: Apple Inc. historical data
- **Sample Images**: Stock charts and financial visualizations
- **Sample Videos**: Earnings calls and market analysis videos
- **Sample Audio**: Test audio files for analysis

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name
```

### Kubernetes Secrets

Update `k8s/secrets.yaml` with your base64-encoded credentials:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: aws-secrets
type: Opaque
data:
  aws-access-key-id: <base64-encoded-access-key>
  aws-secret-access-key: <base64-encoded-secret-key>
  s3-bucket-name: <base64-encoded-bucket-name>
```

## 🧪 Testing

### Test Image Analysis
```python
# In Jupyter notebook
result = process_image_with_nova_arn_simple(
    "data/images/apple_stock.png",
    "arn:aws:bedrock:ap-southeast-2:295386645352:inference-profile/apac.amazon.nova-pro-v1:0",
    "Analyze this financial chart"
)
```

### Test Video Analysis
```python
# In Jupyter notebook
result = process_video_with_nova_arn_simple(
    "data/videos/apple_q4.mp4",
    "arn:aws:bedrock:ap-southeast-2:295386645352:inference-profile/apac.amazon.nova-pro-v1:0",
    "Analyze this earnings call video"
)
```

### Test Audio Analysis
```python
# In Jupyter notebook
result = process_audio_with_nova_pro_working(
    "data/audio/test_tone.wav",
    "arn:aws:bedrock:ap-southeast-2:295386645352:inference-profile/apac.amazon.nova-pro-v1:0"
)
```

## 📝 API Endpoints

### Flask API

- `GET /health` - Health check
- `POST /analyze` - Analyze stock data
- `GET /data` - Get available data

### Streamlit App

- Interactive web interface
- File upload capabilities
- Real-time analysis results

## 🔒 Security

- AWS IAM roles and policies
- Kubernetes secrets management
- Secure credential storage
- Network isolation

## 📈 Monitoring

- Kubernetes health checks
- Application logs
- Resource monitoring
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the logs: `./stock-bot-control-simple.sh logs [app]`
- Review the documentation
- Open an issue on GitHub

---

**Stock Bot v1.0** - AI-Powered Stock Analysis Platform