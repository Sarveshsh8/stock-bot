#!/usr/bin/env python3
"""
Financial Data QA Streamlit App
Simple web interface for the financial analysis system
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from QA_Agent.index_builder import FAISSIndexBuilder
from QA_Agent.query_engine import FAISSQueryEngine
from QA_Agent.output_generator import FinalOutputGenerator

# Page configuration
st.set_page_config(
    page_title="Financial Data QA System",
    page_icon="",
    layout="wide"
)

# Initialize session state
if 'qa_system_ready' not in st.session_state:
    st.session_state.qa_system_ready = False

if 'question' not in st.session_state:
    st.session_state.question = ""

def initialize_system():
    """Initialize the QA system by loading existing FAISS index"""
    try:
        with st.spinner("Loading existing FAISS index..."):
            # Check if index files exist
            index_path = "indices/financial_data.index"
            docs_path = "indices/financial_documents.pkl"
            
            if os.path.exists(index_path) and os.path.exists(docs_path):
                # Load the existing index
                query_engine = FAISSQueryEngine()
                query_engine.load_index(index_path, docs_path)
                query_engine.load_sentence_transformer()
                
                # Load output generator
                output_generator = FinalOutputGenerator()
                output_generator.load_index_and_model(index_path, docs_path)
                
                # Store in session state
                st.session_state.query_engine = query_engine
                st.session_state.output_generator = output_generator
                st.session_state.qa_system_ready = True
                
                st.success("System initialized successfully with existing FAISS index!")
            else:
                st.warning("No existing FAISS index found. Please analyze documents first.")
                
    except Exception as e:
        st.error(f"Error initializing system: {e}")

def analyze_documents():
    """Analyze documents from S3 and build FAISS index"""
    try:
        with st.spinner("Analyzing documents and building FAISS index..."):
            # Build index
            builder = FAISSIndexBuilder()
            builder.build_index()
            
            # Save index
            builder.save_index("indices/financial_data.index", "indices/financial_documents.pkl")
            
            # Initialize system with new index
            initialize_system()
            
            st.success("Documents analyzed and FAISS index built successfully!")
            
    except Exception as e:
        st.error(f"Error analyzing documents: {e}")

def main():
    """Main Streamlit app"""
    
    # Header
    st.title("Financial Data QA System")
    st.markdown("Intelligent financial analysis using S3 data and Nova Pro AI")
    
    # Sidebar
    st.sidebar.header("System Controls")
    
    # Initialize system button
    if st.sidebar.button("Initialize System"):
        initialize_system()
    
    # Analyze documents button
    if st.sidebar.button("Analyze Documents & Build Index"):
        analyze_documents()
    
    # System status
    st.sidebar.header("System Status")
    if st.session_state.qa_system_ready:
        st.sidebar.success("QA System Ready")
    else:
        st.sidebar.error("QA System Not Ready")
    
    # Check if index files exist
    index_exists = os.path.exists("indices/financial_data.index") and os.path.exists("indices/financial_documents.pkl")
    st.sidebar.write(f"FAISS Index: {'READY' if index_exists else 'NOT READY'}")
    
    # Main content area
    if st.session_state.qa_system_ready:
        st.header("Ask Questions About Financial Data")
        
        # Question input
        question = st.text_input(
            "Enter your question:",
            placeholder="e.g., What is the current Apple stock price?",
            help="Ask any question about the financial data"
        )
        
        if question:
            if st.button("Get Answer"):
                with st.spinner("Processing your question..."):
                    try:
                        answer = st.session_state.output_generator.process_query(question)
                        
                        # Display answer
                        st.subheader("Answer")
                        st.markdown(answer)
                        
                        # Display question
                        st.subheader("Question")
                        st.write(question)
                        
                    except Exception as e:
                        st.error(f"Error processing question: {e}")
        
        # Example questions
        st.header("Example Questions")
        example_questions = [
            "What is the current Apple stock price?",
            "Show me technical indicators",
            "What are the financial recommendations?",
            "Give me a trading summary",
            "What is the market sentiment?",
            "Analyze the market trends"
        ]
        
        cols = st.columns(2)
        for i, example in enumerate(example_questions):
            col = cols[i % 2]
            if col.button(example, key=f"example_{i}"):
                st.session_state.question = example
                st.experimental_rerun()
        
    else:
        st.header("System Setup Required")
        st.info("Please use the sidebar to initialize the system or analyze documents.")
        
        # Instructions
        st.markdown("""
        ### Setup Steps:
        1. **Initialize System** - Load existing FAISS index (if available)
        2. **Analyze Documents** - Read from S3, analyze, and build new index
        
        ### Requirements:
        - S3_BUCKET_NAME set in .env file
        - Documents uploaded to S3 bucket
        - AWS credentials configured
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("Built with Streamlit, FAISS, and AWS Nova Pro")

if __name__ == "__main__":
    main()
