#!/usr/bin/env python3
"""
Main QA Script: Read from S3, build FAISS index, and perform QA operations
"""

import os
import sys
import json
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.aws_code.read_from_s3 import read_file_from_s3
from src.model.analysis_orchestrator import AnalysisOrchestrator
from src.QA_Agent.index_builder import FAISSIndexBuilder
from src.QA_Agent.output_generator import FinalOutputGenerator

def create_faiss_data_from_s3(excel_data, video_analysis, image_analyses):
    """Create data structure for FAISS indexing from S3 data"""
    
    # Create Excel chunks
    excel_chunks = []
    if isinstance(excel_data, dict) and 'sheets' in excel_data:
        excel_chunks.append(f"""
        Excel Data Summary:
        - Total Sheets: {len(excel_data['sheets'])}
        - Sheets: {', '.join(excel_data['sheets'])}
        - Data Summary: {excel_data.get('data_summary', 'Excel file loaded successfully')}
        """)
    
    # Create video analysis chunks
    video_chunks = []
    if video_analysis:
        video_chunks.append(f"""
        Video Analysis:
        {video_analysis}
        """)
    
    # Create image analysis chunks
    image_chunks = []
    for i, analysis in enumerate(image_analyses):
        if analysis:
            image_chunks.append(f"""
            Image Analysis {i+1}:
            {analysis}
            """)
    
    # Combine all chunks
    all_chunks = excel_chunks + video_chunks + image_chunks
    
    # Create metadata
    metadata = []
    for i, chunk in enumerate(all_chunks):
        if i < len(excel_chunks):
            source = 'excel'
        elif i < len(excel_chunks) + len(video_chunks):
            source = 'video_analysis'
        else:
            source = 'image_analysis'
        
        metadata.append({
            'source': source,
            'chunk_index': i,
            'content_preview': chunk[:200] + '...' if len(chunk) > 200 else chunk
        })
    
    return all_chunks, metadata

def main():
    """Main function for S3 reading, FAISS indexing, and QA operations"""
    
    print("=" * 60)
    print("S3 READ, FAISS INDEX, AND QA OPERATIONS")
    print("=" * 60)
    
    # Get S3 bucket name from environment
    bucket_name = os.getenv('S3_BUCKET_NAME')
    if not bucket_name:
        print("S3_BUCKET_NAME not found in environment variables")
        print("Please add S3_BUCKET_NAME to your .env file")
        return
    
    print(f"Using S3 Bucket: {bucket_name}")
    
    # Step 1: Read from S3 and analyze
    print("\nStep 1: Reading from S3 and analyzing documents...")
    
    # Initialize orchestrator
    orchestrator = AnalysisOrchestrator(bucket_name)
    
    # Read Excel file from S3
    excel_key = "excel/Apple_Trading_Data_20250902_104928.xlsx"
    print(f"Reading Excel file: {excel_key}")
    excel_data = read_file_from_s3(bucket_name, excel_key)
    
    # Read and analyze video from S3
    video_key = "video/appleq1.mp4"
    print(f"Analyzing video: {video_key}")
    video_file_info = read_file_from_s3(bucket_name, video_key)
    
    # Use orchestrator to analyze video
    if video_file_info and 'local_path' in video_file_info:
        video_analysis = orchestrator._analyze_video_from_s3(
            {'s3_key': video_key, 'type': 'video', 'category': 'video_content'},
            "Analyze this video for financial insights and trading patterns",
            1500
        )
    else:
        video_analysis = None
        print("Video analysis not available")
    
    # Read and analyze images from S3
    image_analyses = []
    image_keys = ["image/test_red_square.png"]
    
    for image_key in image_keys:
        try:
            print(f"Analyzing image: {image_key}")
            image_file_info = read_file_from_s3(bucket_name, image_key)
            
            if image_file_info and 'local_path' in image_file_info:
                image_analysis = orchestrator._analyze_image_from_s3(
                    {'s3_key': image_key, 'type': 'image', 'category': 'chart_analysis'},
                    "Analyze this image for financial chart patterns and insights",
                    1000
                )
                image_analyses.append(image_analysis)
            else:
                print(f"Image analysis not available for {image_key}")
        except Exception as e:
            print(f"Error analyzing image {image_key}: {e}")
    
    # Combine all analyses
    combined_analysis = {
        "excel_data": {
            "sheets": list(excel_data.keys()) if isinstance(excel_data, dict) else ["data"],
            "data_summary": "Excel file loaded successfully"
        },
        "video_analysis": video_analysis,
        "image_analyses": image_analyses,
        "analysis_metadata": {
            "total_files_analyzed": 1 + len(image_analyses) + (1 if video_analysis else 0),
            "analysis_type": "comprehensive",
            "timestamp": "2025-09-02"
        }
    }
    
    # Save combined analysis
    with open("combined_analysis.json", "w") as f:
        json.dump(combined_analysis, f, indent=2)
    
    print("Step 1 completed: Documents read and analyzed from S3")
    
    # Step 2: Build FAISS index directly from S3 data
    print("\nStep 2: Building FAISS index from S3 data...")
    
    # Create FAISS data directly from S3 analysis
    faiss_chunks, faiss_metadata = create_faiss_data_from_s3(
        excel_data, video_analysis, image_analyses
    )
    
    if not faiss_chunks:
        print("No data available for FAISS indexing")
        return
    
    # Initialize FAISS index builder
    index_builder = FAISSIndexBuilder()
    
    # Load sentence transformer model
    if not index_builder.load_sentence_transformer():
        print("Failed to load sentence transformer model")
        return
    
    # Set the data directly (bypassing local file loading)
    index_builder.documents = faiss_chunks
    index_builder.document_metadata = faiss_metadata
    
    # Build the index
    if index_builder.build_index():
        index_builder.save_index("indices/financial_data.index", "indices/financial_documents.pkl")
        print("Step 2 completed: FAISS index built successfully from S3 data")
    else:
        print("Failed to build FAISS index")
        return
    
    # Step 3: Perform QA operations
    print("\nStep 3: Starting QA operations...")
    
    output_generator = FinalOutputGenerator()
    if not output_generator.load_index_and_model("indices/financial_data.index", "indices/financial_documents.pkl"):
        print("Failed to load index and model for QA")
        return
    
    print("QA system ready! Ask questions about the data...")
    print("Type 'quit' to exit")
    
    # Interactive QA session
    while True:
        try:
            question = input("\nYour question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if question:
                print(f"\nProcessing: '{question}'")
                print("-" * 50)
                
                answer = output_generator.process_query(question)
                print(f"\n{answer}")
                
            else:
                print("Please enter a question.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
