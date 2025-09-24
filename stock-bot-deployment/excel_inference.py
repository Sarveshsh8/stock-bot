#!/usr/bin/env python3
"""
Standalone Excel/Spreadsheet Inference Module
Analyzes Excel files, CSV files, and spreadsheets using AWS Bedrock Nova Pro with financial analysis focus
"""

import boto3
import os
import json
import sys
import pandas as pd
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
from dotenv import load_dotenv

# Excel Analysis Prompt - Edit this to customize analysis
EXCEL_ANALYSIS_PROMPT = """Analyze this spreadsheet data from a financial perspective. Please provide:

1. **Data Overview:** What type of financial data is this? (stock prices, earnings, market data, etc.)
2. **Key Metrics:** What are the most important financial metrics and KPIs?
3. **Trends Analysis:** What trends do you observe in the data?
4. **Statistical Insights:** What statistical patterns or correlations exist?
5. **Financial Implications:** What does this data suggest about market conditions or company performance?
6. **Investment Insights:** What actionable insights can investors derive from this data?
7. **Risk Assessment:** What risks or opportunities are highlighted in the data?
8. **Data Quality:** Are there any data quality issues or missing values that need attention?

Please be specific and provide actionable financial analysis with concrete examples from the data."""

class ExcelInference:
    """Standalone Excel/spreadsheet analysis using AWS Bedrock Nova Pro"""
    
    def __init__(self, region: str = "us-east-1", model_id: str = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"):
        """
        Initialize the Excel inference module
        
        Args:
            region: AWS region
            model_id: Bedrock model ARN
        """
        self.region = region
        self.model_id = model_id
        self.max_tokens = 4000
        
        # Load environment variables
        load_dotenv()
        
        self._setup_logging()
        self._setup_bedrock_client()
        self._setup_supported_formats()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_bedrock_client(self):
        """Setup Bedrock client"""
        try:
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self.logger.info(f"Bedrock client initialized for region: {self.region}")
        except Exception as e:
            self.logger.error(f"Error setting up Bedrock client: {str(e)}")
            raise
    
    def _setup_supported_formats(self):
        """Setup supported file formats"""
        self.supported_formats = {
            'excel': ['.xlsx', '.xls'],
            'csv': ['.csv'],
            'all': ['.xlsx', '.xls', '.csv']
        }
    
    def _load_spreadsheet(self, file_path: str) -> pd.DataFrame:
        """
        Load spreadsheet data into pandas DataFrame
        
        Args:
            file_path: Path to the spreadsheet file
            
        Returns:
            pandas DataFrame
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.xlsx', '.xls']:
                # Load Excel file
                df = pd.read_excel(file_path)
            elif file_ext == '.csv':
                # Load CSV file
                df = pd.read_csv(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            self.logger.info(f"Loaded spreadsheet: {df.shape[0]} rows, {df.shape[1]} columns")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading spreadsheet {file_path}: {str(e)}")
            raise
    
    def _prepare_data_summary(self, df: pd.DataFrame, file_path: str) -> str:
        """
        Prepare a comprehensive data summary for analysis
        
        Args:
            df: pandas DataFrame
            file_path: Path to the original file
            
        Returns:
            Formatted data summary string
        """
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / 1024  # KB
            
            # Basic info
            summary = f"""
SPREADSHEET ANALYSIS DATA
========================
File: {file_name}
Size: {file_size:.2f} KB
Dimensions: {df.shape[0]} rows × {df.shape[1]} columns

COLUMN INFORMATION
==================
"""
            
            # Column details
            for i, col in enumerate(df.columns):
                dtype = str(df[col].dtype)
                non_null = df[col].count()
                null_count = df[col].isnull().sum()
                
                summary += f"{i+1}. {col} ({dtype}) - {non_null} non-null, {null_count} null\n"
                
                # Show sample values for first few columns
                if i < 5:
                    sample_values = df[col].dropna().head(3).tolist()
                    summary += f"   Sample values: {sample_values}\n"
            
            # Data preview
            summary += f"""
DATA PREVIEW (First 10 rows)
============================
{df.head(10).to_string()}

STATISTICAL SUMMARY
==================
{df.describe().to_string() if len(df.select_dtypes(include=['number']).columns) > 0 else 'No numeric columns for statistical summary'}

DATA TYPES BREAKDOWN
===================
{df.dtypes.value_counts().to_string()}
"""
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error preparing data summary: {str(e)}")
            return f"Error preparing data summary: {str(e)}"
    
    def analyze_excel(self, file_path: str, prompt: str = None, 
                     temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Analyze Excel/spreadsheet using Nova Pro
        
        Args:
            file_path: Path to the spreadsheet file
            prompt: Analysis prompt (optional, uses default financial analysis if not provided)
            temperature: Response creativity (0.0 to 1.0)
            top_p: Response diversity (0.0 to 1.0)
            
        Returns:
            Analysis result
        """
        try:
            print(f"Starting Excel analysis for: {os.path.basename(file_path)}")
            self.logger.info(f"Starting Excel analysis for: {file_path}")
            
            # Load spreadsheet data
            df = self._load_spreadsheet(file_path)
            
            # Prepare data summary
            data_summary = self._prepare_data_summary(df, file_path)
            
            # Use default financial analysis prompt if none provided
            if prompt is None:
                prompt = EXCEL_ANALYSIS_PROMPT
            
            # Prepare analysis prompt with data
            analysis_prompt = f"""{prompt}

{data_summary}

Please provide a comprehensive financial analysis based on the above spreadsheet data."""
            
            # Prepare request body
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": analysis_prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": self.max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }
            
            # Send request to Bedrock
            print("Sending request to AWS Bedrock Nova Pro...")
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            result = response_body['output']['message']['content'][0]['text']
            
            print("Excel analysis completed successfully!")
            print("=" * 60)
            print("EXCEL ANALYSIS RESULT:")
            print("=" * 60)
            print(result)
            print("=" * 60)
            
            self.logger.info("Excel analysis completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Error in Excel analysis: {str(e)}"
            print(f"Error: {error_msg}")
            self.logger.error(error_msg)
            return error_msg
    
    def get_excel_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic information about an Excel/spreadsheet file
        
        Args:
            file_path: Path to the spreadsheet file
            
        Returns:
            Dictionary containing file information
        """
        try:
            df = self._load_spreadsheet(file_path)
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_ext = Path(file_path).suffix.lower()
            
            return {
                'file_name': file_name,
                'file_size_kb': file_size / 1024,
                'format': file_ext,
                'rows': df.shape[0],
                'columns': df.shape[1],
                'column_names': df.columns.tolist(),
                'data_types': df.dtypes.to_dict(),
                'has_numeric_data': len(df.select_dtypes(include=['number']).columns) > 0,
                'missing_values': df.isnull().sum().to_dict(),
                'file_path': file_path
            }
        except Exception as e:
            return {'error': str(e)}
    
    def extract_key_metrics(self, file_path: str) -> Dict[str, Any]:
        """
        Extract key financial metrics from spreadsheet
        
        Args:
            file_path: Path to the spreadsheet file
            
        Returns:
            Dictionary containing extracted metrics
        """
        try:
            df = self._load_spreadsheet(file_path)
            
            metrics = {
                'basic_info': {
                    'rows': df.shape[0],
                    'columns': df.shape[1],
                    'file_name': os.path.basename(file_path)
                },
                'numeric_columns': [],
                'text_columns': [],
                'date_columns': [],
                'summary_stats': {}
            }
            
            # Categorize columns
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    metrics['numeric_columns'].append(col)
                    metrics['summary_stats'][col] = {
                        'mean': df[col].mean(),
                        'median': df[col].median(),
                        'std': df[col].std(),
                        'min': df[col].min(),
                        'max': df[col].max(),
                        'count': df[col].count()
                    }
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    metrics['date_columns'].append(col)
                else:
                    metrics['text_columns'].append(col)
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    
    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """
        Validate if file is a supported spreadsheet format
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in self.supported_formats['all']:
            return False, f"Unsupported file format: {file_ext}. Supported formats: {', '.join(self.supported_formats['all'])}"
        
        return True, ""

if __name__ == "__main__":
    analyzer = ExcelInference()
    path = "/Users/sarvesh/Desktop/hobbies/coding/20200102/O/O.csv"
    result = analyzer.analyze_excel(path)

    print(result)