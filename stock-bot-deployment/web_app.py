"""
Stock Bot V3 - Web Application
Streamlit-based web interface for the unified financial analysis platform
"""

import streamlit as st
import os
import sys
import tempfile
from typing import List, Dict, Any
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_pipeline import UnifiedPipeline

# Page configuration
st.set_page_config(
    page_title="Stock Bot V3 - Unified Financial Analysis",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = None
if 'system_status' not in st.session_state:
    st.session_state.system_status = None

def initialize_pipeline():
    """Initialize the unified pipeline"""
    try:
        if st.session_state.pipeline is None:
            st.session_state.pipeline = UnifiedPipeline()
            st.session_state.system_status = st.session_state.pipeline.get_system_status()
        return True
    except Exception as e:
        st.error(f"Failed to initialize pipeline: {str(e)}")
        return False

def main():
    """Main application"""
    st.title("📊 Stock Bot V3 - Unified Financial Analysis Platform")
    st.markdown("---")
    
    # Initialize pipeline
    if not initialize_pipeline():
        st.stop()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Data Pipeline", "File Upload", "Q&A System", "System Status"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Data Pipeline":
        show_data_pipeline()
    elif page == "File Upload":
        show_file_upload()
    elif page == "Q&A System":
        show_qa_system()
    elif page == "System Status":
        show_system_status()

def show_dashboard():
    """Show dashboard overview"""
    st.header("📈 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Configured Symbols",
            st.session_state.system_status['yahoo_symbols']['total_count']
        )
    
    with col2:
        st.metric(
            "ETFs",
            len(st.session_state.system_status['yahoo_symbols']['etf_symbols'])
        )
    
    with col3:
        st.metric(
            "Stocks",
            len(st.session_state.system_status['yahoo_symbols']['stock_symbols'])
        )
    
    with col4:
        faiss_status = st.session_state.system_status['faiss_status']['status']
        st.metric(
            "FAISS Index",
            "Active" if faiss_status == 'loaded' else "Inactive"
        )
    
    st.markdown("---")
    
    # Show configured symbols
    st.subheader("📋 Configured Symbols")
    
    symbols_info = st.session_state.system_status['yahoo_symbols']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**ETFs:**")
        for symbol in symbols_info['etf_symbols']:
            st.write(f"• {symbol}: {symbols_info['symbol_names'][symbol]}")
    
    with col2:
        st.write("**Stocks:**")
        for symbol in symbols_info['stock_symbols']:
            st.write(f"• {symbol}: {symbols_info['symbol_names'][symbol]}")

def show_data_pipeline():
    """Show data pipeline interface"""
    st.header("🔄 Data Pipeline")
    
    st.write("Run the complete data pipeline to fetch Yahoo Finance data and create FAISS index.")
    
    if st.button("🚀 Run Full Pipeline", type="primary"):
        with st.spinner("Running pipeline..."):
            try:
                results = st.session_state.pipeline.run_full_pipeline()
                
                if results['status'] == 'success':
                    st.success("Pipeline completed successfully!")
                    
                    # Show results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Yahoo Symbols", results['yahoo_data']['total_symbols'])
                        st.metric("S3 Uploads", len(results['s3_uploads']))
                    
                    with col2:
                        st.metric("Files Processed", len(results['uploaded_files']))
                        st.metric("FAISS Index", results['faiss_index']['status'])
                    
                    # Show detailed results
                    with st.expander("Detailed Results"):
                        st.json(results)
                        
                else:
                    st.error(f"Pipeline failed: {results.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Error running pipeline: {str(e)}")

def show_file_upload():
    """Show file upload interface"""
    st.header("📁 File Upload")
    
    st.write("Upload documents, images, videos, or audio files for analysis.")
    
    # Show supported formats
    supported_formats = st.session_state.system_status['supported_file_formats']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.write("**Documents:**")
        for fmt in supported_formats['documents']:
            st.write(f"• {fmt}")
    
    with col2:
        st.write("**Images:**")
        for fmt in supported_formats['images']:
            st.write(f"• {fmt}")
    
    with col3:
        st.write("**Videos:**")
        for fmt in supported_formats['videos']:
            st.write(f"• {fmt}")
    
    with col4:
        st.write("**Audio:**")
        for fmt in supported_formats['audio']:
            st.write(f"• {fmt}")
    
    st.markdown("---")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        help="Upload multiple files for analysis"
    )
    
    if uploaded_files:
        st.write(f"Uploaded {len(uploaded_files)} files:")
        
        # Show uploaded files
        for file in uploaded_files:
            st.write(f"• {file.name} ({file.size} bytes)")
        
        if st.button("🔄 Process Uploaded Files", type="primary"):
            with st.spinner("Processing files..."):
                try:
                    # Save uploaded files temporarily
                    temp_files = []
                    for uploaded_file in uploaded_files:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            temp_files.append(tmp_file.name)
                    
                    # Run pipeline with uploaded files
                    results = st.session_state.pipeline.run_full_pipeline(temp_files)
                    
                    if results['status'] == 'success':
                        st.success("Files processed successfully!")
                        
                        # Show results
                        st.metric("Files Processed", len(results['uploaded_files']))
                        st.metric("S3 Uploads", len(results['s3_uploads']))
                        
                        # Show detailed results
                        with st.expander("Processing Results"):
                            st.json(results)
                    else:
                        st.error(f"Processing failed: {results.get('error', 'Unknown error')}")
                    
                    # Clean up temp files
                    for temp_file in temp_files:
                        os.unlink(temp_file)
                        
                except Exception as e:
                    st.error(f"Error processing files: {str(e)}")

def show_qa_system():
    """Show Q&A system interface"""
    st.header("❓ Q&A System")
    
    # Check if FAISS index is available
    faiss_status = st.session_state.system_status['faiss_status']['status']
    
    if faiss_status != 'loaded':
        st.warning("No FAISS index available. Please run the data pipeline first.")
        return
    
    st.write("Ask questions about your financial data and uploaded files.")
    
    # Query input
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., What was Apple's recent performance?"
    )
    
    # Number of results
    k = st.slider("Number of results:", min_value=1, max_value=10, value=5)
    
    if st.button("🔍 Search", type="primary") and query:
        with st.spinner("Searching..."):
            try:
                results = st.session_state.pipeline.query_system(query, k)
                
                if results:
                    st.success(f"Found {len(results)} results")
                    
                    for i, result in enumerate(results):
                        with st.expander(f"Result {i+1} (Score: {result['score']:.3f})"):
                            st.write("**Content:**")
                            st.write(result['content'])
                            
                            st.write("**Metadata:**")
                            st.json(result['metadata'])
                else:
                    st.info("No results found for your query.")
                    
            except Exception as e:
                st.error(f"Error searching: {str(e)}")

def show_system_status():
    """Show system status"""
    st.header("⚙️ System Status")
    
    # Refresh status
    if st.button("🔄 Refresh Status"):
        st.session_state.system_status = st.session_state.pipeline.get_system_status()
        st.rerun()
    
    # Show status information
    status = st.session_state.system_status
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Data Sources")
        st.write(f"**Config loaded:** {status['config_loaded']}")
        st.write(f"**Total symbols:** {status['yahoo_symbols']['total_count']}")
        st.write(f"**ETFs:** {len(status['yahoo_symbols']['etf_symbols'])}")
        st.write(f"**Stocks:** {len(status['yahoo_symbols']['stock_symbols'])}")
    
    with col2:
        st.subheader("🔧 System Components")
        st.write(f"**S3 Status:** {status['s3_status']['status']}")
        st.write(f"**FAISS Status:** {status['faiss_status']['status']}")
        if status['faiss_status']['status'] == 'loaded':
            st.write(f"**Index Vectors:** {status['faiss_status']['total_vectors']}")
            st.write(f"**Index Documents:** {status['faiss_status']['total_documents']}")
    
    # Show detailed status
    with st.expander("Detailed System Status"):
        st.json(status)

if __name__ == "__main__":
    main()
