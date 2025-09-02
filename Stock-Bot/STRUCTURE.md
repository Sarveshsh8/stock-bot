# Project Structure

```
v2/
├── run_comprehensive_analysis.py  # MAIN FILE - Run this!
├── requirements.txt               # Dependencies
├── README.md                     # Documentation
├── STRUCTURE.md                  # This file
├── data/                         # Local data files
└── src/                          # Source code
    ├── aws_code/                 # S3 operations
    │   ├── upload_to_s3.py      # Upload files to S3
    │   └── read_from_s3.py      # Read files from S3
    ├── analysis_orchestrator.py  # Main orchestrator
    ├── nova_pro_client.py        # Nova Pro AI client
    └── prompts.py                # Financial analysis prompts
```

## Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure .env file** with your AWS credentials
3. **Run analysis**: `python3 run_comprehensive_analysis.py`

## File Purposes

- **`run_comprehensive_analysis.py`** - Main execution script (keep outside)
- **`src/`** - All source code organized by functionality
- **`data/`** - Local files and analysis results
- **`requirements.txt`** - Python package dependencies

## Code Organization

- **`aws_code/`** - S3 upload/download operations
- **`analysis_orchestrator.py`** - Coordinates the entire workflow
- **`nova_pro_client.py`** - AWS Bedrock Nova Pro integration
- **`prompts.py`** - Custom financial analysis prompts

## Usage

The main file is outside for easy access, while all the complex code is properly organized in the `src` folder. This makes the project clean and maintainable.
