import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import sys

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.data_processor.stock_data_loader import StockDataLoader
from src.vector_store.faiss_store import FAISSVectorStore
from src.serp_integration.google_search import StockGoogleSearch
from src.chatbot.rag_chatbot import StockRAGChatbot
from config_aws import setup_aws_credentials

# Load environment variables
load_dotenv(find_dotenv(), override=False)

# Setup AWS credentials
setup_aws_credentials()

# Page configuration
st.set_page_config(
    page_title="Stock Bot - AWS Nova + Open Source Embeddings",
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
    """Initialize the stock bot system silently."""
    try:
        dataset_path = Path(__file__).parent / "stock_dataset"
        if not dataset_path.exists():
            st.error("Stock dataset not found")
            return None
        
        data_loader = StockDataLoader(str(dataset_path))
        index_path = Path(__file__).parent / "faiss_index_all"
        embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        vector_store = FAISSVectorStore(model_name=embedding_model)
        
        # Load or create index
        if index_path.exists():
            # Load existing index silently
            vector_store.load(str(index_path))
        else:
            # Create index for ALL stocks
            with st.spinner("Building knowledge base from all stocks... (This will take a while on first run)"):
                # Load ALL unique stocks
                metadata_list = data_loader.load_all_stocks_metadata(limit=None)
                
                if not metadata_list:
                    st.error("No stock data found")
                    return None
                
                # Create text summaries
                texts = [data_loader.create_summary_text(m) for m in metadata_list]
                
                # Create FAISS index
                vector_store.create_index(texts, metadata_list)
                
                # Save index for future use
                vector_store.save(str(index_path))
        
        # Initialize components
        google_search = StockGoogleSearch()
        region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        model_id = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")
        
        chatbot = StockRAGChatbot(vector_store, google_search, region=region, model_id=model_id)
        
        # Silent connection test
        chatbot.test_nova_connection()
        
        return chatbot
    
    except Exception as e:
        st.error(f"Initialization error: {str(e)}")
        return None


def main():
    """
    Main Streamlit application - Simple chat interface.
    """
    
    # Simple title
    st.title("Stock Bot")
    
    # Minimal sidebar
    with st.sidebar:
        st.header("Stock Bot")
        st.caption("Powered by AWS Nova Pro")
        
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

