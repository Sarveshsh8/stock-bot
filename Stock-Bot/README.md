# Comprehensive Apple Trading Data Analysis System

A modular system that reads files from S3, analyzes them using AWS Bedrock Nova Pro, and generates comprehensive financial insights for Apple trading data.

## System Architecture

```
v2/
├── run_comprehensive_analysis.py  # Main execution script (outside)
├── requirements.txt               # Dependencies
├── README.md                     # This documentation
├── data/                         # Local data files
└── src/                          # Source code
    ├── aws_code/                 # S3 operations
    │   ├── upload_to_s3.py
    │   └── read_from_s3.py
    ├── analysis_orchestrator.py  # Main orchestrator
    ├── nova_pro_client.py        # Nova Pro client
    └── prompts.py                # Custom analysis prompts
```

## Features

- **Multimodal Analysis**: Excel, video, image, and data files
- **S3 Integration**: Direct reading from S3 buckets
- **Nova Pro AI**: Advanced AI analysis using AWS Bedrock
- **Custom Prompts**: Specialized financial analysis prompts
- **Financial Analyst Focus**: Stock market analysis, technical indicators, market sentiment
- **Comprehensive Output**: Combined insights from all data sources
- **Modular Design**: Clean separation of concerns

## Prerequisites

1. **AWS Account** with Bedrock access
2. **S3 Bucket** for storing files
3. **Python 3.8+** with required packages
4. **Environment Variables** configured

## Setup

### 1. Install Dependencies

```bash
cd v2
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `v2` directory:

```bash
# AWS Configuration
S3_BUCKET_NAME=your-s3-bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 3. AWS Permissions

Ensure your AWS credentials have:
- `s3:GetObject`, `s3:ListBucket` (for S3 reading)
- `bedrock:InvokeModel` (for Nova Pro)

## File Organization in S3

The system expects files organized in S3 with this structure:

```
apple_trading_data/
├── spreadsheets/           # Excel/CSV files
│   └── timestamp_filename.xlsx
├── videos/                 # Video files
│   └── timestamp_filename.mp4
├── images/                 # Chart/images
│   └── timestamp_filename.png
└── other/                  # Other file types
```

## Usage

### Quick Start

```bash
cd v2
python3 run_comprehensive_analysis.py
```

Choose option 1 for comprehensive financial analysis or option 2 for quick connectivity test.

### Programmatic Usage

```python
from src.model.analysis_orchestrator import AnalysisOrchestrator

# Initialize orchestrator
orchestrator = AnalysisOrchestrator(
    bucket_name="your-bucket",
    region="us-east-1"
)

# Run complete analysis
results = orchestrator.run_complete_analysis(
    prefix="apple_trading_data/",
    max_tokens=1500,
    save_output=True
)
```

### Individual Components

#### Nova Pro Client

```python
from src.model.nova_pro_client import NovaProClient

client = NovaProClient()

# Analyze specific content
result = client.analyze_apple_trading_data("path/to/file.xlsx", "data")
```

#### S3 Operations

```python
from src.aws_code.read_from_s3 import read_file_from_s3

# Read file from S3
content = read_file_from_s3("bucket-name", "s3-key")
```

## Analysis Focus

### **Financial Analyst Role**
- Focus on financial metrics and performance
- Investment recommendations
- Risk assessment
- Technical indicators and chart patterns
- Market sentiment analysis

## Output Structure

The system generates comprehensive financial output with:

```json
{
  "analysis_metadata": {
    "timestamp": "2025-01-02T10:30:00",
    "total_files_analyzed": 5,
    "categories_analyzed": ["trading_data", "video_content", "chart_analysis"],
    "analysis_type": "Financial Analyst"
  },
  "category_summaries": {
    "trading_data": {
      "summary": "Analyzed 2 trading data files",
      "key_findings": "Financial metrics and performance indicators"
    }
  },
  "overall_insights": {
    "total_files": 5,
    "success_rate": "100.0%",
    "analysis_coverage": "Comprehensive financial analysis across multiple formats"
  },
  "detailed_results": {
    "file1.xlsx": {
      "analysis": "Detailed analysis results...",
      "timestamp": "2025-01-02T10:30:00"
    }
  },
  "financial_recommendations": [
    "Review trading data analysis for investment decisions",
    "Consider video content insights for market sentiment"
  ]
}
```

## Customization

### Adding New Content Types

1. Add file extensions to `_detect_file_type()` method in orchestrator
2. Create appropriate analysis prompts in `prompts.py`
3. Update analysis methods if needed

### Custom Prompts

Modify `src/prompts.py` to add:
- New financial analysis prompts
- Content-specific analysis prompts
- Apple-specific prompts

## Workflow

1. **File Discovery**: Scan S3 bucket for analyzable files
2. **Categorization**: Organize files by type and content
3. **Analysis**: Process each file with Nova Pro using financial analysis prompts
4. **Synthesis**: Combine all analysis results
5. **Output Generation**: Create comprehensive financial report
6. **Storage**: Save results to JSON file

## Troubleshooting

### Common Issues

1. **S3 Access Denied**
   - Check AWS credentials and permissions
   - Verify bucket name and region

2. **Bedrock Access Denied**
   - Ensure Bedrock is enabled in your region
   - Check IAM permissions for `bedrock:InvokeModel`

3. **Import Errors**
   - Verify Python path includes `src` directory
   - Check all dependencies are installed

4. **File Type Not Supported**
   - Add new file extensions to detection methods
   - Create appropriate analysis prompts

### Debug Mode

Enable detailed logging by modifying the orchestrator:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Tips

1. **Batch Processing**: Use `batch_analyze()` for multiple files
2. **Token Limits**: Adjust `max_tokens` based on content complexity
3. **Caching**: Results are cached during analysis session

## Future Enhancements

- **Real-time Analysis**: Streaming analysis of live data
- **Advanced Visualization**: Charts and graphs for insights
- **API Integration**: REST API for external access
- **Machine Learning**: Custom ML models for specific analysis

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review AWS service status
3. Verify environment configuration
4. Check file permissions and formats

## License

This project is for educational and research purposes. Ensure compliance with AWS terms of service and data privacy regulations.
