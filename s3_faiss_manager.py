"""
S3 FAISS Index Manager
Handles uploading and downloading FAISS index to/from S3
"""

import boto3
import os
from pathlib import Path
import tarfile
import logging
from botocore.exceptions import ClientError


class S3FAISSManager:
    """
    Manages FAISS index storage in S3.
    
    How it works:
    1. Compress FAISS index folder to tar.gz
    2. Upload to S3 bucket
    3. Download from S3 when needed
    4. Extract and use locally
    """
    
    def __init__(self, bucket_name: str, index_key: str = "faiss_index.tar.gz"):
        """
        Initialize S3 FAISS Manager.
        
        Parameters:
        - bucket_name: Name of S3 bucket
        - index_key: Key/path for index file in S3
        """
        self.bucket_name = bucket_name
        self.index_key = index_key
        self.s3_client = boto3.client('s3')
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def compress_index(self, index_path: str, output_file: str = "faiss_index.tar.gz"):
        """
        Compress FAISS index folder to tar.gz.
        
        Parameters:
        - index_path: Path to FAISS index folder
        - output_file: Output tar.gz filename
        
        Returns:
        - Path to compressed file
        """
        self.logger.info(f"Compressing index from {index_path}")
        
        with tarfile.open(output_file, "w:gz") as tar:
            tar.add(index_path, arcname=os.path.basename(index_path))
        
        self.logger.info(f"Compressed to {output_file}")
        return output_file
    
    def upload_index(self, index_path: str):
        """
        Upload FAISS index to S3.
        
        Parameters:
        - index_path: Path to FAISS index folder
        
        Returns:
        - S3 URL of uploaded file
        """
        try:
            # Compress index
            compressed_file = self.compress_index(index_path)
            
            # Upload to S3
            self.logger.info(f"Uploading to s3://{self.bucket_name}/{self.index_key}")
            self.s3_client.upload_file(
                compressed_file,
                self.bucket_name,
                self.index_key
            )
            
            # Clean up compressed file
            if os.path.exists(compressed_file):
                os.remove(compressed_file)
            
            s3_url = f"s3://{self.bucket_name}/{self.index_key}"
            self.logger.info(f"Successfully uploaded to {s3_url}")
            return s3_url
            
        except ClientError as e:
            self.logger.error(f"Error uploading to S3: {e}")
            raise
    
    def download_index(self, extract_path: str = "."):
        """
        Download FAISS index from S3.
        
        Parameters:
        - extract_path: Where to extract the index
        
        Returns:
        - Path to extracted index folder
        """
        try:
            compressed_file = "faiss_index_download.tar.gz"
            
            # Download from S3
            self.logger.info(f"Downloading from s3://{self.bucket_name}/{self.index_key}")
            self.s3_client.download_file(
                self.bucket_name,
                self.index_key,
                compressed_file
            )
            
            # Extract
            self.logger.info(f"Extracting to {extract_path}")
            with tarfile.open(compressed_file, "r:gz") as tar:
                tar.extractall(extract_path)
            
            # Clean up downloaded file
            if os.path.exists(compressed_file):
                os.remove(compressed_file)
            
            self.logger.info("Successfully downloaded and extracted index")
            
            # Return path to extracted index
            extracted_folders = [f for f in os.listdir(extract_path) if f.startswith("faiss_index")]
            if extracted_folders:
                return os.path.join(extract_path, extracted_folders[0])
            return None
            
        except ClientError as e:
            self.logger.error(f"Error downloading from S3: {e}")
            raise
    
    def index_exists(self):
        """
        Check if index exists in S3.
        
        Returns:
        - True if exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=self.index_key)
            return True
        except ClientError:
            return False
    
    def get_index_info(self):
        """
        Get information about the index in S3.
        
        Returns:
        - Dictionary with size, last modified, etc.
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=self.index_key
            )
            
            return {
                'size_mb': response['ContentLength'] / (1024 * 1024),
                'last_modified': response['LastModified'],
                'etag': response['ETag']
            }
        except ClientError as e:
            self.logger.error(f"Error getting index info: {e}")
            return None


def main():
    """CLI tool for managing FAISS index in S3."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Upload:   python s3_faiss_manager.py upload <bucket_name> <index_path>")
        print("  Download: python s3_faiss_manager.py download <bucket_name> [extract_path]")
        print("  Check:    python s3_faiss_manager.py check <bucket_name>")
        sys.exit(1)
    
    action = sys.argv[1]
    bucket_name = sys.argv[2]
    
    manager = S3FAISSManager(bucket_name)
    
    if action == "upload":
        if len(sys.argv) < 4:
            print("Error: Please provide index path")
            sys.exit(1)
        index_path = sys.argv[3]
        s3_url = manager.upload_index(index_path)
        print(f"✓ Uploaded to: {s3_url}")
    
    elif action == "download":
        extract_path = sys.argv[3] if len(sys.argv) > 3 else "."
        index_path = manager.download_index(extract_path)
        print(f"✓ Downloaded to: {index_path}")
    
    elif action == "check":
        if manager.index_exists():
            info = manager.get_index_info()
            print(f"✓ Index exists in S3")
            print(f"  Size: {info['size_mb']:.2f} MB")
            print(f"  Last Modified: {info['last_modified']}")
        else:
            print("✗ Index does not exist in S3")
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()

