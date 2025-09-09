#!/usr/bin/env python3
"""
Financial Data Analysis API
REST API for S3 document analysis and QA operations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.aws_code.read_from_s3 import read_file_from_s3
from src.model.analysis_orchestrator import AnalysisOrchestrator
from src.QA_Agent.index_builder import FAISSIndexBuilder
from src.QA_Agent.output_generator import FinalOutputGenerator

app = Flask(__name__)
CORS(app)

# Global variables for the system
faiss_index = None
output_generator = None
bucket_name = None

def initialize_system():
    """Initialize the FAISS index and output generator"""
    global faiss_index, output_generator, bucket_name
    
    bucket_name = os.getenv('S3_BUCKET_NAME')
    if not bucket_name:
        print("S3_BUCKET_NAME not found in environment variables")
        return False
    
    # Check if index exists
    if os.path.exists("indices/financial_data.index") and os.path.exists("indices/financial_documents.pkl"):
        print("Loading existing FAISS index...")
        output_generator = FinalOutputGenerator()
        if output_generator.load_index_and_model("indices/financial_data.index", "indices/financial_documents.pkl"):
            print("System initialized successfully!")
            return True
    
    print("No existing index found. Please run analysis first.")
    return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Financial Data Analysis API is running",
        "bucket": bucket_name or "not configured"
    })

@app.route('/upload', methods=['POST'])
def upload_document():
    """Upload document to S3"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        file_path = data.get('file_path')
        file_type = data.get('file_type', 'general')
        
        if not file_path:
            return jsonify({"error": "file_path is required"}), 400
        
        if not os.path.exists(file_path):
            return jsonify({"error": f"File not found: {file_path}"}), 404
        
        # Import upload function
        from src.aws_code.upload_to_s3 import upload_file_to_s3
        
        # Upload to S3
        s3_key = f"{file_type}/{os.path.basename(file_path)}"
        s3_url = upload_file_to_s3(file_path, bucket_name, s3_key)
        
        if s3_url:
            return jsonify({
                "message": "File uploaded successfully",
                "s3_url": s3_url,
                "s3_key": s3_key
            })
        else:
            return jsonify({"error": "Failed to upload file"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze_documents():
    """Analyze documents from S3 and build FAISS index"""
    try:
        global faiss_index, output_generator
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get file keys from request
        excel_key = data.get('excel_key', 'excel/Apple_Trading_Data_20250902_104928.xlsx')
        video_key = data.get('video_key', 'video/appleq1.mp4')
        image_keys = data.get('image_keys', ['image/test_red_square.png'])
        
        print(f"Starting analysis for bucket: {bucket_name}")
        
        # Initialize orchestrator
        orchestrator = AnalysisOrchestrator(bucket_name)
        
        # Read Excel file from S3
        print(f"Reading Excel file: {excel_key}")
        excel_data = read_file_from_s3(bucket_name, excel_key)
        
        # Read and analyze video from S3
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
        
        # Create FAISS data directly from S3 analysis
        faiss_chunks, faiss_metadata = create_faiss_data_from_s3(
            excel_data, video_analysis, image_analyses
        )
        
        if not faiss_chunks:
            return jsonify({"error": "No data available for FAISS indexing"}), 500
        
        # Initialize FAISS index builder
        index_builder = FAISSIndexBuilder()
        
        # Load sentence transformer model
        if not index_builder.load_sentence_transformer():
            return jsonify({"error": "Failed to load sentence transformer model"}), 500
        
        # Set the data directly
        index_builder.documents = faiss_chunks
        index_builder.document_metadata = faiss_metadata
        
        # Build the index
        if index_builder.build_index():
            index_builder.save_index("indices/financial_data.index", "indices/financial_documents.pkl")
            print("FAISS index built successfully from S3 data")
            
            # Initialize output generator
            output_generator = FinalOutputGenerator()
            if output_generator.load_index_and_model("indices/financial_data.index", "indices/financial_documents.pkl"):
                return jsonify({
                    "message": "Analysis completed successfully",
                    "faiss_index_built": True,
                    "total_chunks": len(faiss_chunks),
                    "video_analysis": bool(video_analysis),
                    "image_analyses_count": len(image_analyses)
                })
            else:
                return jsonify({"error": "Failed to initialize QA system"}), 500
        else:
            return jsonify({"error": "Failed to build FAISS index"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/qa', methods=['POST'])
def ask_question():
    """Ask a question and get intelligent answer"""
    try:
        global output_generator
        
        if not output_generator:
            return jsonify({"error": "QA system not initialized. Please run analysis first."}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        question = data.get('question')
        if not question:
            return jsonify({"error": "question is required"}), 400
        
        print(f"Processing question: {question}")
        
        # Get answer from the system
        answer = output_generator.process_query(question)
        
        return jsonify({
            "question": question,
            "answer": answer,
            "timestamp": "2025-09-02"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get system status"""
    global faiss_index, output_generator
    
    return jsonify({
        "faiss_index_ready": faiss_index is not None,
        "qa_system_ready": output_generator is not None,
        "bucket_name": bucket_name,
        "index_files_exist": {
            "financial_data.index": os.path.exists("indices/financial_data.index"),
            "financial_documents.pkl": os.path.exists("indices/financial_documents.pkl")
        }
    })

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

if __name__ == '__main__':
    print("=" * 60)
    print("FINANCIAL DATA ANALYSIS API")
    print("=" * 60)
    
    # Initialize system
    if initialize_system():
        print("System ready for API requests!")
    else:
        print("System initialization failed. Some endpoints may not work.")
    
    print("\nStarting Flask API server...")
    print("API endpoints:")
    print("  GET  /health     - Health check")
    print("  POST /upload     - Upload document to S3")
    print("  POST /analyze    - Analyze documents and build index")
    print("  POST /qa         - Ask questions")
    print("  GET  /status     - System status")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)
