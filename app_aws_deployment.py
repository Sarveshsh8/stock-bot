import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
import sys

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.data_processor.stock_data_loader import StockDataLoader
from src.vector_store.faiss_store import FAISSVectorStore
from src.serp_integration.google_search import StockGoogleSearch
from src.chatbot.rag_chatbot import StockRAGChatbot
from config_aws import setup_aws_credentials
from s3_faiss_manager import S3FAISSManager

# Load environment variables
load_dotenv()

# Setup AWS credentials
setup_aws_credentials()

# Page configuration
st.set_page_config(
    page_title="Stock Bot - AWS Deployment",
    page_icon=":chart_with_upwards_trend:",
    layout="wide"
)

# Initialize session state
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'index_created' not in st.session_state:
    st.session_state.index_created = False


@st.cache_resource
def initialize_system():
    """Initialize system - reads FAISS index from S3 directly to temp location."""
    try:
        import tempfile
        import shutil
        
        embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # S3 Configuration
        s3_bucket = os.getenv("S3_BUCKET_NAME")
        use_s3 = os.getenv("USE_S3_INDEX", "false").lower() == "true"
        
        vector_store = FAISSVectorStore(model_name=embedding_model)
        
        if use_s3 and s3_bucket:
            # Download from S3 to temporary directory (in memory)
            with st.spinner("Loading index from S3..."):
                s3_manager = S3FAISSManager(s3_bucket)
                
                if not s3_manager.index_exists():
                    st.error(f"Index not found in S3 bucket: {s3_bucket}")
                    st.info("Please upload index first: python3 s3_faiss_manager.py upload {s3_bucket} faiss_index_all")
                    return None
                
                # Create temp directory for index
                temp_dir = tempfile.mkdtemp(prefix="faiss_")
                
                try:
                    # Download from S3
                    downloaded_path = s3_manager.download_index(temp_dir)
                    
                    if downloaded_path and Path(downloaded_path).exists():
                        # Load into vector store (keeps in memory)
                        vector_store.load(downloaded_path)
                        
                        # Get stats
                        stats = vector_store.get_stats()
                        st.sidebar.success(f"✓ Loaded from S3: {stats.get('total_documents', 0)} stocks")
                    else:
                        st.error("Failed to download from S3")
                        return None
                        
                finally:
                    # Clean up temp directory - index is now in memory
                    if Path(temp_dir).exists():
                        shutil.rmtree(temp_dir)
        
        else:
            # Fallback: load from local if exists
            local_index = Path(__file__).parent / "faiss_index_all"
            if local_index.exists():
                vector_store.load(str(local_index))
            else:
                st.error("No index found. Set USE_S3_INDEX=true and S3_BUCKET_NAME in .env")
                return None
        
        # Initialize chatbot
        google_search = StockGoogleSearch()
        region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        model_id = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")
        
        chatbot = StockRAGChatbot(vector_store, google_search, region=region, model_id=model_id)
        
        return chatbot
    
    except Exception as e:
        st.error(f"Initialization error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None


def main():
    """Main Streamlit application - Simple chat interface."""
    
    # Simple title
    st.title("Stock Bot")
    
    # Minimal sidebar
    with st.sidebar:
        st.header("Stock Bot")
        st.caption("Powered by AWS Nova Pro")
        st.caption("Index: S3" if os.getenv("USE_S3_INDEX", "false").lower() == "true" else "Index: Local")
        
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize system
    if st.session_state.chatbot is None:
        with st.spinner("Initializing..."):
            st.session_state.chatbot = initialize_system()
        
        if st.session_state.chatbot:
            st.session_state.index_created = True
        else:
            st.error("Failed to initialize. Check configuration.")
            st.stop()
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # User input
    if prompt := st.chat_input("Ask about stocks..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.chatbot.chat(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()

