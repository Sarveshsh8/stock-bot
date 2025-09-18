"""
S3 Storage Manager
Handles all S3 operations with versioning support
"""

import boto3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging
from botocore.exceptions import ClientError, NoCredentialsError

class S3Manager:
    """Manages S3 storage operations with versioning"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize S3 manager
        
        Args:
            config: Configuration dictionary containing S3 settings
        """
        self.config = config
        self.bucket_name = config['s3_settings']['bucket_name']
        self.region = config['s3_settings']['region']
        self.version_prefix = config['s3_settings']['version_prefix']
        self.available = False  # Initialize availability flag
        
        self._setup_logging()
        self._setup_s3_client()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_s3_client(self):
        """Setup S3 client"""
        try:
            self.s3_client = boto3.client('s3', region_name=self.region)
            self._verify_bucket_access()
            self.available = True
        except NoCredentialsError:
            self.logger.warning("AWS credentials not found - S3 operations will be disabled")
            self.s3_client = None
            self.available = False
        except Exception as e:
            self.logger.warning(f"Error setting up S3 client: {str(e)} - S3 operations will be disabled")
            self.s3_client = None
            self.available = False
    
    def is_available(self) -> bool:
        """Check if S3 is available"""
        return self.available and self.s3_client is not None
    
    def _verify_bucket_access(self):
        """Verify bucket access and create if needed"""
        if not self.available:
            return
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.logger.info(f"Bucket {self.bucket_name} exists and is accessible")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                self.logger.info(f"Bucket {self.bucket_name} does not exist, creating...")
                self._create_bucket()
            else:
                self.logger.error(f"Error accessing bucket: {str(e)}")
                raise
    
    def _create_bucket(self):
        """Create S3 bucket"""
        try:
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            self.logger.info(f"Created bucket: {self.bucket_name}")
        except Exception as e:
            self.logger.error(f"Error creating bucket: {str(e)}")
            raise
    
    def _get_version_path(self, data_type: str, filename: str) -> str:
        """Get versioned S3 path"""
        return f"{self.version_prefix}/{data_type}/{filename}"
    
    def upload_yahoo_finance_data(self, data: Dict[str, Any], data_type: str = "yahoo_finance") -> List[str]:
        """
        Upload Yahoo Finance data to S3
        
        Args:
            data: Dictionary containing financial data
            data_type: Type of data being uploaded
            
        Returns:
            List of uploaded file paths
        """
        uploaded_files = []
        
        for symbol, df in data.items():
            try:
                # Convert DataFrame to JSON
                json_data = df.to_json(orient='records', date_format='iso')
                
                # Create filename
                filename = f"{symbol}_data.json"
                s3_key = self._get_version_path(data_type, filename)
                
                # Upload to S3
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=json_data,
                    ContentType='application/json',
                    Metadata={
                        'symbol': symbol,
                        'data_type': 'yahoo_finance',
                        'upload_date': datetime.now().isoformat(),
                        'version': self.version_prefix
                    }
                )
                
                uploaded_files.append(s3_key)
                self.logger.info(f"Uploaded {symbol} data to s3://{self.bucket_name}/{s3_key}")
                
            except Exception as e:
                self.logger.error(f"Error uploading {symbol} data: {str(e)}")
        
        return uploaded_files
    
    def upload_file(self, file_path: str, data_type: str, metadata: Optional[Dict] = None) -> str:
        """
        Upload a file to S3
        
        Args:
            file_path: Local file path
            data_type: Type of data (documents, images, videos, etc.)
            metadata: Additional metadata
            
        Returns:
            S3 key of uploaded file
        """
        try:
            filename = os.path.basename(file_path)
            s3_key = self._get_version_path(data_type, filename)
            
            # Prepare metadata
            file_metadata = {
                'upload_date': datetime.now().isoformat(),
                'version': self.version_prefix,
                'original_filename': filename
            }
            
            if metadata:
                file_metadata.update(metadata)
            
            # Upload file
            with open(file_path, 'rb') as file:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file,
                    Metadata=file_metadata
                )
            
            self.logger.info(f"Uploaded {filename} to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except Exception as e:
            self.logger.error(f"Error uploading file {file_path}: {str(e)}")
            raise
    
    def upload_processed_file(self, processed_data: Dict[str, Any], filename: str, data_type: str) -> str:
        """
        Upload processed file data to S3
        
        Args:
            processed_data: Processed file data
            filename: Original filename
            data_type: Type of data
            
        Returns:
            S3 key of uploaded file
        """
        try:
            s3_key = self._get_version_path(data_type, f"processed_{filename}")
            
            # Convert to JSON
            json_data = json.dumps(processed_data, indent=2)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_data,
                ContentType='application/json',
                Metadata={
                    'original_filename': filename,
                    'data_type': data_type,
                    'upload_date': datetime.now().isoformat(),
                    'version': self.version_prefix
                }
            )
            
            self.logger.info(f"Uploaded processed {filename} to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except Exception as e:
            self.logger.error(f"Error uploading processed file {filename}: {str(e)}")
            raise
    
    def upload_faiss_index(self, index_data: bytes, documents_data: bytes) -> Tuple[str, str]:
        """
        Upload FAISS index and documents to S3
        
        Args:
            index_data: FAISS index as bytes
            documents_data: Documents data as bytes
            
        Returns:
            Tuple of (index_s3_key, documents_s3_key)
        """
        try:
            # Upload index
            index_key = self._get_version_path("faiss_index", "financial_index.faiss")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=index_key,
                Body=index_data,
                ContentType='application/octet-stream',
                Metadata={
                    'data_type': 'faiss_index',
                    'upload_date': datetime.now().isoformat(),
                    'version': self.version_prefix
                }
            )
            
            # Upload documents
            docs_key = self._get_version_path("faiss_index", "financial_documents.pkl")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=docs_key,
                Body=documents_data,
                ContentType='application/octet-stream',
                Metadata={
                    'data_type': 'faiss_documents',
                    'upload_date': datetime.now().isoformat(),
                    'version': self.version_prefix
                }
            )
            
            self.logger.info(f"Uploaded FAISS index to s3://{self.bucket_name}/{index_key}")
            self.logger.info(f"Uploaded documents to s3://{self.bucket_name}/{docs_key}")
            
            return index_key, docs_key
            
        except Exception as e:
            self.logger.error(f"Error uploading FAISS index: {str(e)}")
            raise
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download file from S3
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            self.logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error downloading file: {str(e)}")
            return False
    
    def list_files(self, data_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in S3 bucket
        
        Args:
            data_type: Filter by data type (optional)
            
        Returns:
            List of file information dictionaries
        """
        try:
            prefix = f"{self.version_prefix}/"
            if data_type:
                prefix += f"{data_type}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'data_type': self._extract_data_type(obj['Key'])
                })
            
            return files
            
        except Exception as e:
            self.logger.error(f"Error listing files: {str(e)}")
            return []
    
    def _extract_data_type(self, s3_key: str) -> str:
        """Extract data type from S3 key"""
        parts = s3_key.split('/')
        if len(parts) >= 3:
            return parts[2]  # Assuming structure: version/data_type/filename
        return 'unknown'
    
    def get_bucket_info(self) -> Dict[str, Any]:
        """Get bucket information"""
        try:
            response = self.s3_client.head_bucket(Bucket=self.bucket_name)
            return {
                'bucket_name': self.bucket_name,
                'region': self.region,
                'version_prefix': self.version_prefix,
                'status': 'accessible'
            }
        except Exception as e:
            return {
                'bucket_name': self.bucket_name,
                'region': self.region,
                'version_prefix': self.version_prefix,
                'status': f'error: {str(e)}'
            }
