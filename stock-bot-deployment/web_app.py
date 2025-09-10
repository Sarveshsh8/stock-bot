"""
Stock Bot V3 - Simple Unified App
Single interface for file uploads, Yahoo Finance data, indexing, and Q&A
"""

import streamlit as st
import os
import tempfile
import yaml
import boto3
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.faiss.faiss_manager import FAISSManager
from ai.bedrock.video.video_analyzer import VideoAnalyzer
from ai.bedrock.image.image_analyzer import ImageAnalyzer
from ai.prompts.qa_prompts import get_prompt
from ai.prompts.financial_prompts import get_video_prompt, get_image_prompt
import boto3

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Stock Bot V3 - Simple App",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'index_created' not in st.session_state:
    st.session_state.index_created = False
if 'faiss_manager' not in st.session_state:
    st.session_state.faiss_manager = None
if 's3_client' not in st.session_state:
    st.session_state.s3_client = None

def setup_faiss_manager():
    """Setup FAISS manager"""
    try:
        if st.session_state.faiss_manager is None:
            # Load config for FAISS settings
            config = load_config()
            if not config:
                st.error("Failed to load config for FAISS settings")
                return False
            
            st.session_state.faiss_manager = FAISSManager(config)
        return True
    except Exception as e:
        st.error(f"FAISS setup failed: {str(e)}")
        return False

def setup_analyzers():
    """Setup Nova Pro analyzers"""
    try:
        config = load_config()
        if not config:
            st.error("Failed to load config for analyzers")
            return False, None, None
        
        video_analyzer = VideoAnalyzer(config)
        image_analyzer = ImageAnalyzer(config)
        return True, video_analyzer, image_analyzer
    except Exception as e:
        st.error(f"Analyzer setup failed: {str(e)}")
        return False, None, None

def get_simple_answer(query, search_results):
    """Get simple answer using Bedrock for Q&A"""
    try:
        # Check for common greetings
        greeting_words = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        if any(word in query.lower() for word in greeting_words):
            return get_prompt("greeting_response", "qa")
        
        # If no search results, return a simple response
        if not search_results:
            return get_prompt("no_context_response", "qa")
        
        # Prepare context from search results
        context = ""
        for i, result in enumerate(search_results[:3]):  # Use top 3 results
            context += f"Source {i+1}: {result['content'][:500]}...\n\n"
        
        # Get prompt from qa_prompts.py
        prompt = get_prompt("simple_qa", "qa").format(context=context, query=query)

        # Use Bedrock for simple Q&A
        config = load_config()
        if not config:
            return "Error: Could not load configuration for Q&A"
        
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=config['bedrock_settings']['region']
        )
        
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 200,  # Keep answers short
                "temperature": 0.3,  # More focused responses
                "topP": 0.9
            }
        }
        
        response = bedrock_runtime.converse(
            modelId=config['bedrock_settings']['nova_pro_arn'],
            messages=body["messages"],
            inferenceConfig=body["inferenceConfig"]
        )
        
        return response['output']['message']['content'][0]['text']
        
    except Exception as e:
        return f"Error generating answer: {str(e)}"

def process_uploaded_files(uploaded_files):
    """Process uploaded files with Nova Pro analyzers"""
    try:
        success, video_analyzer, image_analyzer = setup_analyzers()
        if not success:
            return []
        
        processed_files = []
        
        for uploaded_file in uploaded_files:
            # Save file temporarily with proper extension
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, mode='wb') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                if file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']:
                    # Process video with Nova Pro
                    video_prompt = get_video_prompt("general_financial")
                    analysis = video_analyzer.analyze_video(tmp_path, video_prompt)
                    
                    processed_files.append({
                        'content': analysis,
                        'metadata': {
                            'file_name': uploaded_file.name,
                            'file_type': 'video',
                            'file_size': uploaded_file.size,
                            'source': 'nova_pro_analysis'
                        }
                    })
                    
                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
                    # Process image with Nova Pro
                    image_prompt = get_image_prompt("general_financial")
                    analysis = image_analyzer.analyze_image(tmp_path, image_prompt)
                    
                    processed_files.append({
                        'content': analysis,
                        'metadata': {
                            'file_name': uploaded_file.name,
                            'file_type': 'image',
                            'file_size': uploaded_file.size,
                            'source': 'nova_pro_analysis'
                        }
                    })
                        
                else:
                    # For other files, just store basic info
                    processed_files.append({
                        'content': f"File: {uploaded_file.name}\nSize: {uploaded_file.size} bytes\nType: {file_ext}",
                        'metadata': {
                            'file_name': uploaded_file.name,
                            'file_type': 'document',
                            'file_size': uploaded_file.size,
                            'source': 'file_upload'
                        }
                    })
                    
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
        
        return processed_files
        
    except Exception as e:
        st.error(f"Error processing files: {str(e)}")
        return []

def setup_s3():
    """Setup S3 client"""
    try:
        if st.session_state.s3_client is None:
            # Use environment variables for AWS credentials
            st.session_state.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )
        return True
    except Exception as e:
        st.error(f"S3 setup failed: {str(e)}")
        return False

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        st.error(f"Failed to load config: {str(e)}")
        return None

def fetch_yahoo_data(symbols, period_months=3):
    """Fetch data from Yahoo Finance"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_months * 30)
        
        data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date)
                if not df.empty:
                    data[symbol] = df
                    st.success(f"✅ Fetched {len(df)} days of data for {symbol}")
                else:
                    st.warning(f"⚠️ No data found for {symbol}")
            except Exception as e:
                st.error(f"❌ Error fetching {symbol}: {str(e)}")
        
        return data
    except Exception as e:
        st.error(f"Yahoo Finance error: {str(e)}")
        return {}

def create_unified_index(yahoo_data, uploaded_files):
    """Create unified index from both Yahoo data and uploaded files"""
    index_data = []
    
    # Add Yahoo Finance data
    if yahoo_data:
        for symbol, df in yahoo_data.items():
            latest_price = df['Close'].iloc[-1] if not df.empty else 0
            price_change = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100) if len(df) > 1 else 0
            
            summary = f"""
            Symbol: {symbol}
            Latest Price: ${latest_price:.2f}
            Price Change: {price_change:.2f}%
            Data Points: {len(df)}
            Date Range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}
            """
            
            index_data.append({
                'content': summary,
                'metadata': {
                    'type': 'yahoo_finance',
                    'symbol': symbol,
                    'source': 'Yahoo Finance API'
                }
            })
    
    # Add uploaded files
    if uploaded_files:
        for file in uploaded_files:
            summary = f"""
            File: {file.name}
            Size: {file.size} bytes
            Type: {os.path.splitext(file.name)[1]}
            Upload Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            index_data.append({
                'content': summary,
                'metadata': {
                    'type': 'uploaded_file',
                    'filename': file.name,
                    'source': 'User Upload'
                }
            })
    
    return index_data

def upload_faiss_to_s3(bucket_name="stock-bot-v3-index"):
    """Upload FAISS index to S3"""
    try:
        if not setup_s3() or not st.session_state.faiss_manager:
            return False
        
        # Try to create bucket if it doesn't exist
        try:
            st.session_state.s3_client.head_bucket(Bucket=bucket_name)
        except:
            # Bucket doesn't exist, create it
            try:
                st.session_state.s3_client.create_bucket(Bucket=bucket_name)
                st.write(f"Created S3 bucket: {bucket_name}")
            except Exception as e:
                st.error(f"Failed to create bucket: {str(e)}")
                return False
            
        # Create timestamped folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save FAISS index to temporary files
        temp_index_path = f"/tmp/faiss_index_{timestamp}.index"
        temp_docs_path = f"/tmp/faiss_docs_{timestamp}.pkl"
        
        # Save the index
        if not st.session_state.faiss_manager.save_index(temp_index_path, temp_docs_path):
            st.error("Failed to save FAISS index locally")
            return False
        
        # Upload FAISS index file
        s3_index_key = f"indexes/{timestamp}/faiss_index.index"
        with open(temp_index_path, 'rb') as f:
            st.session_state.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_index_key,
                Body=f,
                ContentType='application/octet-stream'
            )
        
        # Upload documents file
        s3_docs_key = f"indexes/{timestamp}/faiss_docs.pkl"
        with open(temp_docs_path, 'rb') as f:
            st.session_state.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_docs_key,
                Body=f,
                ContentType='application/octet-stream'
            )
                    
                    # Clean up temp files
        os.unlink(temp_index_path)
        os.unlink(temp_docs_path)
                        
        st.success(f"✅ FAISS index uploaded to S3: s3://{bucket_name}/indexes/{timestamp}/")
        return True
        
    except Exception as e:
        st.error(f"❌ S3 upload failed: {str(e)}")
        return False

def search_index(query, index_data, k=5):
    """Simple search in the index"""
    try:
        query_lower = query.lower()
        results = []
        
        for item in index_data:
            content_lower = item['content'].lower()
            if query_lower in content_lower:
                score = content_lower.count(query_lower) / len(content_lower.split())
                results.append({
                    'content': item['content'],
                    'metadata': item['metadata'],
                    'score': score
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:k]
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []

def main():
    """Minimal interface"""
    st.title("Stock Bot V3")
    
    # Simple layout - everything in one column
    st.write("Upload files, fetch data, create index, search")
    
    # File upload
    uploaded_files = st.file_uploader("Upload files:", accept_multiple_files=True)
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        st.write(f"Uploaded: {len(uploaded_files)} files")
    
    # Yahoo Finance
    config = load_config()
    if config:
        etf_symbols = [etf['symbol'] for etf in config.get('etfs', [])]
        stock_symbols = [stock['symbol'] for stock in config.get('stocks', [])]
        all_symbols = etf_symbols + stock_symbols
        
        if all_symbols:
            st.write(f"Symbols: {', '.join(all_symbols)}")
            if st.button("Fetch Yahoo Data"):
                with st.spinner("Fetching..."):
                    yahoo_data = fetch_yahoo_data(all_symbols, 3)
                    if yahoo_data:
                        st.session_state.yahoo_data = yahoo_data
                        st.write(f"Fetched: {len(yahoo_data)} symbols")
    
    # Create index
    if st.button("Create FAISS Index & Store in S3"):
        uploaded_files = getattr(st.session_state, 'uploaded_files', [])
        yahoo_data = getattr(st.session_state, 'yahoo_data', {})
        
        if uploaded_files or yahoo_data:
            with st.spinner("Processing files with Nova Pro and creating FAISS index..."):
                if setup_faiss_manager():
                    # Process uploaded files with Nova Pro
                    processed_files = []
                    if uploaded_files:
                        processed_files = process_uploaded_files(uploaded_files)
                    
                    # Create index from processed files
                    if processed_files:
                        st.session_state.faiss_manager.create_index_from_files(processed_files)
                        st.session_state.index_created = True
                    
                    # Create index from Yahoo data
                    if yahoo_data:
                        st.session_state.faiss_manager.create_index_from_yahoo_data(yahoo_data)
                        st.session_state.index_created = True
                    
                    # Upload to S3
                    upload_faiss_to_s3()
    
    # Q&A System
    if st.session_state.index_created and st.session_state.faiss_manager:
        st.subheader("Ask Questions")
        query = st.text_input("Ask me anything about your financial data:")
        if st.button("Get Answer") and query:
            with st.spinner("Searching and generating answer..."):
                # Search FAISS index
                search_results = st.session_state.faiss_manager.search(query, 5)
                
                # Get simple answer
                answer = get_simple_answer(query, search_results)
                
                # Display answer
                st.write("**Answer:**")
                st.write(answer)
                
                # Show sources if available
                if search_results:
                    with st.expander("View Sources"):
                        for i, result in enumerate(search_results):
                            st.write(f"**Source {i+1}** (Score: {result['score']:.3f})")
                            st.write(f"Content: {result['content'][:300]}...")
                            st.write(f"Type: {result['metadata'].get('source', 'unknown')}")
                            st.write("---")
    
    # Status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files", len(getattr(st.session_state, 'uploaded_files', [])))
    with col2:
        st.metric("Yahoo", len(getattr(st.session_state, 'yahoo_data', {})))
    with col3:
        st.metric("Index", "Yes" if st.session_state.index_created else "No")



if __name__ == "__main__":
    main()

