import boto3
import pandas as pd
import io
from botocore.exceptions import ClientError
import os
from datetime import datetime
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

def list_s3_files(bucket_name, prefix=""):
    """
    List files in S3 bucket with optional prefix
    """
    try:
        s3_client = boto3.client('s3')
        
        print(f"Listing files in S3 bucket: {bucket_name}")
        if prefix:
            print(f"With prefix: {prefix}")
        
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        if 'Contents' in response:
            files = [obj['Key'] for obj in response['Contents']]
            print(f"Found {len(files)} files:")
            for file in files:
                print(f"  - {file}")
            return files
        else:
            print("No files found in bucket")
            return []
            
    except ClientError as e:
        print(f"Error listing S3 files: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error listing S3 files: {e}")
        return None

def read_file_from_s3(bucket_name, s3_key):
    """
    Read file from S3 bucket based on file type
    """
    try:
        s3_client = boto3.client('s3')
        
        # Get file extension to determine type
        file_ext = os.path.splitext(s3_key)[1].lower()
        
        print(f"Reading file from S3: s3://{bucket_name}/{s3_key}")
        print(f"File type: {file_ext}")
        
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        
        if file_ext in ['.xlsx', '.xls', '.csv']:
            # Read Excel/CSV files
            if file_ext == '.csv':
                df = pd.read_csv(io.BytesIO(response['Body'].read()))
                print(f"Successfully read CSV file from S3")
                return {'csv_data': df}
            else:
                # Read Excel files
                df = pd.read_excel(io.BytesIO(response['Body'].read()), sheet_name=None)
                print(f"Successfully read Excel file from S3 with {len(df)} sheets")
                return df
        elif file_ext in ['.json']:
            # Read JSON files
            content = response['Body'].read().decode('utf-8')
            data = json.loads(content)
            print(f"Successfully read JSON file from S3")
            return {'json_data': data}
        elif file_ext in ['.txt', '.log', '.md']:
            # Read text files
            content = response['Body'].read().decode('utf-8')
            print(f"Successfully read text file from S3")
            return {'text_data': content}
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.ico', '.raw', '.heic', '.heif']:
            # Handle image files - download for analysis
            print(f"Image file detected. Downloading for analysis...")
            local_path = download_file_from_s3(bucket_name, s3_key, f"data/images/{os.path.basename(s3_key)}")
            if local_path:
                # Get file size from local file
                file_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
                return {'image_file': True, 'local_path': local_path, 'file_size': file_size}
            else:
                return {'image_file': True, 'file_size': 0}
        elif file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.ogv', '.mpg', '.mpeg']:
            # Handle video files - download for analysis
            print(f"Video file detected. Downloading for analysis...")
            local_path = download_file_from_s3(bucket_name, s3_key, f"data/videos/{os.path.basename(s3_key)}")
            if local_path:
                # Get file size from local file
                file_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
                return {'video_file': True, 'local_path': local_path, 'file_size': file_size}
            else:
                return {'video_file': True, 'file_size': 0}
        elif file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus']:
            # Handle audio files
            print(f"Audio file detected. Use download option to save locally.")
            return {'audio_file': True, 'file_size': len(response['Body'].read())}
        elif file_ext in ['.pdf']:
            # Handle PDF files
            print(f"PDF file detected. Use download option to save locally.")
            return {'pdf_file': True, 'file_size': len(response['Body'].read())}
        else:
            # Handle other file types
            print(f"File type {file_ext} not supported for reading. Use download option to save locally.")
            return {'other_file': True, 'file_size': len(response['Body'].read())}
        
    except ClientError as e:
        print(f"Error reading from S3: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error reading from S3: {e}")
        return None

def read_excel_from_s3(bucket_name, s3_key, sheet_name=None):
    """
    Read Excel file from S3 bucket (legacy function for backward compatibility)
    """
    result = read_file_from_s3(bucket_name, s3_key)
    if result and isinstance(result, dict) and any(key.endswith('_data') for key in result.keys()):
        return result
    return None

def download_file_from_s3(bucket_name, s3_key, local_path=None):
    """
    Download a file from S3 bucket to local storage
    """
    try:
        s3_client = boto3.client('s3')
        
        if local_path is None:
            local_path = os.path.basename(s3_key)
        
        print(f"Downloading s3://{bucket_name}/{s3_key} to {local_path}")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        print(f"Created directory: {os.path.dirname(local_path)}")
        
        s3_client.download_file(bucket_name, s3_key, local_path)
        
        # Verify the file was downloaded
        if os.path.exists(local_path):
            file_size = os.path.getsize(local_path)
            print(f"File downloaded successfully to: {local_path}")
            print(f"Downloaded file size: {file_size} bytes")
            return local_path
        else:
            print(f"File download failed - file doesn't exist at: {local_path}")
            return None
        
    except ClientError as e:
        print(f"Error downloading from S3: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error downloading from S3: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_apple_data(df_dict):
    """
    Analyze the Apple trading data from Excel sheets
    """
    print("\n" + "="*60)
    print("APPLE TRADING DATA ANALYSIS")
    print("="*60)
    
    if 'Historical_Data' in df_dict:
        hist_data = df_dict['Historical_Data']
        print(f"Historical Data Analysis:")
        print(f"   - Data Period: {hist_data.index[0]} to {hist_data.index[-1]}")
        print(f"   - Total Trading Days: {len(hist_data)}")
        print(f"   - Current Price: ${hist_data['Close'].iloc[-1]:.2f}")
        print(f"   - Price Range: ${hist_data['Low'].min():.2f} - ${hist_data['High'].max():.2f}")
        print(f"   - Average Volume: {hist_data['Volume'].mean():,.0f}")
        
        # Recent performance
        if len(hist_data) >= 2:
            recent_return = ((hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[-2]) / hist_data['Close'].iloc[-2]) * 100
            print(f"   - Latest Daily Return: {recent_return:.2f}%")
    
    if 'Company_Info' in df_dict:
        company_info = df_dict['Company_Info']
        print(f"Company Information:")
        # Display key metrics
        key_metrics = ['Market Cap', 'Current Price', '52 Week High', '52 Week Low', 'P/E Ratio']
        for metric in key_metrics:
            row = company_info[company_info['Metric'].str.contains(metric, case=False, na=False)]
            if not row.empty:
                print(f"   - {metric}: {row.iloc[0]['Value']}")
    
    if 'Analyst_Recommendations' in df_dict:
        recs = df_dict['Analyst_Recommendations']
        print(f"Analyst Recommendations:")
        print(f"   - Total Recommendations: {len(recs)}")
        if 'To Grade' in recs.columns:
            grade_counts = recs['To Grade'].value_counts()
            for grade, count in grade_counts.items():
                print(f"   - {grade}: {count}")
    
    if 'Institutional_Holders' in df_dict:
        inst_holders = df_dict['Institutional_Holders']
        print(f"Institutional Holders:")
        print(f"   - Total Institutional Holders: {len(inst_holders)}")
        if 'Shares' in inst_holders.columns:
            top_holders = inst_holders.nlargest(5, 'Shares')
            for _, holder in top_holders.iterrows():
                print(f"   - {holder.get('Holder', 'N/A')}: {holder.get('Shares', 0):,.0f} shares")

def main():
    # Configuration from environment variables
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    PREFIX = os.getenv('S3_PREFIX', 'apple_trading_data/')  # Default prefix
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')  # Default region
    
    print("="*60)
    print("S3 FILE READER SCRIPT")
    print("="*60)
    
    # Check if required environment variables are set
    if not S3_BUCKET_NAME:
        print("S3_BUCKET_NAME not found in environment variables")
        print("Please add S3_BUCKET_NAME to your .env file")
        print("Example: S3_BUCKET_NAME=my-stock-data-bucket")
        exit(1)
    
    # Set AWS region if specified
    if AWS_REGION:
        os.environ['AWS_DEFAULT_REGION'] = AWS_REGION
        print(f"Using AWS Region: {AWS_REGION}")
    
    print(f"Target S3 Bucket: {S3_BUCKET_NAME}")
    print(f"Data Prefix: {PREFIX}")
    print()
    
    # List available files in S3
    print("Available files in S3:")
    s3_files = list_s3_files(S3_BUCKET_NAME, PREFIX)
    
    if not s3_files:
        print("No files found. Please upload some files first.")
        return
    
    # Let user choose a file
    print(f"Select a file to read (1-{len(s3_files)}):")
    for i, file in enumerate(s3_files, 1):
        file_ext = os.path.splitext(file)[1].lower()
        if file_ext in ['.xlsx', '.xls', '.csv']:
            file_type = "Spreadsheet"
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.ico', '.raw', '.heic', '.heif']:
            file_type = "Image"
        elif file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.ogv', '.mpg', '.mpeg']:
            file_type = "Video"
        elif file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus']:
            file_type = "Audio"
        elif file_ext in ['.pdf']:
            file_type = "PDF"
        elif file_ext in ['.json', '.xml', '.txt', '.log', '.md', '.yaml', '.yml', '.ini', '.cfg', '.conf']:
            file_type = "Data/Text"
        else:
            file_type = "Other"
        
        print(f"  {i}. {file} [{file_type}]")
    
    try:
        choice = int(input("\nEnter your choice: ")) - 1
        if 0 <= choice < len(s3_files):
            selected_file = s3_files[choice]
            file_ext = os.path.splitext(selected_file)[1].lower()
            print(f"Selected: {selected_file}")
            
            # Read the file from S3
            print("Reading file from S3...")
            file_data = read_file_from_s3(S3_BUCKET_NAME, selected_file)
            
            if file_data:
                if file_ext in ['.xlsx', '.xls', '.csv']:
                    # Handle spreadsheet data
                    if isinstance(file_data, dict) and 'csv_data' in file_data:
                        print(f"Successfully read CSV file with {len(file_data['csv_data'])} rows")
                        # Analyze the data if it's Apple trading data
                        if 'Apple' in selected_file or 'trading' in selected_file.lower():
                            analyze_apple_data({'Historical_Data': file_data['csv_data']})
                    else:
                        print(f"Successfully read Excel file with {len(file_data)} sheets:")
                        for sheet_name in file_data.keys():
                            print(f"  - {sheet_name}: {file_data[sheet_name].shape[0]} rows × {file_data[sheet_name].shape[1]} columns")
                        
                        # Analyze the data
                        analyze_apple_data(file_data)
                
                elif file_ext in ['.json']:
                    print(f"Successfully read JSON file")
                    print(f"JSON data structure: {type(file_data['json_data'])}")
                
                elif file_ext in ['.txt', '.log', '.md']:
                    print(f"Successfully read text file")
                    print(f"Text content preview: {file_data['text_data'][:200]}...")
                
                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.ico', '.raw', '.heic', '.heif']:
                    print(f"Image file: {file_data['file_size']:,} bytes")
                
                elif file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.ogv', '.mpg', '.mpeg']:
                    print(f"Video file: {file_data['file_size']:,} bytes")
                
                elif file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus']:
                    print(f"Audio file: {file_data['file_size']:,} bytes")
                
                elif file_ext in ['.pdf']:
                    print(f"PDF file: {file_data['file_size']:,} bytes")
                
                # Option to download
                download_choice = input("\nWould you like to download this file locally? (y/n): ").lower()
                if download_choice == 'y':
                    local_filename = f"downloaded_{os.path.basename(selected_file)}"
                    download_file_from_s3(S3_BUCKET_NAME, selected_file, local_filename)
            else:
                print("Failed to read file from S3")
        else:
            print("Invalid choice!")
    except ValueError:
        print("Please enter a valid number!")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    
    print("\n" + "="*60)
    print("SCRIPT COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main()
