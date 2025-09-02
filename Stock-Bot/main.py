#!/usr/bin/env python3
"""
Financial Analysis Runner - Main execution script for Apple trading data analysis
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.model.analysis_orchestrator import AnalysisOrchestrator

def main():
    """Main function to run comprehensive financial analysis"""
    print("=" * 70)
    print("COMPREHENSIVE APPLE TRADING DATA FINANCIAL ANALYSIS")
    print("=" * 70)
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    bucket_name = os.getenv('S3_BUCKET_NAME')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not bucket_name:
        print("Error: S3_BUCKET_NAME not found in environment variables")
        print("Please create a .env file with your AWS configuration")
        return
    
    print("Configuration:")
    print(f"  S3 Bucket: {bucket_name}")
    print(f"  AWS Region: {region}")
    print(f"  Analysis Type: Financial Analyst")
    
    # Initialize financial analysis orchestrator
    print("\nInitializing financial analysis orchestrator...")
    orchestrator = AnalysisOrchestrator(bucket_name, region)
    
    print("Analysis type: Financial Analyst")
    print("Focus: Stock market analysis, technical indicators, and market sentiment")
    
    print("\n" + "=" * 70)
    print("STARTING FINANCIAL ANALYSIS WORKFLOW")
    print("=" * 70)
    
    # Run the complete analysis
    try:
        results = orchestrator.run_complete_analysis(
            prefix="apple_trading_data/",
            max_tokens=4096,
            save_output=True
        )
        
        if results:
            print("\n" + "=" * 70)
            print("FINANCIAL ANALYSIS WORKFLOW COMPLETED")
            print("=" * 70)
            
            # Display summary
            print("\n" + "=" * 50)
            print("FINANCIAL ANALYSIS SUMMARY")
            print("=" * 50)
            
            if 'analysis_metadata' in results:
                metadata = results['analysis_metadata']
                print(f"Total files analyzed: {metadata.get('total_files_analyzed', 0)}")
                print(f"Categories analyzed: {', '.join(metadata.get('categories_analyzed', []))}")
                print(f"Analysis type: {metadata.get('analysis_type', 'Unknown')}")
                print(f"Timestamp: {metadata.get('timestamp', 'Unknown')}")
            
            if 'category_summaries' in results:
                print("\nCategory Summaries:")
                for category, summary in results['category_summaries'].items():
                    print(f"  {category.upper()}: {summary['summary']}")
                    print(f"    Key findings: {summary['key_findings']}")
            
            if 'financial_recommendations' in results:
                print("\nFinancial Recommendations:")
                for i, rec in enumerate(results['financial_recommendations'], 1):
                    print(f"  {i}. {rec}")
            
            print(f"\nFinancial analysis completed successfully!")
            print(f"Results saved to: financial_analysis_*.json")
            
        else:
            print("Error: No analysis results returned")
            
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("FINANCIAL ANALYSIS WORKFLOW COMPLETED")
    print("=" * 70)

def run_quick_analysis():
    """Quick connectivity and basic functionality test"""
    print("=" * 50)
    print("QUICK ANALYSIS TEST")
    print("=" * 50)
    
    try:
        # Load environment variables
        load_dotenv()
        
        bucket_name = os.getenv('S3_BUCKET_NAME')
        region = os.getenv('AWS_REGION', 'us-east-1')
        
        if not bucket_name:
            print("Error: S3_BUCKET_NAME not found in environment variables")
            return
        
        print(f"Testing connectivity to:")
        print(f"  S3 Bucket: {bucket_name}")
        print(f"  AWS Region: {region}")
        
        # Test S3 connectivity
        print("\nTesting S3 connectivity...")
        from src.aws_code.read_from_s3 import list_s3_files
        
        files = list_s3_files(bucket_name, "apple_trading_data/")
        if files:
            print(f"Successfully connected to S3. Found {len(files)} files.")
            for file in files[:3]:  # Show first 3 files
                print(f"  - {file}")
            if len(files) > 3:
                print(f"  ... and {len(files) - 3} more files")
        else:
            print("S3 connection successful, but no files found in apple_trading_data/")
        
        # Test Nova Pro client initialization
        print("\nTesting Nova Pro client...")
        from src.model.nova_pro_client import NovaProClient
        
        client = NovaProClient(region_name=region, bucket_name=bucket_name)
        print("Nova Pro client initialized successfully")
        
        print("\nQuick analysis test completed successfully!")
        print("Your system is ready for comprehensive financial analysis.")
        
    except Exception as e:
        print(f"Error during quick analysis test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
            
    
