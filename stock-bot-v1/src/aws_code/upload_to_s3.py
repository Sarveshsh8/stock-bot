import boto3
import os
from botocore.exceptions import ClientError
import glob
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def upload_file_to_s3(file_path, bucket_name, s3_key=None):
    """
    Upload a single file to S3 bucket
    """
    try:
        s3_client = boto3.client('s3')
        
        if s3_key is None:
            # Use filename as S3 key if not specified
            s3_key = os.path.basename(file_path)
        
        print(f"Uploading {file_path} to S3 bucket: {bucket_name}")
        print(f"S3 key: {s3_key}")
        
        s3_client.upload_file(file_path, bucket_name, s3_key)
        
        # Generate S3 URL
        s3_url = f"s3://{bucket_name}/{s3_key}"
        print(f"File uploaded successfully to: {s3_url}")
        
        return s3_url
        
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error uploading to S3: {e}")
        return None

def upload_data_files_to_s3(bucket_name, folder_path=".", file_patterns=None):
    """
    Upload all data files from a folder to S3 bucket
    """
    try:
        # Normalize the folder path
        folder_path = os.path.abspath(folder_path)
        
        # Default file patterns if none specified - comprehensive coverage
        if file_patterns is None:
            file_patterns = [
                # Spreadsheets & Documents
                "*.xlsx", "*.xls", "*.csv", "*.tsv", "*.ods",
                # Images
                "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.tiff", "*.tif", "*.webp", "*.svg", "*.ico", "*.raw", "*.heic", "*.heif",
                # Videos
                "*.mp4", "*.avi", "*.mov", "*.wmv", "*.flv", "*.webm", "*.mkv", "*.m4v", "*.3gp", "*.ogv", "*.mpg", "*.mpeg",
                # Audio
                "*.mp3", "*.wav", "*.flac", "*.aac", "*.ogg", "*.wma", "*.m4a", "*.opus",
                # Data & Text
                "*.json", "*.xml", "*.txt", "*.log", "*.md", "*.yaml", "*.yml", "*.ini", "*.cfg", "*.conf",
                # Archives
                "*.zip", "*.rar", "*.7z", "*.tar", "*.gz", "*.bz2",
                # PDFs
                "*.pdf",
                # Other common formats
                "*.ppt", "*.pptx", "*.doc", "*.docx", "*.rtf"
            ]
        
        all_files = []
        
        # Find files matching each pattern
        for pattern in file_patterns:
            search_pattern = os.path.join(folder_path, pattern)
            files = glob.glob(search_pattern)
            all_files.extend(files)
        
        # Remove duplicates and sort
        all_files = sorted(list(set(all_files)))
        
        if not all_files:
            print(f"No data files found matching patterns: {file_patterns}")
            print(f"Searching in folder: {folder_path}")
            # Try to list what's actually in the folder
            try:
                folder_contents = os.listdir(folder_path)
                data_files_in_folder = [f for f in folder_contents if any(f.lower().endswith(ext.replace('*', '').lower()) for ext in file_patterns)]
                if data_files_in_folder:
                    print(f"Found these data files in folder: {data_files_in_folder}")
                    # Use the found files
                    all_files = [os.path.join(folder_path, f) for f in data_files_in_folder]
                else:
                    print(f"No data files found in folder: {folder_path}")
                    return []
            except Exception as e:
                print(f"Error listing folder contents: {e}")
                return []
        
        print(f"Found {len(all_files)} data files to upload:")
        for file in all_files:
            file_size = os.path.getsize(file)
            print(f"  - {os.path.basename(file)} ({file_size:,} bytes)")
        
        uploaded_files = []
        
        for file_path in all_files:
            # Create S3 key with timestamp to avoid overwriting
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Organize by file type in S3 with comprehensive categorization
            if file_ext in ['.xlsx', '.xls', '.csv', '.tsv', '.ods']:
                s3_key = f"apple_trading_data/spreadsheets/{timestamp}_{filename}"
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.ico', '.raw', '.heic', '.heif']:
                s3_key = f"apple_trading_data/images/{timestamp}_{filename}"
            elif file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.ogv', '.mpg', '.mpeg']:
                s3_key = f"apple_trading_data/videos/{timestamp}_{filename}"
            elif file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus']:
                s3_key = f"apple_trading_data/audio/{timestamp}_{filename}"
            elif file_ext in ['.json', '.xml', '.txt', '.log', '.md', '.yaml', '.yml', '.ini', '.cfg', '.conf']:
                s3_key = f"apple_trading_data/data/{timestamp}_{filename}"
            elif file_ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
                s3_key = f"apple_trading_data/archives/{timestamp}_{filename}"
            elif file_ext in ['.pdf']:
                s3_key = f"apple_trading_data/documents/{timestamp}_{filename}"
            elif file_ext in ['.ppt', '.pptx', '.doc', '.docx', '.rtf']:
                s3_key = f"apple_trading_data/documents/{timestamp}_{filename}"
            else:
                s3_key = f"apple_trading_data/other/{timestamp}_{filename}"
            
            result = upload_file_to_s3(file_path, bucket_name, s3_key)
            if result:
                uploaded_files.append(result)
        
        return uploaded_files
        
    except Exception as e:
        print(f"Error in batch upload: {e}")
        return []

def upload_excel_files_to_s3(bucket_name, folder_path=".", file_pattern="*.xlsx"):
    """
    Upload all Excel files from a folder to S3 bucket (legacy function)
    """
    return upload_data_files_to_s3(bucket_name, folder_path, ["*.xlsx"])

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

def download_file_from_s3(bucket_name, s3_key, local_path=None):
    """
    Download a file from S3 bucket
    """
    try:
        s3_client = boto3.client('s3')
        
        if local_path is None:
            local_path = os.path.basename(s3_key)
        
        print(f"Downloading s3://{bucket_name}/{s3_key} to {local_path}")
        
        s3_client.download_file(bucket_name, s3_key, local_path)
        
        print(f"File downloaded successfully to: {local_path}")
        return local_path
        
    except ClientError as e:
        print(f"Error downloading from S3: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error downloading from S3: {e}")
        return None

if __name__ == "__main__":
    # Configuration from environment variables
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    FOLDER_PATH = os.getenv('FOLDER_PATH', '.')  # Default to current directory
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')  # Default region
    
    print("="*60)
    print("S3 EXCEL FILE UPLOAD SCRIPT")
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
    print(f"Source Folder: {os.path.abspath(FOLDER_PATH)}")
    print()
    
    # List existing files in S3
    print("Existing files in S3 bucket:")
    list_s3_files(S3_BUCKET_NAME, "apple_trading_data/")
    print()
    
    # Upload Excel files
    print("Uploading data files to S3...")
    uploaded_files = upload_data_files_to_s3(S3_BUCKET_NAME, FOLDER_PATH)
    
    if uploaded_files:
        print(f"Successfully uploaded {len(uploaded_files)} files:")
        for file_url in uploaded_files:
            print(f"  - {file_url}")
    else:
        print("No files were uploaded successfully")
    
    print("\n" + "="*60)
    print("SCRIPT COMPLETED")
    print("="*60)
