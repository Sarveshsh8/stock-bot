#!/usr/bin/env python3
"""
Main Upload Script: Upload documents to S3 bucket
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.aws_code.upload_to_s3 import upload_file_to_s3, upload_data_files_to_s3

def main():
    """Main function to upload documents to S3"""
    
    print("=" * 60)
    print("DOCUMENT UPLOAD TO S3")
    print("=" * 60)
    
    # Get S3 bucket name from environment
    bucket_name = os.getenv('S3_BUCKET_NAME')
    if not bucket_name:
        print("S3_BUCKET_NAME not found in environment variables")
        print("Please add S3_BUCKET_NAME to your .env file")
        return
    
    print(f"Target S3 Bucket: {bucket_name}")
    
    # Upload Excel file
    excel_file = "data/excel/apple_data2.xlsx"
    if os.path.exists(excel_file):
        print(f"Uploading Excel file: {excel_file}")
        s3_key = f"excel/{os.path.basename(excel_file)}"
        upload_file_to_s3(excel_file, bucket_name, s3_key)
    else:
        print(f"Excel file not found: {excel_file}")
    
    # Upload video file
    video_file = "data/videos/apple_q2.mp4"
    if os.path.exists(video_file):
        print(f"Uploading video file: {video_file}")
        s3_key = f"video/{os.path.basename(video_file)}"
        upload_file_to_s3(video_file, bucket_name, s3_key)
    else:
        print(f"Video file not found: {video_file}")
    
    # Upload image files
    image_dir = "data/images"
    if os.path.exists(image_dir):
        for file in os.listdir(image_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(image_dir, file)
                print(f"Uploading image: {file}")
                s3_key = f"image/{file}"
                upload_file_to_s3(image_path, bucket_name, s3_key)
    
    print("\nUpload process completed!")

if __name__ == "__main__":
    main()
